from django.db                                  import transaction
from django.http                                import HttpResponse
from django.conf                                import settings
from django.http                                import HttpResponse
from django.urls                                import reverse
from django.core.mail                           import send_mail
from django.utils                               import timezone
from django.contrib                             import messages
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

from weasyprint                                 import HTML
from urllib.parse                               import urlencode

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }


@login_required  # Crear Reporte
def view_create_report(request):
    # 1) Unidad requerida vía query param ?unit=
    unit_id = request.GET.get('unit')
    if not unit_id:
        messages.warning(request, "Debes especificar una unidad para crear un reporte.")
        logger.warning(f"El usuario {request.user} intentó crear un reporte sin especificar una unidad.")
        return redirect('major_equipment:units')

    unit = get_object_or_404(Unit, pk=unit_id)

    # 2) Cargar plantilla de ítems con su categoría
    template_items = (
        ReportTemplateItem.objects
        .select_related('category')
        .filter(units=unit)
    )

    # 3) Agrupar por categoría y ordenar por question_type
    items_by_category = {}
    for item in template_items:
        items_by_category.setdefault(item.category.label, []).append(item)
    for lst in items_by_category.values():
        lst.sort(key=lambda x: x.question_type)

    # 4) POST: validar y crear
    if request.method == "POST":
        # No duplicar reporte del mismo día
        today = timezone.localdate()
        if Report.objects.filter(unit=unit, date=today).exists():
            messages.error(request, "Ya existe un reporte para esta unidad en el día de hoy.")
            logger.warning(
                f"El usuario {request.user} intentó crear un reporte duplicado "
                f"para la unidad {unit.id} en la fecha {today}."
            )
            base = reverse('major_equipment:unit_reports')
            return redirect(f"{base}?{urlencode({'unit': unit.id})}")

        try:
            with transaction.atomic():
                # Validar Report (mostrar errores arriba si los hay)
                report = Report(
                    unit=unit,
                    author=request.user,
                    date=today,
                    coment=request.POST.get('general_comment', '').strip()
                )
                try:
                    report.full_clean()
                except ValidationError as e:
                    # Errores propios del modelo Report
                    if hasattr(e, "message_dict"):
                        for errs in e.message_dict.values():
                            for err in errs:
                                messages.error(request, err)
                    else:
                        for err in e.messages:
                            messages.error(request, err)
                    raise  # abortar transacción

                report.save()

                # Crear cada ReportEntry y, si falla, indicar la pregunta (item.label)
                for item in template_items:
                    answer = (request.POST.get(f"q_{item.id}", "") or "").strip()
                    comment = (request.POST.get(f"q_{item.id}_comment", "") or "").strip()

                    entry = ReportEntry(
                        report=report,
                        question=item,
                        answer=answer,
                        comment=comment
                    )

                    try:
                        entry.full_clean()
                    except ValidationError as e:
                        if hasattr(e, "message_dict"):
                            for errs in e.message_dict.values():
                                for err in errs:
                                    messages.error(request, f"{item.label}: {err}")
                        else:
                            for err in e.messages:
                                messages.error(request, f"{item.label}: {err}")
                        raise  # abortar transacción

                    entry.save()

        except ValidationError:
            # Ya mostramos los errores arriba; caemos al render del form
            pass
        except Exception as e:
            messages.error(request, f"Ocurrió un error inesperado: {e}")
        else:
            messages.success(request, "Reporte creado correctamente.")
            base = reverse('major_equipment:unit_reports')
            return redirect(f"{base}?{urlencode({'unit': unit.id})}")

    # 5) Render (GET o POST con errores)
    return render(request, "major_equipment/reports/report_form.html", {
        'unit': unit,
        'report_template_items': items_by_category,
        'title': "Bomberos Quintero | Crear reporte"
    })

@login_required # Listar reportes de una unidad. 
def view_unit_reports(request):
    unit_id = request.GET.get('unit')


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
    
    base = f"{reverse('major_equipment:unit_reports')}"
    data['prev_url'] = f"{base}?unit={unit_id}&year={prev_year}&month={prev_month}"
    data['next_url'] = f"{base}?unit={unit_id}&year={next_year}&month={next_month}"

    return render(request, "major_equipment/reports/unit_reports.html", data)

@login_required # Ver reporte
def view_get_report(request, report_id):
    data = {}
    data["report"] = get_object_or_404(Report, pk=report_id)
    return render(request, "major_equipment/reports/report.html", data)

@login_required # Generar PDF de reporte
def view_generate_report_pdf(request, report_id):
    data = {}
    data['report'] = get_object_or_404(Report, pk=report_id)
    data['unit'] = data["report"].unit

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

