# analyticApp/apps.py

from django.apps import AppConfig


class AnalyticAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analyticApp'
    verbose_name = 'Analytics'
    
    def ready(self):
        """
        Import any signals or perform initialization when app is ready
        """
        pass