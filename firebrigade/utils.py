from firebrigade.models import Membership


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
