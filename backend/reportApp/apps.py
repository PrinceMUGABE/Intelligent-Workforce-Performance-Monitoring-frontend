# reportApp/apps.py
from django.apps import AppConfig


class ReportAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportApp'
    verbose_name = 'Report Management'
    
    def ready(self):
        """Import signals if any"""
        pass