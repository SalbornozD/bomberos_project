from django.http                                import HttpResponse
from django.http                                import HttpRequest, HttpResponse, HttpResponseForbidden
from django.db.models                           import Q
from django.shortcuts                           import render, get_object_or_404
from django.contrib.auth.decorators             import login_required

# MODELOS
from major_equipment.models.unit                import *

# Utilidades
from ..utils.permission                          import *

# Configuración de logging
import logging
logger = logging.getLogger('myapp')

@login_required # Listado de unidades.
def view_get_units(request: HttpRequest) -> HttpResponse:
    """
    Vista para listar unidades visibles para el usuario autenticado, en base los permisos
    que tenga el usuario asignado. 
        
    """
    user = request.user # Usuario actual
    
    search_filter = request.GET.get("search-filter", "") # Filtro de busqueda

    units = get_units_for_user(user) # QuerySet de unidades.

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
    if not user_can_view_unit(user, unit):
        logger.warning(f'Intento de acceso no autorizado de {user} a {unit}')
        return HttpResponseForbidden(
            "No tienes autorización para acceder a esta unidad. "
            "Este intento ha sido registrado para fines de auditoría. "
            "Si consideras que se trata de un error, por favor comunícate con el área de informática."
        )
    
    images = unit.images.all()

    context = {
        "unit": unit,
        "images": images,
        "title": "Material Mayor | Bomberos Quintero",
    }
    return render(request, "major_equipment/unit/unit.html", context)