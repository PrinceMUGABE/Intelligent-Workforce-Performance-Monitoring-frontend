# dashboardApp/apps.py

from django.apps import AppConfig


class DashboardAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboardApp'
    verbose_name = 'Dashboard'
    
    def ready(self):
        """
        Import any signals or perform initialization when app is ready
        """
        pass