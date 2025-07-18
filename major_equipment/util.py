from django.contrib.auth.models import User
from django.db.models import QuerySet
from firebrigade.models import Entity
from firebrigade.utils import get_user_entity
from major_equipment.models import MajorEquipment, Report, maintenance_log


# ==========================
# Unidades
# ==========================




def can_view_unit(user: User, unit: MajorEquipment) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.view_majorequipment'):
        return True
    if user.has_perm('major_equipment.view_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    return False


def can_create_unit(user: User, entity: Entity) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.add_majorequipment'):
        return True
    if user.has_perm('major_equipment.add_company_majorequipment'):
        return entity == get_user_entity(user)
    return False


def can_edit_unit(user: User, unit: MajorEquipment, new_entity: Entity) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.change_majorequipment'):
        return True
    if user.has_perm('major_equipment.change_company_majorequipment'):
        ue = get_user_entity(user)
        return unit.entity == ue and new_entity == ue
    return False


def can_delete_unit(user: User, unit: MajorEquipment) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.delete_majorequipment'):
        return True
    if user.has_perm('major_equipment.delete_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    return False


# =====================================
# Reportes de Desperfectos (Report)
# =====================================

def get_maintenance_reports(user: User) -> QuerySet[Report]:
    """
    Devuelve Report.objects filtrados según:
    - superuser o view_report                     → todos
    - view_company_maintenancereport              → por entidad
    - view_own_maintenancereport                  → propios
    - en otro caso                                → ninguno
    """
    qs = Report.objects.select_related('unit__entity', 'author')
    if user.is_superuser or user.has_perm('major_equipment.view_report'):
        return qs
    if user.has_perm('major_equipment.view_company_maintenancereport'):
        return qs.filter(unit__entity=get_user_entity(user))
    if user.has_perm('major_equipment.view_own_maintenancereport'):
        return qs.filter(author=user)
    return Report.objects.none()


def can_view_maintenance_report(user: User, report: Report) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.view_report'):
        return True
    if user.has_perm('major_equipment.view_company_maintenancereport'):
        return report.unit.entity == get_user_entity(user)
    if user.has_perm('major_equipment.view_own_maintenancereport'):
        return report.author == user
    return False


def can_edit_maintenance_report(user: User, report: Report) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.change_report'):
        return True
    if (user.has_perm('major_equipment.change_company_maintenancereport') and
            report.unit.entity == get_user_entity(user)):
        return True
    if (user.has_perm('major_equipment.change_own_maintenancereport') and
            report.author == user):
        return True
    return False


def can_delete_maintenance_report(user: User, report: Report) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.delete_report'):
        return True
    if (user.has_perm('major_equipment.delete_company_maintenancereport') and
            report.unit.entity == get_user_entity(user)):
        return True
    if (user.has_perm('major_equipment.delete_own_maintenancereport') and
            report.author == user):
        return True
    return False


def can_create_maintenance_report(user: User) -> bool:
    """
    Permiso para crear reportes.
    """
    return user.is_superuser or user.has_perm('major_equipment.add_report')


# =====================================
# Solicitudes de Mantención (MaintenanceLog)
# =====================================

def can_create_maintenance_request(user: User) -> bool:
    return user.is_superuser or user.has_perm('major_equipment.add_maintenancelog')


def get_maintenance_requests(user: User) -> QuerySet[maintenance_log]:
    qs = maintenance_log.objects.select_related('unit__entity', 'author')
    if user.is_superuser or user.has_perm('major_equipment.view_maintenancelog'):
        return qs
    if user.has_perm('major_equipment.view_company_maintenancerequests'):
        return qs.filter(unit__entity=get_user_entity(user))
    if user.has_perm('major_equipment.view_own_maintenancerequests'):
        return qs.filter(author=user)
    return maintenance_log.objects.none()


def can_view_maintenance_request(user: User, req: maintenance_log) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.view_maintenancelog'):
        return True
    if (user.has_perm('major_equipment.view_company_maintenancerequests') and
            req.unit.entity == get_user_entity(user)):
        return True
    if (user.has_perm('major_equipment.view_own_maintenancerequests') and
            req.author == user):
        return True
    return False


def can_edit_maintenance_request(user: User, req: maintenance_log) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.change_maintenancelog'):
        return True
    if (user.has_perm('major_equipment.change_company_maintenancerequests') and
            req.unit.entity == get_user_entity(user)):
        return True
    if (user.has_perm('major_equipment.change_own_maintenancerequests') and
            req.author == user):
        return True
    return False


def can_delete_maintenance_request(user: User, req: maintenance_log) -> bool:
    if user.is_superuser or user.has_perm('major_equipment.delete_maintenancelog'):
        return True
    if (user.has_perm('major_equipment.delete_company_maintenancerequests') and
            req.unit.entity == get_user_entity(user)):
        return True
    if (user.has_perm('major_equipment.delete_own_maintenancerequests') and
            req.author == user):
        return True
    return False


def can_approve_as_comandancia(user: User) -> bool:
    return user.is_superuser or user.has_perm('major_equipment.approve_maintenance_as_command')


def can_approve_as_admin(user: User) -> bool:
    return user.is_superuser or user.has_perm('major_equipment.approve_maintenance_as_admin')
