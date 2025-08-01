from firebrigade.models import Membership, Entity, Position
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

def get_entities_for_user(user: User) -> QuerySet:
    """
    Retorna las entidades a las que el usuario tiene acceso.
    - Si el usuario es superusuario o tiene permiso global, retorna todas las entidades.
    - Si el usuario tiene el permiso 'view_own_entity' a través de alguna membresía, retorna solo esas entidades.
    - Si no tiene permisos, retorna un QuerySet vacío.
    """
    entities = Entity.objects.all()
    if user.is_superuser or user.has_perm('firebrigade.view_entity'):
        return entities

    # Entidades en las que el usuario tiene el permiso por algún cargo
    own_entities = get_user_entities_with_permission(user, 'view_own_entity')
    if own_entities.exists():
        return own_entities

    return Entity.objects.none()

def get_user_memberships(user: User) -> QuerySet:
    """
    Retorna todas las membresías activas del usuario.
    """
    return Membership.objects.filter(user=user)

def get_user_entities(user: User) -> QuerySet:
    """
    Retorna todas las entidades a las que el usuario pertenece por membresía.
    """
    return Entity.objects.filter(membership__user=user).distinct()

def get_user_positions(user: User) -> QuerySet:
    """
    Retorna todos los cargos que ocupa el usuario en cualquier entidad.
    """
    return Position.objects.filter(membership__user=user).distinct()

def get_user_entities_with_permission(user: User, codename: str) -> QuerySet:
    """
    Devuelve las entidades en las que el usuario tiene, a través de algún cargo, el permiso indicado.
    """
    return Entity.objects.filter(
        membership__user=user,
        membership__position__permissions__codename=codename
    ).distinct()
