# taskAssignmentApp/models.py - Updated to support multi-day tasks

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TaskAssignment(models.Model):
    """Individual task assignment for an employee"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('reassigned', 'Reassigned'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.CASCADE,
        related_name='task_assignments'
    )
    
    task = models.ForeignKey(
        'taskApp.Task',
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    department = models.ForeignKey(
        'departmentApp.Department',
        on_delete=models.CASCADE,
        related_name='task_assignments'
    )
    
    # Timing
    assignment_date = models.DateField(
        help_text="Date when the assignment was created/scheduled"
    )
    start_time = models.DateTimeField(
        help_text="When employee should start this task (can be future date)"
    )
    end_time = models.DateTimeField(
        help_text="When employee should finish this task (can be future date)"
    )
    
    # Actual timing
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    sequence_order = models.IntegerField(
        default=1,
        help_text="Order of tasks for the day (only relevant if start/end on same day)"
    )
    
    is_modified = models.BooleanField(
        default=False,
        help_text="True if assignment was manually modified"
    )
    
    modification_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for manual modification"
    )
    
    # Metadata
    assigned_by = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_created'
    )
    
    modified_by = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_modified'
    )
    
    notes = models.TextField(blank=True, null=True)

    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Store tracking data like sent reminders"
    )
    
    # Notification tracking
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time', 'sequence_order']
        verbose_name = 'Task Assignment'
        verbose_name_plural = 'Task Assignments'
        indexes = [
            models.Index(fields=['user', 'assignment_date', 'status']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['department', 'assignment_date']),
            models.Index(fields=['user', 'status']),
        ]
        # Remove unique_together constraint for multi-day tasks
        # unique_together = ['user', 'assignment_date', 'sequence_order']
    
    def __str__(self):
        duration_days = (self.end_time.date() - self.start_time.date()).days
        if duration_days > 0:
            date_range = f"{self.start_time.strftime('%Y-%m-%d')} to {self.end_time.strftime('%Y-%m-%d')}"
        else:
            date_range = self.assignment_date.strftime('%Y-%m-%d')
        
        return f"{self.user.full_name} - {self.task.name} - {date_range} ({self.status})"
    
    def clean(self):
        """Validate assignment times"""
        super().clean()
        
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })
            
            # Don't require dates to match - tasks can span multiple days
            # Only validate that assignment_date is provided
            if not self.assignment_date:
                raise ValidationError({
                    'assignment_date': 'Assignment date is required.'
                })
    
    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        
        # Auto-calculate assignment_date from start_time if not provided
        if not self.assignment_date and self.start_time:
            self.assignment_date = self.start_time.date()
        
        # Check if status is changing
        if self.pk:
            try:
                old_instance = TaskAssignment.objects.get(pk=self.pk)
                
                # If status is changing to 'missed', create notification and log activity
                if old_instance.status != 'missed' and self.status == 'missed':
                    from activityApp.models import Activity
                    
                    # Log activity
                    Activity.log_activity(
                        activity_type='task_assignment_missed',
                        user=self.assigned_by if self.assigned_by else None,
                        status_code='200',
                        description=f'Task "{self.task.name}" marked as missed for {self.user.full_name}',
                        related_user_id=self.user.id,
                        related_task_id=self.task.id,
                        related_assignment_id=self.id,
                        related_department_id=self.department_id,
                        request_data={
                            'old_status': old_instance.status,
                            'new_status': self.status,
                            'reason': self.modification_reason
                        }
                    )
                    
                    # Create missed task notification
                    try:
                        from notificationApp.services import NotificationService
                        NotificationService.create_task_missed_alert(self)
                    except Exception as e:
                        logger.error(f"Error creating missed task notification: {str(e)}")
                        
                # If status is changing to 'cancelled' or 'reassigned', log activity
                elif old_instance.status != self.status and self.status in ['cancelled', 'reassigned']:
                    from activityApp.models import Activity
                    Activity.log_activity(
                        activity_type='task_assignment_status_change',
                        user=self.modified_by if self.modified_by else self.assigned_by,
                        status_code='200',
                        description=f'Task assignment status changed from {old_instance.status} to {self.status}',
                        related_user_id=self.user.id,
                        related_task_id=self.task.id,
                        related_assignment_id=self.id,
                        related_department_id=self.department_id,
                        request_data={
                            'old_status': old_instance.status,
                            'new_status': self.status,
                            'reason': self.modification_reason
                        }
                    )
                    
            except TaskAssignment.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Calculate scheduled duration in minutes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0
    
    @property
    def duration_days(self):
        """Calculate scheduled duration in days"""
        if self.start_time and self.end_time:
            return (self.end_time.date() - self.start_time.date()).days
        return 0
    
    @property
    def actual_duration_minutes(self):
        """Calculate actual duration in minutes"""
        if self.actual_start_time and self.actual_end_time:
            return (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        return None
    
    @property
    def is_current(self):
        """Check if this assignment is currently active"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status in ['scheduled', 'active']
    
    @property
    def can_start(self):
        """Check if assignment can be started"""
        now = timezone.now()
        return (
            self.status == 'scheduled' and
            self.start_time <= now <= self.end_time
        )
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        now = timezone.now()
        return self.status == 'scheduled' and self.end_time < now
    
    @property
    def time_until_start_minutes(self):
        """Calculate minutes until assignment starts"""
        now = timezone.now()
        if self.start_time > now:
            return (self.start_time - now).total_seconds() / 60
        return 0
    
    @property
    def time_until_end_minutes(self):
        """Calculate minutes until assignment ends"""
        now = timezone.now()
        if self.end_time > now:
            return (self.end_time - now).total_seconds() / 60
        return 0
    
    @property
    def time_until_end_days(self):
        """Calculate days until assignment ends"""
        now = timezone.now()
        if self.end_time > now:
            return (self.end_time - now).days
        return 0
    
    def start_assignment(self):
        """Mark assignment as active"""
        if not self.can_start:
            raise ValidationError("Assignment cannot be started at this time")
        
        self.status = 'active'
        self.actual_start_time = timezone.now()
        self.save()
        
        # Log activity using Activity model
        try:
            from activityApp.models import Activity
            Activity.log_activity(
                activity_type='task_assignment_start',
                user=self.user,
                status_code='200',
                description=f'Started task "{self.task.name}"',
                related_user_id=self.user.id,
                related_task_id=self.task.id,
                related_assignment_id=self.id,
                related_department_id=self.department_id,
                response_data={
                    'assignment_id': self.id,
                    'task_name': self.task.name,
                    'start_time': self.actual_start_time.isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log start assignment activity: {str(e)}")
        
        return True

    def complete_assignment(self):
        """Mark assignment as completed"""
        if self.status != 'active':
            raise ValidationError("Only active assignments can be completed")
        
        self.status = 'completed'
        self.actual_end_time = timezone.now()
        self.save()
        
        # Log activity using Activity model
        try:
            from activityApp.models import Activity
            Activity.log_activity(
                activity_type='task_assignment_complete',
                user=self.user,
                status_code='200',
                description=f'Completed task "{self.task.name}"',
                related_user_id=self.user.id,
                related_task_id=self.task.id,
                related_assignment_id=self.id,
                related_department_id=self.department_id,
                response_data={
                    'assignment_id': self.id,
                    'task_name': self.task.name,
                    'start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
                    'end_time': self.actual_end_time.isoformat(),
                    'duration_minutes': self.actual_duration_minutes
                }
            )
        except Exception as e:
            logger.error(f"Failed to log complete assignment activity: {str(e)}")
        
        return True

class TaskAssignmentTemplate(models.Model):
    """Template for recurring task assignments"""
    name = models.CharField(max_length=255)
    task = models.ForeignKey('taskApp.Task', on_delete=models.CASCADE)
    department = models.ForeignKey('departmentApp.Department', on_delete=models.CASCADE)
    
    # Time settings
    start_time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    priority = models.CharField(max_length=20, choices=TaskAssignment.PRIORITY_CHOICES, default='medium')
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_days = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Comma-separated days (0=Sunday, 1=Monday, etc.)"
    )
    
    # Assignment rules
    assign_to_all_department = models.BooleanField(
        default=False,
        help_text="Assign to all employees in department"
    )
    
    specific_users = models.ManyToManyField(
        'userApp.CustomUser',
        blank=True,
        help_text="Specific users to assign (if not all department)"
    )
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_templates_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task Assignment Template'
        verbose_name_plural = 'Task Assignment Templates'
        unique_together = ['department', 'task', 'start_time']
    
    def __str__(self):
        return f"{self.name} - {self.task.name}"


class TaskOverload(models.Model):
    """Track task overload situations requiring multiple employees"""
    task = models.ForeignKey(
        'taskApp.Task',
        on_delete=models.CASCADE,
        related_name='overloads'
    )
    
    department = models.ForeignKey(
        'departmentApp.Department',
        on_delete=models.CASCADE,
        related_name='task_overloads'
    )
    
    overload_date = models.DateField()
    additional_employees_needed = models.IntegerField(
        default=1,
        help_text="Additional employees needed beyond normal assignment"
    )
    
    time_slot_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Specific time slot start (optional)"
    )
    
    time_slot_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Specific time slot end (optional)"
    )
    
    reason = models.TextField(help_text="Reason for overload")
    
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overloads_created'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task Overload'
        verbose_name_plural = 'Task Overloads'
        ordering = ['-overload_date', '-created_at']
    
    def __str__(self):
        return f"{self.task.name} - {self.overload_date} (+{self.additional_employees_needed})"