# accounts/adapters.py
from django.conf import settings
from django.core.exceptions import PermissionDenied
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class DomainRestrictedAdapter(DefaultSocialAccountAdapter):
    """
    Restringe el login social a un dominio corporativo específico y
    (opcional) exige que el correo venga verificado por el IdP.
    """

    def pre_social_login(self, request, sociallogin):
        # Email provisto por el proveedor (Google OIDC)
        email = (sociallogin.user.email or "").strip().lower()
        if not email:
            raise PermissionDenied("No se recibió un correo válido desde el proveedor.")

        # Dominio permitido (configurable por settings/.env)
        allowed_domain = getattr(settings, "GOOGLE_ALLOWED_DOMAIN", "bomberosquintero.cl")
        if not email.endswith(f"@{allowed_domain}"):
            raise PermissionDenied("Solo cuentas corporativas pueden iniciar sesión.")

        # (Opcional pero recomendado) verificar bandera 'email_verified' si viene en extra_data
        extra = (sociallogin.account.extra_data or {})
        # Google suele incluir 'email_verified': True/False
        if extra.get("email_verified") is False:
            raise PermissionDenied("Tu correo de Google no aparece verificado.")

        # Si quieres, aquí podrías mapear roles/grupos según datos externos
        # (dejado fuera para mantenerlo simple).
        # p. ej.: self._sync_roles_from_google_groups(email)

    def populate_user(self, request, sociallogin, data):
        """
        Completa campos del usuario local a partir de los datos del proveedor.
        Mantiene el comportamiento base y normaliza nombre/apellidos.
        """
        user = super().populate_user(request, sociallogin, data)

        # Normaliza nombres si Google los provee
        # NOTE: 'data' keys dependen del proveedor; con Google OIDC suelen venir:
        #   name, given_name, family_name, picture, email, email_verified
        user.first_name = (data.get("given_name") or user.first_name or "").strip()
        user.last_name = (data.get("family_name") or user.last_name or "").strip()
        # Si prefieres usar 'name' completo:
        # full_name = (data.get("name") or "").strip()

        return user
