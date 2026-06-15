# notificationApp/services.py - Simplified version

from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import Notification, NotificationPreference
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and managing notifications"""
    
    @staticmethod
    def get_or_create_preferences(user):
        """Get or create notification preferences for a user"""
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        return prefs
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {count} notifications as read for {user.full_name}")
        return count
    
    @staticmethod
    def delete_expired_notifications():
        """Delete expired notifications"""
        count = Notification.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        logger.info(f"Deleted {count} expired notifications")
        return count
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user"""
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).count()
    
    @staticmethod
    def create_task_assignment_notification(assignment):
        """Create notification for new task assignment"""
        user = assignment.user
        prefs = NotificationService.get_or_create_preferences(user)
        
        if not prefs.new_assignment_notification or not prefs.web_notifications:
            return None
        
        title = f"New Task Assigned: {assignment.task.name}"
        message = (
            f"You have been assigned a new task:\n"
            f"• Task: {assignment.task.name}\n"
            f"• Date: {assignment.assignment_date}\n"
            f"• Time: {assignment.start_time.strftime('%H:%M')} - {assignment.end_time.strftime('%H:%M')}\n"
            f"• Priority: {assignment.get_priority_display()}\n"
            f"• Department: {assignment.department.name}"
        )
        
        notification = Notification.objects.create(
            user=user,
            notification_type='task_assignment_create',
            title=title,
            message=message,
            priority=assignment.priority,
            expires_at=assignment.end_time + timedelta(hours=24),
            metadata={
                'assignment_id': assignment.id,
                'task_id': assignment.task.id,
                'task_name': assignment.task.name,
                'department_id': assignment.department.id,
                'department_name': assignment.department.name,
                'assigned_by': assignment.assigned_by.full_name if assignment.assigned_by else 'System',
                'assignment_date': str(assignment.assignment_date),
                'start_time': assignment.start_time.isoformat(),
                'end_time': assignment.end_time.isoformat(),
                'priority': assignment.priority
            }
        )
        
        notification.mark_as_sent()
        logger.info(f"Created task assignment notification for {user.full_name}")
        return notification