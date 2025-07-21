from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from major_equipment.utils.permission import get_units
from django.shortcuts import render, get_object_or_404, redirect
from major_equipment.models import Unit
from major_equipment.models.report import *
from major_equipment.models.fuel_log import *
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .utils.calendar import get_calendar_data
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.contrib.auth.models import Group
from django.urls import reverse
from django.template.loader import render_to_string
from django.http         import HttpResponse
from weasyprint          import HTML


import logging
logger = logging.getLogger('myapp')


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

@login_required # Detalle de unidad (Ficha resumen y docyumentos asociados).
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

    MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

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

@login_required # Crear carga de combustible de una unidad.
def view_create_fuel(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)

    if request.method == 'POST':
        # 1. Fecha: parseamos el input datetime-local (YYYY-MM-DDTHH:MM)
        date_str = request.POST.get('date', '')
        if date_str:
            naive = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            date = timezone.make_aware(naive)
        else:
            date = timezone.now()

        # 2. Cantidad y costo
        try:
            quantity = Decimal(request.POST.get('quantity', '0'))
            cost = int(request.POST.get('cost', '0'))
            if quantity <= 0 or cost < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, 'La cantidad o el costo no son válidos.')
            return render(request, 'major_equipment/fuel/fuel_form.html', {
                'unit': unit,
                'now': timezone.localtime(),
            })

        # 3. Campos opcionales
        station = request.POST.get('station') or None
        notes   = request.POST.get('notes')   or None
        ticket  = request.FILES.get('ticket')  # requiere enctype multipart/form-data

        # 4. Guardar FuelLog
        fuel_log = FuelLog(
            unit=unit,
            date=date,
            quantity=quantity,
            cost=cost,
            station=station,
            notes=notes,
            ticket=ticket
        )
        fuel_log.save()

        messages.success(request, 'Registro de combustible creado exitosamente.')
        return redirect('major_equipment:unit_fuel', unit_id=unit_id)

    # GET: renderizamos el formulario
    return render(request, 'major_equipment/fuel/fuel_form.html', {
        'unit': unit,
        'now': timezone.localtime(),
    })

@login_required # Ver cargas de combustible de una unidad.
def view_unit_fuel(request, unit_id):
    data = {}
    unit = get_object_or_404(Unit, pk=unit_id)
    data["unit"] = unit

    MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    fecha_actual = timezone.now()
    data["month_year"] = f"{MESES_ES[fecha_actual.month]} {fecha_actual.year}"

    data["fuel_logs"] = FuelLog.objects.filter(unit=unit, date__year=fecha_actual.year, date__month=fecha_actual.month).order_by("-date")
    

    return render(request, "major_equipment/unit_fuel.html", data)


# MANTENCIONES

@login_required
def view_unit_maintenance(request, unit_id):
    data = {}
    unit = get_object_or_404(Unit, pk=unit_id)
    data["unit"] = unit

    MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    fecha_actual = timezone.now()

    data["month_year"] = f"{MESES_ES[fecha_actual.month]} {fecha_actual.year}"

    return render(request, "major_equipment/unit_maintenance.html", data)