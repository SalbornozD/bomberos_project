import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import UnitImage, MajorEquipment
from config.utils.files import delete_file

# ============================
# Señales para UnitImage
# ============================

@receiver(post_delete, sender=UnitImage)
def delete_unit_image_on_delete(sender, instance: UnitImage, **kwargs):
    """
    Elimina la imagen del sistema de archivos cuando se elimina la instancia.
    """
    if instance.image:
        delete_file(instance.image.path)


@receiver(pre_save, sender=UnitImage)
def delete_unit_image_on_change(sender, instance: UnitImage, **kwargs):
    """
    Elimina la imagen anterior si se reemplaza por una nueva al editar.
    """
    if not instance.pk:
        return  # nueva instancia, no hay imagen previa
    try:
        old = UnitImage.objects.get(pk=instance.pk)
    except UnitImage.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        delete_file(old.image.path)

# ============================
# Señales para MajorEquipment
# ============================

@receiver(post_delete, sender=MajorEquipment)
def delete_major_equipment_documents_on_delete(sender, instance: MajorEquipment, **kwargs):
    """
    Elimina los documentos asociados al eliminar una unidad.
    """
    fields = [
        'registration_certificate',
        'soap_certificate',
        'technical_inspection_certificate',
        'vehicle_permit'
    ]
    for field in fields:
        file = getattr(instance, field)
        if file:
            delete_file(file.path)


@receiver(pre_save, sender=MajorEquipment)
def delete_major_equipment_documents_on_change(sender, instance: MajorEquipment, **kwargs):
    """
    Elimina los documentos antiguos si han sido reemplazados al editar.
    """
    if not instance.pk:
        return  # nueva instancia
    try:
        old = MajorEquipment.objects.get(pk=instance.pk)
    except MajorEquipment.DoesNotExist:
        return
    fields = [
        'registration_certificate',
        'soap_certificate',
        'technical_inspection_certificate',
        'vehicle_permit'
    ]
    for field in fields:
        old_file = getattr(old, field)
        new_file = getattr(instance, field)
        if old_file and old_file != new_file:
            delete_file(old_file.path)
