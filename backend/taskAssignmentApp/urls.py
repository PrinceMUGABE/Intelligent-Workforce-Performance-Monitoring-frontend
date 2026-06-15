# taskAssignmentApp/urls.py

from django.urls import path
from . import views
from . import view_status  # Import the status views

app_name = 'taskAssignmentApp'

urlpatterns = [
    # Employee endpoints
    path('my-assignments/', views.get_my_assignments, name='my-assignments'),
    path('current/', views.get_current_assignment, name='current-assignment'),
    path('next/', views.get_next_assignment, name='next-assignment'),
    path('<int:assignment_id>/start/', views.start_assignment, name='start-assignment'),
    path('<int:assignment_id>/complete/', views.complete_assignment, name='complete-assignment'),
    
    # Admin/Manager/Analyst endpoints
    path('all/', views.get_all_assignments, name='all-assignments'),
    path('create/', views.create_assignment, name='create-assignment'),
    path('modify/', views.modify_assignment, name='modify-assignment'),
    path('<int:assignment_id>/delete/', views.delete_assignment, name='delete-assignment'),
    
    # Department assignment endpoints
    path('department/create/', views.create_department_assignments, name='create-department-assignments'),
    
    # Template endpoints
    path('templates/', views.manage_assignment_templates, name='manage-templates'),
    
    # Task overload endpoints
    path('overloads/', views.manage_task_overloads, name='task-overloads'),
    path('overloads/<int:overload_id>/resolve/', views.resolve_task_overload, name='resolve-overload'),
    
    # Bulk assignment endpoints
    path('bulk-assign/', views.bulk_assign_task, name='bulk-assign'),
    path('assign-to-department/', views.assign_task_to_department, name='assign-to-department'),
    path('assign-to-users/', views.assign_task_to_users, name='assign-to-users'),
    path('assign-to-role/', views.assign_task_to_role, name='assign-to-role'),
    
    # NEW: Status update endpoints
    path('update-status/', view_status.update_assignment_status, name='update-status'),
    path('<int:assignment_id>/transitions/', view_status.get_possible_status_transitions, name='status-transitions'),
    path('check-missed/', view_status.run_missed_check, name='check-missed'),
]