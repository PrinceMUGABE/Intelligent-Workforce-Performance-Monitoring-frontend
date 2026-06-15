# dashboardApp/urls.py

from django.urls import path
from . import views

app_name = 'dashboardApp'

urlpatterns = [
    # Main dashboard endpoint (with role-based dispatch)
    path('', views.get_dashboard, name='dashboard'),
]