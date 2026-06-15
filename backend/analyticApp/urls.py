# analyticApp/urls.py

from django.urls import path
from . import views

app_name = 'analyticApp'

urlpatterns = [
    # Main analytics dashboard
    path('dashboard/', views.get_analytics_dashboard, name='analytics_dashboard'),
    
    # Department analytics
    path('department/<int:department_id>/', views.get_department_analytics, name='department_analytics'),
    
    # User analytics
    path('user/<int:user_id>/', views.get_user_analytics, name='user_analytics'),
    
    # System overview
    path('overview/', views.get_system_overview, name='system_overview'),
]