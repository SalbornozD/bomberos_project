from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
import os
from .models import Membership, MembershipHistory, Entity
from config.utils.files import delete_file

@receiver(pre_save, sender=Membership)
def save_previous_membership_to_history(sender, instance: Membership, **kwargs):
    """
    Antes de guardar una asignación, si el cargo o entidad cambian,
    guarda la asignación anterior como historial con fecha de término.
    """
    if instance.pk:  # Solo si ya existía (update)
        old_instance = Membership.objects.get(pk=instance.pk)

        if old_instance.position != instance.position or old_instance.entity != instance.entity:
            MembershipHistory.objects.create(
                full_name=old_instance.user.get_full_name(),
                position=old_instance.position,
                entity=old_instance.entity,
                start_date=now().date(),  # opcional: usar un campo real
                end_date=now().date()
            )


@receiver(post_save, sender=Membership)
def create_history_on_new_membership(sender, instance: Membership, created: bool, **kwargs):
    """
    Al crear una nueva asignación, guarda un historial con fecha de inicio.
    """
    if created:
        MembershipHistory.objects.create(
            full_name=instance.user.get_full_name(),
            position=instance.position,
            entity=instance.entity,
            start_date=now().date()
        )


@receiver(post_delete, sender=Membership)
def create_history_on_membership_delete(sender, instance: Membership, **kwargs):
    """
    Al eliminar una asignación activa, guarda una entrada de historial con fecha de término.
    """
    MembershipHistory.objects.create(
        full_name=instance.user.get_full_name(),
        position=instance.position,
        entity=instance.entity,
        start_date=now().date(),
        end_date=now().date()
    )

# Cuando se elimina una entidad, también se elimina su logo
@receiver(post_delete, sender=Entity)
def delete_logo_on_entity_delete(sender, instance, **kwargs):
    if instance.logo:
        delete_file(instance.logo.path)

# Cuando se reemplaza el logo, eliminar el anterior
@receiver(pre_save, sender=Entity)
def delete_old_logo_on_entity_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = Entity.objects.get(pk=instance.pk)
    except Entity.DoesNotExist:
        return

    if old_instance.logo and old_instance.logo != instance.logo:
        delete_file(old_instance.logo.path)