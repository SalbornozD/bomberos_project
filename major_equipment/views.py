from django.db                              import transaction, IntegrityError
from django.http                            import HttpResponse
from django.conf                            import settings
from django.http                            import HttpRequest, HttpResponse, HttpResponseForbidden
from django.urls                            import reverse
from django.utils                           import timezone
from django.db.models                       import Q
from django.shortcuts                       import render, get_object_or_404, redirect
from django.template.loader                 import render_to_string
from django.contrib.auth.models             import Group
from django.contrib.auth.decorators         import login_required

# MODELOS
from major_equipment.models.unit            import *
from major_equipment.models.report          import *
from major_equipment.models.fuel_log        import *
from major_equipment.models.maintenance_log import *

# Utilidades
from .utils.permission                      import *
from .utils.calendar                        import *

# Librerias
from django.contrib                         import messages
from django.core.mail                       import send_mail
from decimal                                import Decimal, InvalidOperation
from datetime                               import datetime
from weasyprint                             import HTML

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }


# UNIDADES

@login_required # Listado de unidades.
def view_get_units(request: HttpRequest) -> HttpResponse:
    """
    Vista para listar unidades visibles para el usuario autenticado, en base los permisos
    que tenga el usuario asignado. 
        
    """
    user = request.user # Usuario actual
    
    search_filter = request.GET.get("search-filter", "") # Filtro de busqueda

    units = get_units(user) # QuerySet de unidades.

    # Filtrar por numero de unidad, descripcion o numero de patente.
    if search_filter:
        units = units.filter(
        Q(unit_number__icontains=search_filter) |
        Q(description__icontains=search_filter) |
        Q(plate_number__icontains=search_filter)
    )

    # Ordenamos las unidades por número de unidad
    units = units.order_by("unit_number")

    # Preparamos los datos de las unidades para el template
    # Incluimos la primera imagen de cada unidad para mostrarla en la tarjeta
    # Incluimos clases indicadores del estado de los documentos asociados.
    # Solo falta el estado del vehiculo (verde operativo, rojo fuera de servicio)
    units_data = []
    for unit in units:
        element = {
            "unit": unit,
            "image": unit.images.first(),
        }

        if unit.vehicle_permit and not unit.vehicle_permit.is_expired:
            element["vehicle_permit_class"] = "badge text-bg-success"
        elif unit.vehicle_permit and unit.vehicle_permit.is_expired:
            element["vehicle_permit_class"] = "badge text-bg-danger"
        else:
            element["vehicle_permit_class"] = "badge text-bg-light"

        if unit.soap and not unit.soap.is_expired:
            element["soap_class"] = "badge text-bg-success"
        elif unit.soap and unit.soap.is_expired:
            element["soap_class"] = "badge text-bg-danger"
        else:
            element["soap_class"] = "badge text-bg-light"

        if unit.technical_inspection and not unit.technical_inspection.is_expired:
            element["technical_inspection_class"] = "badge text-bg-success"
        elif unit.technical_inspection and unit.technical_inspection.is_expired:
            element["technical_inspection_class"] = "badge text-bg-danger"
        else:
            element["technical_inspection_class"] = "badge text-bg-light"

        units_data.append(element)


    # Creación del contexto para la plantilla
    context = {
        "title": "Material Mayor | Bomberos Quintero",
        "units": units_data,
        "search_filter": search_filter,
    }

    return render(request, "major_equipment/unit/units.html", context)

@login_required # Detalle de unidad (Ficha resumen y documentos asociados).
def view_get_unit(request: HttpRequest, unit_id: int) -> HttpResponse:
    user = request.user

    # 1) Recuperar unidad o 404
    unit = get_object_or_404(Unit, pk=unit_id)

    # 2) Verificar permiso
    #if not can_view_unit(user, unit):
    #    return HttpResponseForbidden("No tienes permisos para ver esta unidad.")
    
    images = unit.images.all()

    context = {
        "unit": unit,
        "images": images,
        "title": "Material Mayor | Bomberos Quintero",
    }
    return render(request, "major_equipment/unit/unit.html", context)

# REPORTES

