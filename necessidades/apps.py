from django.apps import AppConfig


class NecessidadesConfig(AppConfig):
    name = 'necessidades'

    def ready(self):
        from . import signals
