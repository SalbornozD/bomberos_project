from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission


class RolePermissionBackend(ModelBackend):
    """
    Backend que permite usar permisos heredados desde el cargo del usuario (Position).
    """

    def get_user_permissions(self, user_obj: User, obj=None):
        if not hasattr(user_obj, "membership"):
            return set()

        permissions = user_obj.membership.position.permissions.all()
        perms = set(
            f"{perm.content_type.app_label}.{perm.codename}"
            for perm in permissions
        )
        return perms

    def has_perm(self, user_obj: User, perm: str, obj=None) -> bool:
        if not user_obj.is_active:
            return False
        if user_obj.is_superuser:
            return True
        return (
            perm in self.get_user_permissions(user_obj, obj)
            or super().has_perm(user_obj, perm, obj)
        )
