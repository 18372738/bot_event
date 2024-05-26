from django.apps import AppConfig


class EventModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_models'


class EventModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_models'

    def ready(self):
        import event_models.signals
