from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from firebrigade.models import Entity, Membership
from major_equipment.models import MajorEquipment, MaintenanceReport
from major_equipment.utils import get_units, can_view_unit, get_user_entity, get_maintenance_reports

@login_required
def view_get_units(request):
    """
    Vista para listar unidades de Material Mayor.

    Permite listar unidades visibles para el usuario autenticado, según los
    permisos que tenga asignados.

    Permisos y lógica:
        - Si el usuario tiene `major_equipment.view_majorequipment`, puede ver todas las unidades.
        - Si tiene `major_equipment.view_company_majorequipment`, solo puede ver las unidades de su entidad.
        - Si no tiene permisos válidos, retorna 403.

    Filtros disponibles:
        - search_filter: Filtra por número de unidad (unit_number).
        - status_filter: (Pendiente de implementación)
        - fire_company_filter: Permite filtrar por compañía (solo si el usuario tiene permiso global).

    Parámetros:
        request (HttpRequest): La solicitud HTTP del usuario autenticado.

    Retorna:
        HttpResponse: Renderizado de la plantilla con el contexto correspondiente.
    """

    user = request.user
    search_filter = request.GET.get("search_filter")
    status_filter = request.GET.get("status_filter")
    fire_company_filter = request.GET.get("fire_company_filter")

    # Obtener queryset de unidades segun permisos
    units = get_units(user)

    if not units.exists():
        return HttpResponseForbidden("No tienes permisos para ver unidades.")

    # Filtrado por número de unidad
    if search_filter:
        units = units.filter(unit_number__icontains=search_filter)

    # Filtrado por compañía (solo permitido si tiene permiso global)
    if fire_company_filter and (user.is_superuser or user.has_perm("major_equipment.view_majorequipment")):
        units = units.filter(entity_id=fire_company_filter)

    # Filtrado por status (pendiente implementación)
    if status_filter in ("1", "2", "3"):
        pass

    # Fire Companies disponibles solo para usuarios con permiso global
    fire_companies = Entity.objects.filter(type="COMPANY") if user.is_superuser or user.has_perm("major_equipment.view_majorequipment") else []

    # Paginación
    try:
        page_number = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page_number = 1

    paginator = Paginator(units.select_related("entity").prefetch_related("images").order_by('id'), 8)
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
    Muestra el detalle de una unidad de Material Mayor, validando los permisos del usuario.

    Permisos requeridos:
        - `major_equipment.view_majorequipment`: Permite ver todas las unidades del sistema.
        - `major_equipment.view_company_majorequipment`: Permite ver unidades asociadas a la entidad del usuario.

    Parámetros:
        request (HttpRequest): La solicitud HTTP del usuario autenticado.
        unit_id (int): ID de la unidad a visualizar.

    Comportamiento:
        - Si el usuario es superusuario o tiene `view_majorequipment`, tiene acceso completo.
        - Si tiene `view_company_majorequipment`, puede acceder solo si la unidad pertenece a su entidad.
        - Si no cumple ninguna condición, retorna un error 403.

    Retorna:
        HttpResponse: Renderizado de la plantilla `major_equipment/unit.html` con el contexto correspondiente.
        HttpResponseForbidden: Si el usuario no tiene permisos para ver la unidad.
    """

    user = request.user
    unit = get_object_or_404(MajorEquipment.objects.select_related("entity"), id=unit_id)

    if not can_view_unit(user, unit):
        return HttpResponseForbidden("No tienes permisos para ver esta unidad.")

    context = {
        "unit": unit,
        "title": "Material Mayor | Bomberos Quintero",
    }

    return render(request, "major_equipment/unit.html", context)

@login_required
def get_maintenances_reports(request: HttpRequest) -> HttpResponse:
    """
    Vista para listar reportes de mantención filtrados por permisos y parámetros de búsqueda.

    Permisos:
        - `major_equipment.view_maintenancereport`: Ver todos los reportes (rango cuerpo).
        - `major_equipment.view_company_maintenancereports`: Ver reportes de su entidad (rango compañía).
        - Siempre puede ver sus propios reportes (rango own).

    Parámetros GET:
        - range: Rango visible ('own', 'company', 'body')
        - unit: Filtra por unidad específica.
        - company: Filtra por entidad (solo disponible con permiso global).
        - start_date / end_date: Filtra por rango de fechas.
        - id: Filtra por ID específico.

    Retorna:
        HttpResponse: Renderiza plantilla con reportes paginados.
    """
    user = request.user
    user_entity = get_user_entity(user)

    # Evaluar permisos
    can_view_body = user.is_superuser or user.has_perm('major_equipment.view_maintenancereport')
    can_view_company = user.has_perm('major_equipment.view_company_maintenancereports')
    can_select_range = can_view_body or can_view_company

    # Filtros GET
    current_range = request.GET.get('range', 'own')
    selected_unit = request.GET.get('unit')
    selected_company = request.GET.get('company')
    start_date = request.GET.get('start_date_search')
    end_date = request.GET.get('end_date_search')
    search_id = request.GET.get('id')

    # Base QuerySet de reportes según permisos
    reports = get_maintenance_reports(user).select_related('unit', 'unit__entity', 'reported_by').order_by('-created_at')

    # Filtrado de rango (body/company/own)
    if current_range == 'body' and can_view_body:
        pass  # Ya tiene todo
    elif current_range == 'company' and can_view_company:
        reports = reports.filter(unit__entity=user_entity)
    else:
        reports = reports.filter(reported_by=user)

    # Filtros adicionales
    if selected_unit:
        reports = reports.filter(unit_id=selected_unit)

    if selected_company and can_view_body:
        reports = reports.filter(unit__entity_id=selected_company)

    if start_date:
        reports = reports.filter(created_at__date__gte=start_date)

    if end_date:
        reports = reports.filter(created_at__date__lte=end_date)

    if search_id:
        reports = reports.filter(id=search_id)

    # Unidades visibles según permisos
    units = get_units(user)

    # Paginación
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'can_view_reports_body': can_view_body,
        'can_view_reports_company': can_view_company,
        'can_select_reports_range': can_select_range,
        'current_range': current_range,
        'units': units,
        'current_id_search': search_id,
        'reports': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }

    if can_view_body:
        context['companies'] = Entity.objects.filter(type='COMPANY')

    return render(request, "major_equipment/maintenances_reports.html", context)