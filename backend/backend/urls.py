# urls.py - ROOT URLS
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('departments/', include('departmentApp.urls')),
    path('task/', include('taskApp.urls')),
    path('notification/', include('notificationApp.urls')),
    path('task-assignments/', include('taskAssignmentApp.urls')),
    path('performance/', include('performanceApp.urls')),
    path('request/', include('requestApp.urls')),
    path('analytics/', include('analyticApp.urls')),
    path('dashboard/', include('dashboardApp.urls')),
    path('activity/', include('activityApp.urls')),
    path('report/', include('reportApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)




    