# activityApp/apps.py

from django.apps import AppConfig


class ActivityAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activityApp'
    verbose_name = 'Activity Tracking'