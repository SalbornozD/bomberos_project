from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from docs.models import FileVencible

class Command(BaseCommand):
    help = 'Envía un correo diario a cada usuario del grupo "notificar_vencimiento" con los documentos por vencer o vencidos.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        notice_days = [30, 20] + list(range(14, -1, -1))

        # Buscar documentos próximos a vencer
        upcoming_files = FileVencible.objects.filter(
            expiration_date__in=[today + timedelta(days=days) for days in notice_days]
        )
        # Buscar documentos vencidos
        expired_files = FileVencible.objects.filter(expiration_date__lt=today)

        # Si no hay ningún documento, no hace nada
        if not upcoming_files.exists() and not expired_files.exists():
            self.stdout.write(self.style.WARNING("No hay documentos por vencer ni vencidos. No se enviarán correos."))
            return

        # Construir el mensaje de correo
        message_lines = []
        if upcoming_files.exists():
            message_lines.append("Documentos próximos a vencer:")
            for file in upcoming_files:
                message_lines.append(f"- {file.short_name} (vence el {file.expiration_date})")
            message_lines.append("")

        if expired_files.exists():
            message_lines.append("Documentos vencidos:")
            for file in expired_files:
                message_lines.append(f"- {file.short_name} (venció el {file.expiration_date})")
            message_lines.append("")

        message_lines.append("Este es un correo automatico.")
        message_lines.append("Puedes acceder a los documentos en el sistema.")
        message_lines.append("~ Equipo de informatica :D")


        subject = "Notificación de documentos por vencer o vencidos"
        message = "\n".join(message_lines)

        # Buscar usuarios del grupo
        try:
            group = Group.objects.get(name="notificar_vencimiento")
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('El grupo "notificar_vencimiento" no existe.'))
            return

        # Enviar correo a cada usuario del grupo
        for user in group.user_set.all():
            if user.email:
                send_mail(
                    subject,
                    message,
                    None,  # Usa DEFAULT_FROM_EMAIL de settings.py
                    [user.email],
                )
                self.stdout.write(self.style.SUCCESS(f"Correo enviado a {user.email}."))
            else:
                self.stdout.write(self.style.WARNING(f"El usuario {user.username} no tiene email registrado."))

