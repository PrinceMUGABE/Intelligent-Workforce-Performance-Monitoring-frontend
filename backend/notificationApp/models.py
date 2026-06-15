# notificationApp/models.py - Simplified version without BreakLog dependency

from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """Store notifications for users"""
    NOTIFICATION_TYPES = [
        ('task_assignment_create', 'Task Assignment Created'),
        ('task_assignment_update', 'Task Assignment Updated'),
        ('task_assignment_complete', 'Task Assignment Completed'),
        ('task_missed_alert', 'Task Missed Alert'),
        ('task_end_reminder', 'Task End Reminder'),
        ('upcoming_task_alert', 'Upcoming Task Alert'),
        ('system_alert', 'System Alert'),
        ('performance_alert', 'Performance Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    
    # Related objects (simplified without BreakLog and UserLog)
    # Remove these foreign keys if not needed
    # break_log = models.ForeignKey(...)  # Remove this
    # user_log = models.ForeignKey(...)   # Remove this
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Action buttons data (JSON)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When notification becomes irrelevant")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['user', 'notification_type', 'is_read']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.full_name} - {self.notification_type} - {self.created_at}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save(update_fields=['is_sent', 'sent_at', 'updated_at'])
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    
class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(
        'userApp.CustomUser',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Task notifications
    task_end_reminder = models.BooleanField(default=True)
    task_end_reminder_minutes = models.IntegerField(default=5, help_text="Minutes before task end")
    
    upcoming_task_alert = models.BooleanField(default=True)
    task_missed_alerts = models.BooleanField(default=True, help_text="Receive alerts for missed tasks")
    
    # Assignment notifications
    new_assignment_notification = models.BooleanField(default=True, verbose_name="New Assignments")
    assignment_modification_notification = models.BooleanField(default=True, verbose_name="Assignment Modifications")
    assignment_completion_notification = models.BooleanField(default=True, verbose_name="Assignment Completions")
    
    # System alerts
    system_alerts = models.BooleanField(default=True, verbose_name="System Alerts")
    performance_alerts = models.BooleanField(default=True, verbose_name="Performance Alerts")
    
    # Notification channels
    web_notifications = models.BooleanField(default=True, verbose_name="Web Notifications")
    email_notifications = models.BooleanField(default=False, verbose_name="Email Notifications")
    
    # Do Not Disturb
    dnd_enabled = models.BooleanField(default=False, verbose_name="Do Not Disturb")
    dnd_start_time = models.TimeField(null=True, blank=True, verbose_name="DND Start Time")
    dnd_end_time = models.TimeField(null=True, blank=True, verbose_name="DND End Time")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.user.full_name} - Notification Preferences"
    
    def is_dnd_active(self):
        """Check if Do Not Disturb is currently active"""
        if not self.dnd_enabled or not self.dnd_start_time or not self.dnd_end_time:
            return False
        
        now = timezone.now().time()
        
        # Handle DND spanning midnight
        if self.dnd_start_time <= self.dnd_end_time:
            return self.dnd_start_time <= now <= self.dnd_end_time
        else:
            return now >= self.dnd_start_time or now <= self.dnd_end_time
    
    @property
    def notification_count(self):
        """Get count of enabled notification types"""
        count = 0
        fields = [
            'task_end_reminder', 'upcoming_task_alert', 'task_missed_alerts',
            'new_assignment_notification', 'assignment_modification_notification',
            'assignment_completion_notification', 'system_alerts', 'performance_alerts'
        ]
        
        for field in fields:
            if getattr(self, field, False):
                count += 1
        
        return count