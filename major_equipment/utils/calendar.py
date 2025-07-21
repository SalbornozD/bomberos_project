import calendar
from datetime import date
from django.utils import timezone
from major_equipment.models.report import Report

def get_calendar_data(unit, year, month):
    today = timezone.localdate()

    # Traer todos los Report de una sola vez
    reports = Report.objects.filter(
        unit=unit,
        date__year=year,
        date__month=month,
        deleted=False
    )
    # Mapa de día → instancia de Report
    report_map = {r.date.day: r for r in reports}

    first_weekday, num_days = calendar.monthrange(year, month)
    cells = []

    # Espacios vacíos antes del día 1
    for _ in range(first_weekday):
        cells.append({"day": "", "css_class": "empty-day", "disabled": True})

    # Generar cada día del mes
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        cell = {
            "day": day,
            "css_class": "day",
            "disabled": False,
        }

        # Día de hoy
        if current_date == today:
            cell["css_class"] += " today"

        # Si hay reporte
        if day in report_map:
            cell["css_class"] += " done"
            cell["report"] = report_map[day]
        # Pasados sin reporte
        elif current_date < today:
            cell["css_class"] += " missing"
        # Futuros
        else:
            cell["disabled"] = True

        cells.append(cell)

    # Espacios vacíos al final para cuadrar en múltiplo de 7
    while len(cells) % 7 != 0:
        cells.append({"day": "", "css_class": "empty-day", "disabled": True})

    return cells
