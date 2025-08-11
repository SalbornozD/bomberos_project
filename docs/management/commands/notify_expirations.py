from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from docs.models import FileVencible

class Command(BaseCommand):
    help = 'Envía un correo diario a cada usuario del grupo "notificar_vencimiento" con los documentos por vencer o vencidos.'

    def handle(self, *args, **options):
        today = timezone.localdate()
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

        message_lines.append("Estimado(a):")
        message_lines.append("")
        message_lines.append(
            "Le informamos que, de acuerdo con los registros del sistema, existen documentos que "
            "se encuentran próximos a vencer o ya han vencido. A continuación, se detalla el estado actualizado:"
        )
        message_lines.append("")

        if upcoming_files.exists():
            message_lines.append("Documentos próximos a vencer:")
            message_lines.append("")
            for file in upcoming_files:
                message_lines.append(f"- {file.short_name} (vence el {file.expiration_date.strftime('%d de %B de %Y')})")
            message_lines.append("")

        if expired_files.exists():
            message_lines.append("Documentos ya vencidos:")
            message_lines.append("")
            for file in expired_files:
                message_lines.append(f"- {file.short_name} (venció el {file.expiration_date.strftime('%d de %B de %Y')})")
            message_lines.append("")

        message_lines.append("Le recomendamos revisar y gestionar esta situación a la brevedad para asegurar el cumplimiento de los requisitos correspondientes.")
        message_lines.append("")
        message_lines.append("Puede acceder a los documentos directamente en el sistema.")
        message_lines.append("")
        message_lines.append("Este es un mensaje automático. Por favor, no responda a este correo.")
        message_lines.append("Atentamente,")
        message_lines.append("Equipo de Informática")



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

