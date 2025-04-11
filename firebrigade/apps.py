from django.apps import AppConfig


class FirebrigadeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'firebrigade'
    verbose_name = "Cuerpo de Bomberos"

    def ready(self):
        import firebrigade.signals 
