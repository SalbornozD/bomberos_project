from django.apps import AppConfig


class MajorEquipmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'major_equipment'
    verbose_name = 'Material Mayor'

    def ready(self):
        import major_equipment.signals