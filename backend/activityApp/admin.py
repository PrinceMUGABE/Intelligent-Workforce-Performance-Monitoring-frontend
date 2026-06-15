# activityApp/admin.py

from django.contrib import admin
from .models import Activity, ActivitySummary


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'activity_type',
        'user',
        'status_code',
        'device_type',
        'created_at',
        'is_success'
    ]
    
    list_filter = [
        'activity_type',
        'status_code',
        'device_type',
        'created_at',
    ]
    
    search_fields = [
        'user__full_name',
        'user__work_mail_address',
        'description',
        'endpoint',
        'ip_address'
    ]
    
    readonly_fields = [
        'created_at',
        'user_agent',
        'request_data',
        'response_data'
    ]
    
    fieldsets = (
        ('Activity Information', {
            'fields': (
                'activity_type',
                'user',
                'status_code',
                'description'
            )
        }),
        ('System Information', {
            'fields': (
                'ip_address',
                'user_agent',
                'device_type',
                'browser',
                'operating_system'
            )
        }),
        ('Request Information', {
            'fields': (
                'request_method',
                'endpoint',
                'request_data',
                'response_data',
                'duration_ms'
            ),
            'classes': ('collapse',)
        }),
        ('Related Objects', {
            'fields': (
                'related_user_id',
                'related_department_id'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def is_success(self, obj):
        return obj.is_success()
    is_success.boolean = True
    is_success.short_description = 'Success'


@admin.register(ActivitySummary)
class ActivitySummaryAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'period_type',
        'period_start',
        'user',
        'activity_type',
        'total_count',
        'success_count',
        'error_count'
    ]
    
    list_filter = [
        'period_type',
        'period_start',
        'activity_type'
    ]
    
    search_fields = [
        'user__full_name',
        'user__work_mail_address'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'period_start'