@login_required # Crear Reporte
def view_create_report(request, unit_id):
    # 1. Obtener la unidad
    unit = get_object_or_404(Unit, pk=unit_id)

    # 2. Cargar plantilla de ítems con su categoría (reduce consultas)
    template_items = (
        ReportTemplateItem.objects
        .select_related('category')
        .all()
    )

    # 3. Agrupar por categoría
    items_by_category = {}
    for item in template_items:
        label = item.category.label
        items_by_category.setdefault(label, []).append(item)

    # 4. Ordenar cada lista por question_type
    for lst in items_by_category.values():
        lst.sort(key=lambda x: x.question_type)

    if request.method == "POST":
        # 5. Validación: no duplicar reporte del mismo día
        today = timezone.localdate()
        if Report.objects.filter(unit=unit, date=today).exists():
            messages.error(request, "Ya existe un reporte para hoy.")
            return redirect('major_equipment:unit_reports', unit_id=unit_id)

        flag_mail = False

        try:
            with transaction.atomic():
                # 6. Crear instancia de Report y validarla
                report = Report(
                    unit=unit,
                    author=request.user,
                    date=timezone.now(),
                    coment=request.POST.get('general_comment', '').strip()
                )
                report.full_clean()
                report.save()

                if report.coment:
                    flag_mail = True

                # 7. Crear cada ReportEntry
                for item in template_items:
                    answer = request.POST.get(f"q_{item.id}", "").strip()
                    comment = request.POST.get(f"q_{item.id}_comment", "").strip()

                    entry = ReportEntry(
                        report=report,
                        question=item,
                        answer=answer,
                        comment=comment
                    )
                    entry.full_clean()
                    entry.save()

                    if comment:
                        flag_mail = True

                # 8. Si hay comentarios, notificar por correo
                if flag_mail:
                    try:
                        group = Group.objects.get(name='Notification_observation_report')
                        users = group.user_set.filter(is_active=True).exclude(email='')
                        recipient_list = [u.email for u in users]

                        if recipient_list:
                            subject = (
                                f"Reporte {report.id} requiere atención "
                                f"(Unidad {unit.unit_number})"
                            )
                            body = (
                                f"Estimados,\n\n"
                                f"El {report.date.strftime('%d/%m/%Y %H:%M')}, "
                                f"{report.author} creó un reporte para la unidad "
                                f"{unit.unit_number} ({unit.description}) que requiere atención.\n\n"
                                "Saludos,\n"
                                "Equipo TI Bomberos Quintero"
                            )
                            send_mail(
                                subject=subject,
                                message=body,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=recipient_list,
                                fail_silently=False,
                            )
                    except Group.DoesNotExist:
                        logger.error("Grupo 'Notification_observation_report' no encontrado.")
                    except Exception as e:
                        logger.error(f"Error al enviar correo de notificación: {e}")

                messages.success(request, "Reporte creado exitosamente.")
                return redirect('major_equipment:unit_reports', unit_id=unit_id)

        except ValidationError as e:
            for field, errs in e.message_dict.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {e}")

    # 9. Renderizar el formulario (GET o POST con errores)
    return render(request, "major_equipment/reports/report_form.html", {
        'unit': unit,
        'report_template_items': items_by_category
    })

@login_required # Listar reportes de una unidad. 
def view_unit_reports(request, unit_id):
    data = {}
    unit = get_object_or_404(Unit, pk=unit_id)
    data["unit"] = unit

    try:
        year = int(request.GET.get('year', timezone.localdate().year))
    except ValueError:
        year = timezone.localdate().year
    
    if year < 2000 or year > timezone.localdate().year:
        year = timezone.localdate().year

    try:
        month = int(request.GET.get('month', timezone.localdate().month))
    except ValueError:
        month = timezone.localdate().month
    
    if month not in MESES_ES.keys():
        month = timezone.localdate().month

    data["month_year"] = f"{MESES_ES[month]} {year}"
    data['cells'] = get_calendar_data(unit, year, month)

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    base = reverse('major_equipment:unit_reports', args=[unit_id])
    data['prev_url'] = f"{base}?year={prev_year}&month={prev_month}"
    data['next_url'] = f"{base}?year={next_year}&month={next_month}"

    return render(request, "major_equipment/reports/unit_reports.html", data)

