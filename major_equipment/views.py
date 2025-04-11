from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from major_equipment.models import MajorEquipment
from firebrigade.models import Membership, Entity, EntityType

@login_required
def get_units(request):
    """
    Vista para listar unidades de Material Mayor.

    Atributos:
        request (HttpRequest): La solicitud HTTP del usuario autenticado.

    Permisos y lógica:
        - Si el usuario tiene `major_equipment.view_majorequipment`, puede ver todas las unidades.
        - Si tiene `major_equipment.view_company_majorequipment`, solo puede ver unidades de su entidad.
        - Si no tiene permisos válidos, retorna 403.

    Retorna:
        HttpResponse: Renderizado de la plantilla con contexto paginado.
    """
    user = request.user
    search_filter = request.GET.get("search_filter")
    status_filter = request.GET.get("status_filter")
    fire_company_filter = request.GET.get("fire_company_filter")

    if user.is_superuser or user.has_perm("major_equipment.view_majorequipment"):
        units = MajorEquipment.objects.all()
        fire_companies = Entity.objects.filter(type="COMPANY")
    elif user.has_perm("major_equipment.view_company_majorequipment"):
        membership = Membership.objects.filter(user=user).select_related("entity").first()
        if not membership or not membership.entity:
            return HttpResponseForbidden("No estás asociado a ninguna entidad.")
        units = MajorEquipment.objects.filter(entity=membership.entity)
        fire_companies = []
    else:
        return HttpResponseForbidden("No tienes permisos para ver unidades.")

    if search_filter:
        units = units.filter(unit_number__icontains=search_filter)

    if status_filter in ("1", "2", "3"):
        pass # Implementar mas adelante.

    if fire_company_filter and (user.is_superuser or user.has_perm("major_equipment.view_majorequipment")):
        units = units.filter(entity_id=fire_company_filter)

    try:
        page_number = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page_number = 1

    paginator = Paginator(units.select_related("entity").prefetch_related("images"), 8)
    page = paginator.get_page(page_number)

    context = {
        "title": "Material Mayor | Bomberos Quintero",
        "units": page,
        "unit_data": [(unit, unit.images.first()) for unit in page],
        "search_filter": search_filter,
        "status_filter": status_filter,
        "fire_company_filter": fire_company_filter,
        "fire_companies": fire_companies,
        "page_number": page_number,
    }

    return render(request, "major_equipment/units.html", context)

@login_required
def get_unit(request, unit_id):
    """
    Muestra el detalle de una unidad de Material Mayor, restringido por permisos de usuario.

    Atributos:
        user (User): Usuario autenticado que realiza la solicitud.
        unit_id (int): ID de la unidad a mostrar, obtenido desde la URL.

    Métodos:
        get_unit(request: HttpRequest, unit_id: int) -> HttpResponse:
            Valida si el usuario tiene permisos para ver la unidad y renderiza su detalle.

    Permisos requeridos:
        - `major_equipment.view_majorequipment`: permite ver todas las unidades.
        - `major_equipment.view_company_majorequipment`: permite ver unidades de las compañías asociadas al usuario.

    Comportamiento:
        - Si el usuario es superusuario o tiene permiso `view_majorequipment`, se permite acceso completo.
        - Si el usuario tiene `view_company_majorequipment`, se permite acceso solo si la unidad pertenece
          a una compañía en la que el usuario tiene un cargo.
        - Si no tiene permisos válidos, se retorna un error 403 (acceso denegado).

    Retorna:
        HttpResponse: Renderizado de la plantilla `major_equipment/unit.html` con contexto de unidad.
        HttpResponseForbidden: Si el usuario no tiene acceso autorizado a la unidad.
    """
    user = request.user
    unit = get_object_or_404(MajorEquipment.objects.select_related("entity"), id=unit_id)

    # --- Verificación de acceso ---
    if user.is_superuser or user.has_perm("major_equipment.view_majorequipment"):
        pass  # acceso completo

    elif user.has_perm("major_equipment.view_company_majorequipment"):
        user_companies = [
            m.entity for m in user.membership_set.select_related("entity")
            if m.entity.type == EntityType.COMPAÑIA
        ]

        if unit.entity not in user_companies:
            return HttpResponseForbidden("No tienes acceso a esta unidad.")

    else:
        return HttpResponseForbidden("No tienes permisos para ver esta unidad.")

    context = {
        "unit": unit,
        "title": "Material Mayor | Bomberos Quintero",
    }

    return render(request, "major_equipment/unit.html", context)