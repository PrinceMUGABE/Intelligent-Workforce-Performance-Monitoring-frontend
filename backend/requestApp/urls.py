from django.urls import path
from . import views

app_name = 'requestApp'

urlpatterns = [
    # Create request
    path('create/', views.create_day_off_request, name='create_request'),
    
    # Get requests
    path('all/', views.get_all_requests, name='get_all_requests'),
    path('<int:request_id>/', views.get_request_by_id, name='get_request_by_id'),
    path('my-requests/', views.get_my_requests, name='get_my_requests'),
    path('user/<int:user_id>/', views.get_requests_by_user, name='get_requests_by_user'),
    path('stats/', views.get_requests_stats, name='get_requests_stats'),
    
    # Update request
    path('<int:request_id>/update/', views.update_request, name='update_request'),
    
    # Actions
    path('<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('<int:request_id>/delete/', views.delete_request, name='delete_request'),
]