from major_equipment.models import *
from firebrigade.models import Entity
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from firebrigade.utils import get_user_entities_with_permission

def get_units_for_user(user: User) -> QuerySet:
    """
    Devuelve las unidades visibles para el usuario:
    - superuser o 'major_equipment.view_unit' -> todas
    - permiso 'view_company_majorequipment' en entidad(s) por cargo -> solo esas
    - en otro caso -> ninguna
    """
    units = Unit.objects.all()
    if user.is_superuser or user.has_perm('major_equipment.view_unit'):
        return units
    entities = get_user_entities_with_permission(user, 'view_company_majorequipment')
    if entities.exists():
        return units.filter(entity__in=entities)
    return Unit.objects.none()

def user_can_view_unit(user: User, unit: Unit) -> bool:
    """
    Devuelve True si el usuario puede ver la unidad.
    """
    if user.is_superuser or user.has_perm('major_equipment.view_unit'):
        return True
    return get_user_entities_with_permission(user, 'view_company_majorequipment').filter(pk=unit.entity_id).exists()

def user_can_view_unit_image(user: User, image: UnitImage) -> bool:
    """
    Devuelve True o False si el usuario puede ver la imagen.
    """
    return user_can_view_unit(user, image.unit)