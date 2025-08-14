from django.contrib.auth.backends import ModelBackend

class RolePermissionBackend(ModelBackend):
    """
    Agrega permisos heredados desde el cargo (Position) del usuario,
    además de conservar los permisos propios del usuario.
    """

    def get_user_permissions(self, user_obj, obj=None):
        # Mantener comportamiento estándar (permisos asignados directamente al usuario)
        perms = set(super().get_user_permissions(user_obj, obj))

        # Cortocircuitos seguros
        if not getattr(user_obj, "is_authenticated", False) or not getattr(user_obj, "is_active", False):
            return perms

        # Tomar permisos desde Position si existe membership y position
        membership = getattr(user_obj, "membership", None)
        position = getattr(membership, "position", None)
        if not position:
            return perms

        # Evita N+1 y construye "app_label.codename"
        qs = position.permissions.select_related("content_type") \
                                 .values_list("content_type__app_label", "codename")
        perms |= {f"{app}.{code}" for app, code in qs}
        return perms
