from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    # Employee endpoints
    path('my-performance/', views.get_my_performance, name='my-performance'),
    
    # User performance endpoints
    path('users/<int:user_id>/', views.get_user_performance, name='user-performance'),
    path('all/', views.get_all_performances, name='all-performances'),
    
    # Department performance endpoints
    path('departments/<int:department_id>/', views.get_department_performance, name='department-performance'),
    path('departments/summaries/', views.get_department_summaries, name='department-summaries'),
    
    # Organization performance endpoint
    path('organization/', views.get_organization_performance, name='organization-performance'),
]