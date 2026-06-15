# activityApp/urls.py

from django.urls import path
from . import views

app_name = 'activityApp'

urlpatterns = [
    # Activity listing and filtering
    path('activities/', views.get_all_activities, name='get_all_activities'),
    path('activities/<int:activity_id>/', views.get_activity_by_id, name='get_activity_by_id'),
    path('my-activities/', views.get_my_activities, name='get_my_activities'),
    
    # Activity statistics
    path('stats/', views.get_activity_stats, name='get_activity_stats'),
    path('user/<int:user_id>/summary/', views.get_user_activity_summary, name='get_user_activity_summary'),
    
    # Activity management
    path('cleanup/', views.delete_old_activities, name='delete_old_activities'),
]