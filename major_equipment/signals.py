# import os
# import logging
# from textwrap import dedent

# from django.conf import settings
# from django.core.mail import send_mail
# from django.db.models import Q
# from django.db.models.signals import post_delete, pre_save, post_save
# from django.dispatch import receiver
# from django.contrib.auth.models import User

# from .models.unit import UnitImage, Unit
# from .models.report import Report


# logger = logging.getLogger(__name__)


# def delete_file(path):
#     """Elimina un archivo del sistema de archivos si existe."""
#     if path and os.path.isfile(path):
#         try:
#             os.remove(path)
#         except Exception as e:
#             logger.warning("No se pudo eliminar %s: %s", path, e)


# @receiver(post_delete, sender=UnitImage)
# def delete_unit_image_on_delete(sender, instance, **kwargs):
#     """Elimina la imagen del sistema de archivos cuando se borra la instancia."""
#     if instance.image:
#         delete_file(instance.image.path)


# @receiver(pre_save, sender=UnitImage)
# def delete_unit_image_on_change(sender, instance, **kwargs):
#     """Si la imagen se reemplaza, borra la anterior del disco."""
#     if not instance.pk:
#         return
#     try:
#         old = UnitImage.objects.get(pk=instance.pk)
#     except UnitImage.DoesNotExist:
#         return
#     if old.image and old.image != instance.image:
#         delete_file(old.image.path)

# @receiver(post_delete, sender=Unit)
# def delete_unit_documents_on_delete(sender, instance, **kwargs):
#     """Al eliminar una unidad, borra sus archivos asociados."""
#     for field_name in (
#         'registration_certificate',
#         'soap_certificate',
#         'technical_inspection_certificate',
#         'vehicle_permit',
#     ):
#         file_obj = getattr(instance, field_name)
#         # file_obj es instancia de File o FileVencible: accedemos a file_obj.file.path
#         if file_obj and hasattr(file_obj, 'file'):
#             delete_file(file_obj.file.path)


# @receiver(pre_save, sender=Unit)
# def delete_major_equipment_documents_on_change(sender, instance, **kwargs):
#     """Al editar una unidad, si se cambian archivos, borra los antiguos."""
#     if not instance.pk:
#         return
#     try:
#         old = Unit.objects.get(pk=instance.pk)
#     except Unit.DoesNotExist:
#         return

#     for field_name in (
#         'registration_certificate',
#         'soap_certificate',
#         'technical_inspection_certificate',
#         'vehicle_permit',
#     ):
#         old_file = getattr(old, field_name)
#         new_file = getattr(instance, field_name)
#         if old_file and old_file != new_file and hasattr(old_file, 'file'):
#             delete_file(old_file.file.path)


# @receiver(post_save, sender=Report)
# def on_report_created(sender, instance, created, **kwargs):
#     """Envía correo a usuarios relevantes cuando se crea un nuevo reporte."""
#     if not created:
#         return

#     # Recolectar emails de superusuarios o con permiso de ver/crear reportes
#     users = User.objects.filter(
#         Q(is_superuser=True) |
#         Q(user_permissions__codename='add_maintenancereport') |
#         Q(user_permissions__codename='view_own_maintenancereport')
#     ).distinct()
#     recipient_emails = [u.email for u in users if u.email]
#     if not recipient_emails:
#         logger.warning("No hay destinatarios con email para el Report %s", instance.id)
#         return

#     subject = f"[Bomberos] Nuevo reporte en unidad {instance.unit.unit_number}"
#     for email in recipient_emails:
#         user = next((u for u in users if u.email == email), None)
#         fullname = user.get_full_name() or user.username if user else email

#         body = dedent(f"""
#             Hola {fullname},

#             Se ha generado un nuevo reporte de desperfectos para la unidad
#             {instance.unit.unit_number} – {instance.unit.short_description}
#             adscrita a {instance.unit.entity}.

#             • Fecha del reporte: {instance.created_date:%d-%m-%Y %H:%M}
#             • Reportado por: {instance.author.get_full_name() or instance.author.username}

#             Descripción:
#             {instance.description}

#             Accede al sistema para más detalles:
#             {settings.SITE_URL}

#             Saludos,
#             Equipo de Informática – Cuerpo de Bomberos Quintero
#             informatica@bomberosquintero.cl
#         """).strip()

#         try:
#             send_mail(
#                 subject,
#                 body,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [email],
#                 fail_silently=False,
#             )
#             logger.info("Correo Report %s enviado a %s", instance.id, email)
#         except Exception:
#             logger.exception("Error enviando correo para Report %s a %s", instance.id, email)