@login_required # Ver reporte
def view_get_report(request, unit_id, report_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    data["report"] = get_object_or_404(Report, pk=report_id, unit=data["unit"])
    return render(request, "major_equipment/reports/report.html", data)

@login_required # Generar PDF de reporte
def view_generate_report_pdf(request, unit_id, report_id):
    data = {}
    data['report'] = get_object_or_404(Report, pk=report_id, unit__pk=unit_id)
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    
    # 1. Carga el HTML
    html_string = render_to_string(
        'major_equipment/reports/reportPDF.html',  # ruta relativa a tu carpeta templates/
        data,                                       # pasamos el contexto
        request=request                             # para que {% static %} funcione si lo necesitaras
    )

    # 2. Genera el PDF
    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri('/')   # para resolver rutas a estáticos
    ).write_pdf()

    # 3. Devuelve la respuesta PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="hola_mundo.pdf"'
    return response


# COMBUSTIBLE

@login_required # Crear carga de combustible
def view_create_fuel(request, unit_id):
    unit     = get_object_or_404(Unit, pk=unit_id)
    stations = Station.objects.all()
    now      = timezone.localtime()

    if request.method == 'POST':
        errors = False

        # 1. Fecha
        date_str = request.POST.get('date', '')
        if date_str:
            try:
                naive = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
                date  = timezone.make_aware(naive)
            except ValueError:
                messages.error(request, 'Formato de fecha inválido.')
                errors = True
        else:
            date = timezone.now()

        # 2. Número de guía
        try:
            guide_number = int(request.POST.get('guide_number', ''))
            if guide_number <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'El número de guía es obligatorio y debe ser un entero positivo.')
            errors = True

        # 3. Cantidad, costo y kilometraje
        try:
            quantity      = Decimal(request.POST.get('quantity', '0'))
            cost          = Decimal(request.POST.get('cost', '0'))
            cargo_mileage = Decimal(request.POST.get('cargo_mileage', '0'))
            if quantity <= 0 or cost < 0 or cargo_mileage < 0:
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, 'Cantidad, costo y kilometraje deben ser números válidos y no negativos.')
            errors = True

        # 4. Estación de servicio
        station_id = request.POST.get('station')
        try:
            station = Station.objects.get(pk=station_id)
        except (Station.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Debes seleccionar una estación de servicio válida.')
            errors = True

        # 5. Opcionales
        notes  = request.POST.get('notes') or None
        ticket = request.FILES.get('ticket')

        # 6. Guardar si no hay errores
        if not errors:
            # 1) chequeo de duplicado
            if FuelLog.objects.filter(guide_number=guide_number, station=station).exists():
                messages.error(request, 'Ya existe un registro con ese número de guía de esa estación.')
                errors = True
            else:
                try:
                    FuelLog.objects.create(
                        unit=unit,
                        guide_number=guide_number,
                        station=station,
                        date=date,
                        quantity=quantity,
                        cost=cost,
                        cargo_mileage=cargo_mileage,
                        notes=notes,
                        ticket=ticket,
                        author=request.user,      
                    )
                except IntegrityError as e:
                    logger.exception("Error inesperado guardando FuelLog: %r", e)
                    messages.error(request, 'Ocurrió un error inesperado al guardar. Revisa los logs.')
                    errors = True
                else:
                    messages.success(request, 'Registro de combustible creado exitosamente.')
                    return redirect('major_equipment:unit_fuel', unit_id=unit_id)

        # Si hubo errores, vuelvo a mostrar el formulario con los mensajes
        return render(request, 'major_equipment/fuel/fuel_form.html', {
            'unit': unit,
            'stations': stations,
            'now': now,
        })

    # GET: renderizar formulario vacío
    return render(request, 'major_equipment/fuel/fuel_form.html', {
        'unit': unit,
        'stations': stations,
        'now': now,
    })

@login_required # Ver cargas de combustible de una unidad.
def view_unit_fuel(request, unit_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)

    try:
        year = int(request.GET.get('year', timezone.localdate().year))
    except ValueError:
        year = timezone.localdate().year
    
    if year < 2000 or year > timezone.localdate().year:
        year = timezone.localdate().year

    try:
        month = int(request.GET.get('month', timezone.localdate().month))
    except ValueError:
        month = timezone.localdate().month
    
    if month not in MESES_ES.keys():
        month = timezone.localdate().month

    data["month_year"] = f"{MESES_ES[month]} {year}"

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    base = reverse('major_equipment:unit_fuel', args=[unit_id])
    data['prev_url'] = f"{base}?year={prev_year}&month={prev_month}"
    data['next_url'] = f"{base}?year={next_year}&month={next_month}"

    data["fuel_logs"] = FuelLog.objects.filter(unit=data["unit"], date__year=year, date__month=month).order_by("-date")
    data['fuel_quantity_total'] = sum(log.quantity for log in data["fuel_logs"])
    data['fuel_cost_total'] = sum(log.cost for log in data["fuel_logs"])

    return render(request, "major_equipment/fuel/unit_fuel.html", data)

@login_required # Ver Detalle de carga de combustible
def view_get_fuel_log(request, unit_id, fuel_log_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    data["fuel_log"] = get_object_or_404(FuelLog, pk=fuel_log_id, unit=data["unit"])

    return render(request, "major_equipment/fuel/fuel_log.html", data)

# MANTENCIONES

@login_required # Crear solicitud de mantención
def view_create_maintenance_request(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)

    # Inicializamos contexto para GET o POST fallido
    form_data = {
        'description': '',
        'responsible_for_payment': ''
    }
    errors = {}

    if request.method == "POST":
        # 1. Recogemos datos
        description = request.POST.get('description', '').strip()
        resp_choice = request.POST.get('responsible_for_payment', '')

        form_data['description'] = description
        form_data['responsible_for_payment'] = resp_choice

        # 2. Validaciones
        if not description:
            errors['description'] = "La descripción es obligatoria."
        if resp_choice not in ("bomberos", "company"):
            errors['responsible_for_payment'] = "Debes seleccionar quién paga."

        # 3. Si pasa validación, creamos el MaintenanceLog
        if not errors:
            # Obtener la entidad “Cuerpo de Bomberos”
            # Ajusta este filtro a tu modelo: 
            # por ejemplo un flag is_institutional o un slug concreto.

            if resp_choice == "bomberos":
                entidad_pago = Entity.objects.get(type='ADMIN')
                print(entidad_pago)
            else:
                user = request.user
                print(user)
                entidad_pago = get_user_entity(user)
                print(entidad_pago)

            log = MaintenanceLog.objects.create(
                unit=unit,
                description=description,
                responsible_for_payment=entidad_pago,
                author=request.user
            )
            # Redirige, por ejemplo, al detalle de la solicitud o a la lista
            return redirect('major_equipment:unit_maintenance', unit_id=unit_id)

    # Renderizamos (GET o POST con errores)
    return render(request, 
                  "major_equipment/maintenance/forms/maintenance_form.html", 
                  {
                      'unit': unit,
                      'form_data': form_data,
                      'errors': errors,
                  })

@login_required # Agregar cotización
def view_add_quotation(request, unit_id, log_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    data["maintenance_log"] = get_object_or_404(MaintenanceLog, pk=log_id)
    return render(request, "major_equipment/maintenance/forms/quote_form.html", data)

@login_required # Listado de mantenciones.
def view_unit_maintenance(request, unit_id):
    data = {}
    unit = get_object_or_404(Unit, pk=unit_id)
    data["unit"] = unit
    data["maintenance_logs"] = MaintenanceLog.objects.filter(unit=unit).order_by("-creation_date")
    return render(request, "major_equipment/maintenance/unit_maintenance.html", data)

@login_required # Detalle de mantención
def view_get_maintenance_log(request, unit_id, maintenance_log_id):
    data = {}
    data["unit"] = get_object_or_404(Unit, pk=unit_id)
    data["maintenance_log"] = get_object_or_404(MaintenanceLog, pk=maintenance_log_id)
    return render(request, "major_equipment/maintenance/maintenance_log.html", data)

