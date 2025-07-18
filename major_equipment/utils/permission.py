from django.contrib.auth.models import User
from django.db.models import QuerySet
from firebrigade.models import Entity
from firebrigade.utils import get_user_entity
from major_equipment.models import Unit

def get_units(user: User) -> QuerySet[Unit]:
    """
    Devuelve las unidades visibles para el usuario, dependiendo de sus permisos:
    - superuser o view_majorequipment -> Todas
    - view_company_majorequipment     -> De su entidad
    - en otro caso                    -> Ninguna
    """

    units = Unit.objects.all()
    if user.is_superuser or user.has_perm('major_equipment.view_unit'):
        return units
    
    if user.has_perm('major_equipment.view_company_majorequipment'):
        return units.filter(entity=get_user_entity(user))
    
    return Unit.objects.none()


def can_view_unit(user: User, unit: Unit) -> bool:
    """
    Verifica si el usuario puede ver la unidad. Devolviendo True o False.
    """
    if user.is_superuser or user.has_perm('major_equipment.view_unit'):
        return True
    
    if user.has_perm('major_equipment.view_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    
    return False

def can_edit_unit(user: User, unit: Unit) -> bool:
    """
    Verifica si el usuario puede editar la unidad. Devolviendo True o False.
    """
    if user.is_superuser or user.has_perm('major_equipment.change_majorequipment'):
        return True
    
    if user.has_perm('major_equipment.change_company_majorequipment'):
        return unit.entity == get_user_entity(user)
    
    return False