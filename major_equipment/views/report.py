from django.db                                  import transaction
from django.http                                import HttpResponse
from django.conf                                import settings
from django.http                                import HttpResponse
from django.urls                                import reverse
from django.utils                               import timezone
from django.shortcuts                           import render, get_object_or_404, redirect
from django.template.loader                     import render_to_string
from django.contrib.auth.models                 import Group
from django.contrib.auth.decorators             import login_required

# MODELOS
from major_equipment.models.unit                import *
from major_equipment.models.report              import *

# Utilidades
from ..utils.permission                          import *
from ..utils.calendar                            import *

# Librerias
from django.contrib                             import messages
from django.core.mail                           import send_mail
from weasyprint                                 import HTML

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

# UNIDADES

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

