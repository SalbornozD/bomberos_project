from django.db                                  import IntegrityError
from django.urls                                import reverse
from django.utils                               import timezone
from django.shortcuts                           import render, get_object_or_404, redirect
from django.contrib.auth.decorators             import login_required

# MODELOS
from major_equipment.models.unit                import *
from major_equipment.models.fuel_log            import *

# Utilidades
from ..utils.permission                          import *
from ..utils.calendar                            import *

# Librerias
from django.contrib                             import messages
from decimal                                    import Decimal, InvalidOperation
from datetime                                   import datetime

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

MESES_ES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }


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
