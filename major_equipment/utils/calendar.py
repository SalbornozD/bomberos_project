import calendar
from django.utils import timezone
from major_equipment.models.report import Report

def get_calendar_data(unit, year, month):
    hoy = timezone.localdate()
    # Obtener todos los reportes del mes actual para esa unidad
    reports = Report.objects.filter(
        unit=unit,
        date__year=year,
        date__month=month,
        deleted=False
    ).values_list("date", flat=True)

    # Convertir fechas a un set de días para acceso rápido
    dias_con_reporte = set(dt.day for dt in reports)

    first_weekday, num_days = calendar.monthrange(year, month)

    cells = []

    # Espacios vacíos antes del día 1
    for _ in range(first_weekday):
        cells.append({"day": "", "css_class": "empty-day", "disabled": True})

    for day in range(1, num_days + 1):
        fecha_actual = timezone.datetime(year, month, day).date()

        # Base del botón
        cell = {
            "day": day,
            "css_class": "day",
            "disabled": False,
        }

        # Marcar día actual
        if fecha_actual == hoy:
            cell["css_class"] += " today"

        # Verificar si tiene reporte
        if day in dias_con_reporte:
            cell["css_class"] += " done"
        elif fecha_actual <= hoy:
            cell["css_class"] += " missing"
        else:
            cell["disabled"] = True  # No permitir clics en días futuros

        cells.append(cell)

    # Espacios vacíos al final para cuadrar grilla
    while len(cells) % 7 != 0:
        cells.append({"day": "", "css_class": "empty-day", "disabled": True})

    return cells
