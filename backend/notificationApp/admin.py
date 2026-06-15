# notificationApp/admin.py - Updated to match simplified model

from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user__full_name', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'read_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Notification Details', {
            'fields': ('notification_type', 'title', 'message', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'read_at', 'sent_at', 'expires_at')
        }),
        ('Actions', {
            'fields': ('action_url', 'action_text')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at')
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'new_assignment_notification', 
        'assignment_modification_notification',
        'task_missed_alerts', 
        'dnd_enabled'
    ]
    search_fields = ['user__full_name', 'user__work_mail_address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Task Notifications', {
            'fields': (
                'task_end_reminder', 'task_end_reminder_minutes',
                'upcoming_task_alert', 'task_missed_alerts'
            )
        }),
        ('Assignment Notifications', {
            'fields': (
                'new_assignment_notification', 
                'assignment_modification_notification',
                'assignment_completion_notification'
            )
        }),
        ('System Notifications', {
            'fields': ('system_alerts', 'performance_alerts')
        }),
        ('Channels', {
            'fields': ('web_notifications', 'email_notifications')
        }),
        ('Do Not Disturb', {
            'fields': ('dnd_enabled', 'dnd_start_time', 'dnd_end_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )