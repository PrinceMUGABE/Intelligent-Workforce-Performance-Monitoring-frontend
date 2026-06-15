# reportApp/urls.py
from django.urls import path
from . import views

app_name = 'reportApp'

urlpatterns = [
    # Get available reports based on user role
    path('available/', views.get_available_reports, name='available-reports'),
    
    # User reports
    path('users/', views.generate_user_report, name='user-report'),
    
    # Department reports
    path('departments/', views.generate_department_report, name='department-report'),
    
    # Task reports
    path('tasks/', views.generate_task_report, name='task-report'),
    
    # Task assignment reports
    path('assignments/', views.generate_task_assignment_report, name='assignment-report'),
    
    # Day-off request reports
    path('dayoff/', views.generate_dayoff_report, name='dayoff-report'),
    
    # Activity reports
    path('activities/', views.generate_activity_report, name='activity-report'),
    
    # Performance reports
    path('performance/', views.generate_performance_report, name='performance-report'),
    path('performance/<int:user_id>/', views.generate_performance_report, name='performance-report-user'),
    
    # Organization reports
    path('organization/', views.generate_organization_report, name='organization-report'),
]