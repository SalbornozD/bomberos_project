from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from firebrigade.models import Entity
from firebrigade.utils import get_user_entity, get_user_entity_id
from major_equipment.models import MajorEquipment, MaintenanceReport


# ==========================
# Funciones sobre Unidades
# ==========================

def get_units(user: User):
    """
    Devuelve un queryset de unidades visibles para el usuario, 
    dependiendo de sus permisos.

    Parámetros:
        user (User): Usuario autenticado.

    Retorna:
        QuerySet: Un queryset de MajorEquipment filtrado según permisos.
    """
    units = MajorEquipment.objects.all()

    if user.is_superuser or user.has_perm('major_equipment.view_majorequipment'):
        return units
    
    if user.has_perm('major_equipment.view_company_majorequipment'):
        entity = get_user_entity(user)
        return units.filter(entity=entity)
    
    return MajorEquipment.objects.none()


def can_view_unit(user: User, unit: MajorEquipment) -> bool:
    """
    Determina si el usuario tiene permiso para ver una unidad específica.

    Parámetros:
        user (User): Usuario autenticado.
        unit (MajorEquipment): Unidad a evaluar.

    Retorna:
        bool: True si puede ver la unidad, False en caso contrario.
    """
    if user.is_superuser or user.has_perm('major_equipment.view_majorequipment'):
        return True
    if user.has_perm('major_equipment.view_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    return False


def can_create_unit(user: User, entity: Entity) -> bool:
    """
    Determina si el usuario tiene permiso para crear una unidad 
    asociada a la entidad especificada.

    Parámetros:
        user (User): Usuario autenticado.
        entity (Entity): Entidad a la que se asociará la nueva unidad.

    Retorna:
        bool: True si puede crear la unidad, False en caso contrario.
    """
    if user.is_superuser or user.has_perm('major_equipment.add_majorequipment'):
        return True
    if user.has_perm('major_equipment.add_company_majorequipment'):
        return entity == get_user_entity(user)
    return False


def can_edit_unit(user: User, unit: MajorEquipment, new_entity: Entity) -> bool:
    """
    Determina si el usuario tiene permiso para editar una unidad 
    y cambiarla a otra entidad.

    Parámetros:
        user (User): Usuario autenticado.
        unit (MajorEquipment): Unidad a editar.
        new_entity (Entity): Nueva entidad destino.

    Retorna:
        bool: True si puede editar, False en caso contrario.
    """
    if user.is_superuser or user.has_perm('major_equipment.change_majorequipment'):
        return True
    if user.has_perm('major_equipment.change_company_majorequipment'):
        user_entity = get_user_entity(user)
        return unit.entity == user_entity and new_entity == user_entity
    return False


def can_delete_unit(user: User, unit: MajorEquipment) -> bool:
    """
    Determina si el usuario tiene permiso para eliminar una unidad.

    Parámetros:
        user (User): Usuario autenticado.
        unit (MajorEquipment): Unidad a eliminar.

    Retorna:
        bool: True si puede eliminar, False en caso contrario.
    """
    if user.is_superuser or user.has_perm('major_equipment.delete_majorequipment'):
        return True
    if user.has_perm('major_equipment.delete_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    return False


# =====================================
# Funciones sobre Reportes de Mantención
# =====================================

def get_maintenance_reports(user: User):
    """
    Devuelve un queryset de reportes de mantención que el usuario puede ver.

    Parámetros:
        user (User): Usuario autenticado.

    Retorna:
        QuerySet: Un queryset de MaintenanceReport filtrado según permisos.
    """
    if user.is_superuser or user.has_perm('major_equipment.view_maintenancereport'):
        return MaintenanceReport.objects.all()

    if user.has_perm('major_equipment.view_company_maintenancereports'):
        entity = get_user_entity(user)
        return MaintenanceReport.objects.filter(unit__entity=entity)

    if user.has_perm('major_equipment.view_own_maintenancereports'):
        return MaintenanceReport.objects.filter(reported_by=user)

    return MaintenanceReport.objects.none()


def can_view_maintenance_report(user: User, report: MaintenanceReport) -> bool:
    """
    Verifica si el usuario puede ver un reporte de mantención específico.

    Parámetros:
        user (User): Usuario autenticado.
        report (MaintenanceReport): Reporte a consultar.

    Retorna:
        bool: True si puede verlo, False en caso contrario.
    """
    if user.is_superuser or user.has_perm('major_equipment.view_maintenancereport'):
        return True
    if user.has_perm('major_equipment.view_company_maintenancereports'):
        return report.unit.entity == get_user_entity(user)
    if user.has_perm('major_equipment.view_own_maintenancereports'):
        return report.reported_by == user
    return False


def can_create_maintenance_report(user: User) -> bool:
    """
    Verifica si el usuario tiene permiso para crear un reporte 
    de mantención a su propio nombre.

    Parámetros:
        user (User): Usuario autenticado.

    Retorna:
        bool: True si puede crear reportes, False si no.
    """
    return user.is_superuser or user.has_perm('major_equipment.create_own_maintenancereports')


def can_edit_maintenance_report(user: User, report: MaintenanceReport) -> str | bool:
    """
    Verifica si el usuario puede editar un reporte y qué campos puede modificar.

    Parámetros:
        user (User): Usuario autenticado.
        report (MaintenanceReport): Reporte a modificar.

    Retorna:
        str | bool:
            - 'all' si puede editar todos los campos.
            - 'description' si solo puede editar el campo descripción.
            - False si no puede editar nada.
    """
    if user.is_superuser or user.has_perm('major_equipment.change_maintenancereport'):
        return 'all'
    if user.has_perm('major_equipment.change_body_maintenancereports'):
        return 'description'
    if user.has_perm('major_equipment.change_company_maintenancereports') and report.unit.entity == get_user_entity(user):
        return 'description'
    if user.has_perm('major_equipment.change_own_maintenancereports') and report.reported_by == user:
        return 'description'
    return False


def can_delete_maintenance_report(user: User, report: MaintenanceReport) -> bool:
    """
    Verifica si el usuario puede eliminar un reporte de mantención.

    Parámetros:
        user (User): Usuario autenticado.
        report (MaintenanceReport): Reporte a eliminar.

    Retorna:
        bool: True si puede eliminarlo, False si no.
    """
    if user.is_superuser or user.has_perm('major_equipment.delete_maintenancereport'):
        return True
    if user.has_perm('major_equipment.delete_company_maintenancereports'):
        return report.unit.entity == get_user_entity(user)
    if user.has_perm('major_equipment.delete_own_maintenancereports'):
        return report.reported_by == user
    return False
