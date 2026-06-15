# taskAssignmentApp/status_service.py

from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from .models import TaskAssignment
from .utils import get_assignment_status_values, get_assignment_status_dict
from activityApp.models import Activity
import logging

logger = logging.getLogger(__name__)


class TaskAssignmentStatusService:
    """
    Service class for handling task assignment status updates with role-based permissions
    """
    
    # Get status values dynamically from the model
    STATUS_VALUES = get_assignment_status_values()
    STATUS_DICT = get_assignment_status_dict()
    
    # Define status constants for easy reference
    SCHEDULED = 'scheduled'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    MISSED = 'missed'
    REASSIGNED = 'reassigned'
    CANCELLED = 'cancelled'
    
    # Define allowed status transitions for each role
    ALLOWED_TRANSITIONS = {
        'employee': {
            SCHEDULED: [ACTIVE],
            ACTIVE: [COMPLETED],
            # Employees cannot update any other status
        },
        'manager': {
            SCHEDULED: [COMPLETED, REASSIGNED, CANCELLED],
            ACTIVE: [COMPLETED, REASSIGNED, CANCELLED],
            MISSED: [REASSIGNED, CANCELLED],
            REASSIGNED: [],  # Terminal state
            COMPLETED: [],   # Terminal state
            CANCELLED: [],   # Terminal state
        },
        'admin': {
            SCHEDULED: [ACTIVE, COMPLETED, REASSIGNED, CANCELLED],
            ACTIVE: [COMPLETED, REASSIGNED, CANCELLED],
            MISSED: [REASSIGNED, CANCELLED, COMPLETED],
            REASSIGNED: [],  # Terminal state
            COMPLETED: [],   # Terminal state
            CANCELLED: [],   # Terminal state
        },
        'analyst': {
            # Analysts typically have view-only permissions
            SCHEDULED: [],
            ACTIVE: [],
            MISSED: [],
            REASSIGNED: [],
            COMPLETED: [],
            CANCELLED: [],
        }
    }
    
    # Terminal states that cannot be updated
    TERMINAL_STATES = [COMPLETED, CANCELLED, REASSIGNED]
    
    @classmethod
    def can_update_status(cls, user, assignment, new_status):
        """
        Check if a user can update an assignment to a new status
        """
        # Check if assignment is in terminal state
        if assignment.status in cls.TERMINAL_STATES:
            return False, f"Cannot update {assignment.status} assignments"
        
        # Check if user is the assignee for employee role
        if user.role == 'employee' and assignment.user_id != user.id:
            return False, "You can only update your own assignments"
        
        # Get allowed transitions for user's role
        role = user.role
        allowed_transitions = cls.ALLOWED_TRANSITIONS.get(role, {})
        
        # Check if current status allows transition to new status
        if assignment.status not in allowed_transitions:
            return False, f"Current status '{assignment.status}' cannot be updated by {role}s"
        
        if new_status not in allowed_transitions[assignment.status]:
            return False, f"Cannot change status from '{assignment.status}' to '{new_status}'"
        
        # Additional validation for specific transitions
        if new_status == cls.ACTIVE:
            # Check if assignment can be started (time window check)
            now = timezone.now()
            if not (assignment.start_time <= now <= assignment.end_time):
                return False, "Assignment can only be started during its scheduled time window"
        
        if new_status == cls.COMPLETED:
            # Can complete from either active or scheduled (admin/manager)
            if assignment.status == cls.SCHEDULED:
                # Admin/manager completing a scheduled task (mark as done early)
                pass
            elif assignment.status == cls.ACTIVE:
                # Normal completion flow
                pass
            elif assignment.status == cls.MISSED:
                # Admin completing a missed task
                pass
        
        return True, "Allowed"
    
    @classmethod
    @transaction.atomic
    def update_status(cls, assignment, new_status, user, reason=None):
        """
        Update assignment status with proper validation and logging
        """
        # Check permission
        allowed, message = cls.can_update_status(user, assignment, new_status)
        if not allowed:
            raise PermissionDenied(message)
        
        old_status = assignment.status
        old_actual_times = {
            'actual_start_time': assignment.actual_start_time,
            'actual_end_time': assignment.actual_end_time
        }
        
        # Handle special cases
        now = timezone.now()
        
        if new_status == cls.ACTIVE:
            assignment.actual_start_time = now
            # Don't set actual_end_time yet
            
        elif new_status == cls.COMPLETED:
            assignment.actual_end_time = now
            # If starting and completing at the same time (admin override)
            if not assignment.actual_start_time:
                assignment.actual_start_time = now
                
        elif new_status == cls.REASSIGNED:
            # Mark as reassigned - will be handled by reassignment logic elsewhere
            pass
            
        elif new_status == cls.CANCELLED:
            # Just mark as cancelled
            pass
        
        # Update status
        assignment.status = new_status
        assignment.is_modified = True
        assignment.modification_reason = reason or f"Status updated from {old_status} to {new_status}"
        assignment.modified_by = user
        assignment.save()
        
        # Log the activity using the correct activity type
        try:
            # Determine the specific activity type based on the status change
            if new_status == cls.ACTIVE:
                activity_type = 'task_assignment_start'
            elif new_status == cls.COMPLETED:
                activity_type = 'task_assignment_complete'
            elif new_status == cls.MISSED:
                activity_type = 'task_assignment_missed'
            elif new_status == cls.REASSIGNED:
                activity_type = 'task_assignment_reassign'
            else:
                # For any other status changes (including cancelled)
                activity_type = 'task_assignment_status_change'
            
            Activity.log_activity(
                activity_type=activity_type,
                user=user,
                status_code='200',
                description=f'Task assignment status updated from {old_status} to {new_status}',
                related_user_id=assignment.user_id,
                related_task_id=assignment.task_id,
                related_assignment_id=assignment.id,
                related_department_id=assignment.department_id,
                request_data={
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason
                },
                response_data={
                    'assignment_id': assignment.id,
                    'task_name': assignment.task.name,
                    'user_name': assignment.user.full_name
                }
            )
            logger.info(f"Activity logged successfully for assignment {assignment.id}")
        except Exception as e:
            logger.error(f"Failed to log status update activity: {str(e)}")
        
        return assignment
    
    @classmethod
    def check_for_missed_assignments(cls):
        """
        Systematic check for overdue assignments and mark them as missed
        This should be run periodically (e.g., via cron job or Celery task)
        """
        now = timezone.now()
        
        # Find assignments that are scheduled but past their end time
        overdue_assignments = TaskAssignment.objects.filter(
            status=cls.SCHEDULED,
            end_time__lt=now
        )
        
        count = 0
        for assignment in overdue_assignments:
            try:
                # Mark as missed (system action, no user)
                assignment.status = cls.MISSED
                assignment.is_modified = True
                assignment.modification_reason = "Automatically marked as missed - overdue"
                assignment.save(update_fields=['status', 'is_modified', 'modification_reason', 'updated_at'])
                
                # Log system activity
                try:
                    Activity.log_activity(
                        activity_type='task_assignment_missed',
                        user=None,  # System action
                        status_code='200',
                        description=f'Task "{assignment.task.name}" automatically marked as missed - overdue',
                        related_user_id=assignment.user_id,
                        related_task_id=assignment.task_id,
                        related_assignment_id=assignment.id,
                        related_department_id=assignment.department_id,
                        request_data={
                            'scheduled_end_time': assignment.end_time.isoformat(),
                            'detected_at': now.isoformat()
                        }
                    )
                    logger.info(f"Missed activity logged for assignment {assignment.id}")
                except Exception as e:
                    logger.error(f"Failed to log missed assignment activity: {str(e)}")
                
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to mark assignment {assignment.id} as missed: {str(e)}")
        
        return count