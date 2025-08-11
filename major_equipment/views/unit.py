from django.http                                import HttpResponse, FileResponse, Http404
from django.http                                import HttpRequest, HttpResponse, HttpResponseForbidden
from django.db.models                           import Q
from django.shortcuts                           import render, get_object_or_404
from django.contrib.auth.decorators             import login_required
from django.core.exceptions                     import PermissionDenied

# MODELOS
from major_equipment.models.unit                import *

# Utilidades
from ..utils.permission                         import *

import mimetypes
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

@login_required
def protected_unit_image(request, image_id):
    """
    Sirve la imagen de una unidad solo a usuarios autenticados.
    """
    img = get_object_or_404(UnitImage, id=image_id)

    # Permisos de negocio
    if not user_can_view_unit_image(request.user, img):
        logger.warning(
            "Intento de acceso no autorizado | user=%s ip=%s image_id=%s",
            request.user.pk,
            request.META.get("REMOTE_ADDR"),
            image_id,
        )
        raise PermissionDenied("No tienes autorización para acceder a esta imagen.")

    # Adivinar MIME por el nombre (funciona aunque no haya .path en storage remotos)
    filename = getattr(img.image, "name", None)
    content_type, _ = mimetypes.guess_type(filename or "")

    try:
        # Abrir desde el storage configurado (local o remoto)
        file_handle = img.image.open("rb")
    except FileNotFoundError:
        # Registro para auditoría
        logger.error("Archivo de imagen no encontrado en storage | image_id=%s", image_id)
        raise Http404("Imagen no encontrada.")
    except OSError:
        logger.exception("Error de E/S al abrir la imagen | image_id=%s", image_id)
        raise Http404("Imagen no encontrada.")

    # Entrega del archivo
    response = FileResponse(file_handle, content_type=content_type or "application/octet-stream")
    # inline sugiere al browser mostrarla si puede
    response["Content-Disposition"] = f'inline; filename="{filename or "image"}"'
    return response