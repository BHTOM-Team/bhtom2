from django.apps import AppConfig


class BHTOM2Config(AppConfig):
    name = 'bhtom2'
    
    def ready(self):
        import bhtom2.signals
