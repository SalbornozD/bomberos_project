from firebrigade.models import *
from django.db.models.query import QuerySet

def get_entities_for_user(user: User) -> QuerySet[Entity]:
    """
    Retorna las entidades a las que el usuario tiene acceso.
    Si el usuario es superusuario, retorna todas las entidades.
    Si el usuario tiene el permiso `view_own_entity`, retorna solo la entidad
    asociada a su Membership.
    Si no tiene permisos, retorna un QuerySet vacío.

    :param user: instancia de User
    :return: QuerySet de Entity
    """
    entities = Entity.objects.all()
    if user.is_superuser or user.has_perm('firebrigade.view_entity'): return entities
    elif user.has_perm('firebrigade.view_own_entity'): return entities.filter(pk=get_user_entity_id(user))
    else: return Entity.objects.none()

def get_user_membership(user):
    """
    Retorna el objeto Membership del usuario si existe.
    Si no tiene, retorna None.
    """
    return Membership.objects.filter(user=user).first()


def get_user_entity(user):
    """
    Retorna la entidad (compañía/comandancia/etc) del usuario.
    Si no tiene Membership asociado, retorna None.
    """
    membership = get_user_membership(user)
    return membership.entity if membership else None


def get_user_position(user):
    """
    Retorna el cargo (Position) del usuario.
    Si no tiene Membership asociado, retorna None.
    """
    membership = get_user_membership(user)
    return membership.position if membership else None


def get_user_entity_id(user):
    """
    Retorna el ID de la entidad del usuario (optimizado para filtros).
    Si no tiene Membership asociado, retorna None.
    """
    membership = get_user_membership(user)
    return membership.entity_id if membership else None


def get_user_position_id(user):
    """
    Retorna el ID del cargo del usuario.
    Si no tiene Membership asociado, retorna None.
    """
    membership = get_user_membership(user)
    return membership.position_id if membership else None
