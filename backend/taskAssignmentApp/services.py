# taskAssignmentApp/services.py - Add _log_to_terminal function at the top

import json
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta, time
from .models import TaskAssignment, TaskAssignmentTemplate, TaskOverload
from userApp.models import CustomUser
from taskApp.models import Task
from departmentApp.models import Department
import logging
from django.db import models

logger = logging.getLogger(__name__)


# ==================== HELPER FUNCTIONS ====================

def _log_to_terminal(message, data=None, level="INFO"):
    """Helper function to log messages to terminal with formatting"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"[{timestamp}] [{level}] {message}")
    if data is not None:
        print(f"\nDATA:")
        if isinstance(data, dict):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)
    print(f"{'='*80}\n")


class TaskAssignmentService:
    """Service for managing task assignments"""
    
    @staticmethod
    def create_single_assignment(user, task, assignment_date, start_time, end_time, 
                                 assigned_by=None, priority='medium', department=None):
        """Create a single task assignment"""
        try:
            # Use user's department if not specified
            if not department:
                department = user.department
            
            assignment = TaskAssignment.objects.create(
                user=user,
                task=task,
                department=department,
                assignment_date=assignment_date,
                start_time=start_time,
                end_time=end_time,
                priority=priority,
                assigned_by=assigned_by,
                status='scheduled'
            )
            
            # Log activity
            from activityApp.models import Activity
            Activity.log_activity(
                activity_type='task_assignment_create',
                user=assigned_by,
                description=f'Assigned task "{task.name}" to {user.full_name}',
                related_user_id=user.id,
                related_task_id=task.id,
                related_assignment_id=assignment.id,
                status_code='201'
            )
            
            # Send notification to user
            TaskAssignmentService._send_assignment_notification(assignment)
            
            logger.info(f"Created assignment: {user.full_name} - {task.name} - {assignment_date}")
            return assignment
            
        except Exception as e:
            logger.error(f"Error creating single assignment: {str(e)}")
            raise
    
    @staticmethod
    def create_daily_assignments_for_department(date, department, assigned_by=None):
        """
        Create task assignments for a department based on templates
        """
        try:
            # Get active templates for this department
            templates = TaskAssignmentTemplate.objects.filter(
                department=department,
                is_active=True
            )
            
            assignments_created = []
            
            for template in templates:
                # Check if template applies to this date
                if template.is_recurring:
                    if not TaskAssignmentService._should_apply_template(template, date):
                        continue
                
                # Get users to assign
                users = TaskAssignmentService._get_users_for_template(template, department)
                
                # Calculate end time based on duration
                start_datetime = timezone.make_aware(
                    datetime.combine(date, template.start_time)
                )
                end_datetime = start_datetime + timedelta(minutes=template.duration_minutes)
                
                # Create assignments for each user
                for user in users:
                    # Check if user already has an assignment at this time
                    existing = TaskAssignment.objects.filter(
                        user=user,
                        assignment_date=date,
                        start_time__lt=end_datetime,
                        end_time__gt=start_datetime,
                        status__in=['scheduled', 'active']
                    ).exists()
                    
                    if not existing:
                        assignment = TaskAssignment.objects.create(
                            user=user,
                            task=template.task,
                            department=department,
                            assignment_date=date,
                            start_time=start_datetime,
                            end_time=end_datetime,
                            priority=template.priority,
                            assigned_by=assigned_by,
                            status='scheduled'
                        )
                        assignments_created.append(assignment)
                        
                        # Send notification
                        TaskAssignmentService._send_assignment_notification(assignment)
            
            # Log bulk creation activity
            if assignments_created:
                from activityApp.models import Activity
                Activity.log_activity(
                    activity_type='task_assignment_bulk_create',
                    user=assigned_by,
                    description=f'Created {len(assignments_created)} assignments for department {department.name} on {date}',
                    related_department_id=department.id,
                    status_code='201',
                    response_data={'count': len(assignments_created), 'date': str(date)}
                )
            
            logger.info(f"Created {len(assignments_created)} assignments for department {department.name} on {date}")
            return assignments_created
            
        except Exception as e:
            logger.error(f"Error creating daily assignments: {str(e)}")
            raise
    
    @staticmethod
    def _should_apply_template(template, date):
        """Check if template should be applied on given date"""
        if not template.recurrence_days:
            return False
        
        # Get day of week (0=Monday, 6=Sunday in Python)
        day_of_week = date.weekday()  # Monday=0
        
        # Convert to string format used in template (0=Sunday, 1=Monday, etc.)
        days_list = [int(d.strip()) for d in template.recurrence_days.split(',')]
        
        # Adjust day_of_week: template uses 0=Sunday, so convert
        template_day = (day_of_week + 1) % 7
        
        return template_day in days_list
    
    @staticmethod
    def _get_users_for_template(template, department):
        """Get users to assign based on template rules"""
        if template.assign_to_all_department:
            return CustomUser.objects.filter(
                department=department,
                role='employee',
                is_active=True,
                status='approved'
            )
        else:
            return template.specific_users.filter(
                department=department,
                role='employee',
                is_active=True,
                status='approved'
            )
    
    @staticmethod
    def get_current_assignment(user):
        """Get the current active assignment for a user"""
        now = timezone.now()
        return TaskAssignment.objects.filter(
            user=user,
            start_time__lte=now,
            end_time__gte=now,
            status__in=['scheduled', 'active']
        ).first()
    
    @staticmethod
    def get_next_assignment(user):
        """Get the next scheduled assignment for a user"""
        now = timezone.now()
        return TaskAssignment.objects.filter(
            user=user,
            start_time__gt=now,
            status='scheduled'
        ).order_by('start_time').first()
    
    @staticmethod
    def modify_assignment(assignment_id, modified_by, new_task_id=None, 
                        new_start_time=None, new_end_time=None, new_notes=None, reason=None):
        """Modify an existing assignment"""
        try:
            assignment = TaskAssignment.objects.get(id=assignment_id)
            
            if not TaskAssignmentService._can_modify_assignment(modified_by, assignment.user):
                raise PermissionError("You don't have permission to modify this assignment")
            
            changes_made = []
            
            if new_task_id and new_task_id != assignment.task.id:
                old_task = assignment.task
                assignment.task = Task.objects.get(id=new_task_id)
                changes_made.append(f"Task changed from {old_task.name} to {assignment.task.name}")
            
            if new_start_time and new_start_time != assignment.start_time:
                changes_made.append(f"Start time changed from {assignment.start_time.strftime('%Y-%m-%d %H:%M')} to {new_start_time.strftime('%Y-%m-%d %H:%M')}")
                assignment.start_time = new_start_time
            
            if new_end_time and new_end_time != assignment.end_time:
                changes_made.append(f"End time changed from {assignment.end_time.strftime('%Y-%m-%d %H:%M')} to {new_end_time.strftime('%Y-%m-%d %H:%M')}")
                assignment.end_time = new_end_time
            
            if new_notes is not None and new_notes != assignment.notes:
                changes_made.append("Notes updated")
                assignment.notes = new_notes
            
            if changes_made:
                assignment.is_modified = True
                assignment.modified_by = modified_by
                assignment.modification_reason = reason or "; ".join(changes_made)
                assignment.save()
                
                from activityApp.models import Activity
                Activity.log_activity(
                    activity_type='task_assignment_modify',
                    user=modified_by,
                    description=f'Modified assignment for {assignment.user.full_name}: {", ".join(changes_made)}',
                    related_user_id=assignment.user.id,
                    related_task_id=assignment.task.id,
                    related_assignment_id=assignment.id,
                    status_code='200'
                )
                
                TaskAssignmentService._send_modification_notification(assignment, changes_made)
                logger.info(f"Assignment {assignment_id} modified by {modified_by.full_name}")
            
            return assignment
            
        except TaskAssignment.DoesNotExist:
            raise ValueError("Assignment not found")
        except Task.DoesNotExist:
            raise ValueError("Task not found")
    
    @staticmethod
    def _can_modify_assignment(user, assignment_user):
        """Check if user can modify assignment"""
        if user.is_admin or user.is_manager:
            return True
        if user.is_analyst:
            return user.department == assignment_user.department
        return False
    
    @staticmethod
    def _send_assignment_notification(assignment):
        """Send notification about new assignment"""
        try:
            from notificationApp.models import Notification
            
            message = (
                f"New Task Assignment:\n"
                f"Task: {assignment.task.name}\n"
                f"Date: {assignment.assignment_date}\n"
                f"Time: {assignment.start_time.strftime('%H:%M')} - {assignment.end_time.strftime('%H:%M')}\n"
                f"Priority: {assignment.get_priority_display()}"
            )
            
            Notification.objects.create(
                user=assignment.user,
                notification_type='task_assignment_create',
                title='New Task Assigned',
                message=message,
                priority=assignment.priority,
                action_url=f'/assignments/{assignment.id}/',
                action_text='View Assignment',
                metadata={
                    'assignment_id': assignment.id,
                    'task_name': assignment.task.name,
                    'assigned_by': assignment.assigned_by.full_name if assignment.assigned_by else 'System',
                    'due_date': str(assignment.assignment_date),
                    'start_time': assignment.start_time.isoformat(),
                    'end_time': assignment.end_time.isoformat()
                }
            ).mark_as_sent()
            
        except Exception as e:
            logger.error(f"Failed to send assignment notification: {str(e)}")
    
    @staticmethod
    def _send_modification_notification(assignment, changes):
        """Send notification about assignment modification"""
        try:
            from notificationApp.models import Notification
            
            message = f"Your task assignment has been modified:\n" + "\n".join(changes)
            
            Notification.objects.create(
                user=assignment.user,
                notification_type='task_assignment_update',
                title='Task Assignment Modified',
                message=message,
                priority='high',
                action_url=f'/assignments/{assignment.id}/',
                action_text='View Assignment',
                metadata={
                    'assignment_id': assignment.id,
                    'task_name': assignment.task.name,
                    'modified_by': assignment.modified_by.full_name if assignment.modified_by else 'System',
                    'modification_reason': assignment.modification_reason
                }
            ).mark_as_sent()
            
        except Exception as e:
            logger.error(f"Failed to send modification notification: {str(e)}")
    
    # ==================== BULK ASSIGNMENT METHODS ====================
    
    @staticmethod
    def create_bulk_assignments(task_id, start_time, end_time, assigned_by=None, 
                            priority='medium', assignment_date=None, notes=None, **kwargs):
        """
        Create assignments for multiple users based on different criteria
        
        Returns: dict with created assignments, failed assignments, and summary
        """
        try:
            # Get the task
            try:
                task = Task.objects.get(id=task_id)
            except Task.DoesNotExist:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # Set assignment_date if not provided
            if not assignment_date:
                assignment_date = start_time.date()
            
            # Determine target users based on kwargs
            target_users = TaskAssignmentService._get_target_users(**kwargs)
            
            if not target_users:
                _log_to_terminal("CREATE_BULK_ASSIGNMENTS - No users found", 
                            {
                                'task_id': task_id,
                                'task_name': task.name,
                                'kwargs': {k: v for k, v in kwargs.items() if k not in ['exclude_user_ids']}
                            }, 
                            level="WARNING")
                return {
                    'success': False,
                    'task': task,
                    'created': [],
                    'created_count': 0,
                    'skipped': [],
                    'skipped_count': 0,
                    'failed': [],
                    'failed_count': 0,
                    'total_targeted': 0,
                    'message': 'No users found to assign the task to'
                }
            
            created_assignments = []
            failed_assignments = []
            skipped_assignments = []
            
            for user in target_users:
                try:
                    # ============== VALIDATE USER ELIGIBILITY ==============
                    # Skip users without department (admins, managers, analysts without department)
                    if not user.department:
                        skipped_assignments.append({
                            'user_id': user.id,
                            'user_name': user.full_name,
                            'reason': f'User has no department assigned (role: {user.role})',
                            'user_role': user.role
                        })
                        continue
                    
                    # Only create assignments for employees (or allow all users with departments?)
                    # For now, we'll only assign tasks to employees
                    if user.role != 'employee':
                        skipped_assignments.append({
                            'user_id': user.id,
                            'user_name': user.full_name,
                            'reason': f'User is not an employee (role: {user.role})',
                            'user_role': user.role
                        })
                        continue
                    
                    # Check if user is active and approved
                    if not user.is_active or user.status != 'approved':
                        skipped_assignments.append({
                            'user_id': user.id,
                            'user_name': user.full_name,
                            'reason': f'User is not active or not approved (is_active: {user.is_active}, status: {user.status})'
                        })
                        continue
                    
                    # ============== CHECK FOR CONFLICTING ASSIGNMENTS ==============
                    conflicting = TaskAssignment.objects.filter(
                        user=user,
                        status__in=['scheduled', 'active']
                    ).filter(
                        models.Q(start_time__lt=end_time, end_time__gt=start_time)
                    )
                    
                    if conflicting.exists():
                        conflict = conflicting.first()
                        skipped_assignments.append({
                            'user_id': user.id,
                            'user_name': user.full_name,
                            'reason': f'Time conflict with assignment: {conflict.task.name}',
                            'conflict_id': conflict.id,
                            'conflict_time': f'{conflict.start_time.strftime("%H:%M")} - {conflict.end_time.strftime("%H:%M")}'
                        })
                        continue
                    
                    # ============== GET SEQUENCE ORDER ==============
                    sequence_order = 1
                    if start_time.date() == end_time.date():
                        last_assignment = TaskAssignment.objects.filter(
                            user=user,
                            assignment_date=start_time.date()
                        ).order_by('-sequence_order').first()
                        sequence_order = (last_assignment.sequence_order + 1) if last_assignment else 1
                    
                    # ============== CREATE ASSIGNMENT ==============
                    assignment = TaskAssignment.objects.create(
                        user=user,
                        task=task,
                        department=user.department,  # Now guaranteed to exist
                        assignment_date=assignment_date,
                        start_time=start_time,
                        end_time=end_time,
                        priority=priority,
                        sequence_order=sequence_order,
                        assigned_by=assigned_by,
                        notes=notes or '',
                        status='scheduled'
                    )
                    
                    created_assignments.append(assignment)
                    TaskAssignmentService._send_assignment_notification(assignment)
                    
                except Exception as e:
                    failed_assignments.append({
                        'user_id': user.id,
                        'user_name': user.full_name,
                        'error': str(e),
                        'user_role': user.role,
                        'has_department': user.department is not None
                    })
                    logger.error(f"Failed to create assignment for user {user.id} ({user.full_name}): {str(e)}")
            
            # Log bulk creation activity
            if created_assignments:
                try:
                    from activityApp.models import Activity
                    Activity.log_activity(
                        activity_type='task_assignment_bulk_create',
                        user=assigned_by,
                        description=f'Created {len(created_assignments)} assignments for task "{task.name}"',
                        related_task_id=task.id,
                        status_code='201',
                        response_data={
                            'total_created': len(created_assignments),
                            'total_skipped': len(skipped_assignments),
                            'total_failed': len(failed_assignments)
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to log bulk creation activity: {str(e)}")
            
            return {
                'success': True,
                'task': task,
                'created': created_assignments,
                'created_count': len(created_assignments),
                'skipped': skipped_assignments,
                'skipped_count': len(skipped_assignments),
                'failed': failed_assignments,
                'failed_count': len(failed_assignments),
                'total_targeted': len(target_users)
            }
            
        except Exception as e:
            logger.error(f"Error in bulk assignment: {str(e)}")
            raise
    
    @staticmethod
    def _get_target_users(department_id=None, user_ids=None, 
                        assign_to_all_employees=False, assign_to_all_users=False,
                        exclude_user_ids=None, **kwargs):
        """Get target users based on assignment criteria"""
        
        users = CustomUser.objects.none()
        
        if assign_to_all_users:
            # For all users, we still need to filter appropriately
            # We'll filter later in create_bulk_assignments
            users = CustomUser.objects.filter(is_active=True)
            _log_to_terminal("_GET_TARGET_USERS - All users", 
                        {'count': users.count(), 'users': list(users.values_list('id', 'full_name', 'role'))[:5]}, 
                        level="DEBUG")
            
        elif assign_to_all_employees:
            # All active employees - these should have departments
            users = CustomUser.objects.filter(
                role='employee',
                is_active=True,
                status='approved'
            ).exclude(department__isnull=True)  # Only employees with departments
            _log_to_terminal("_GET_TARGET_USERS - All employees", 
                        {'count': users.count()}, 
                        level="DEBUG")
            
        elif department_id:
            # All employees in specific department
            try:
                department = Department.objects.get(id=department_id)
                users = CustomUser.objects.filter(
                    department=department,
                    role='employee',
                    is_active=True,
                    status='approved'
                )
                _log_to_terminal("_GET_TARGET_USERS - Department employees", 
                            {'department_id': department_id, 'department_name': department.name, 'count': users.count()}, 
                            level="DEBUG")
            except Department.DoesNotExist:
                raise ValueError(f"Department with ID {department_id} not found")
                
        elif user_ids:
            # Specific users - filter out non-employees and those without departments
            users = CustomUser.objects.filter(
                id__in=user_ids,
                is_active=True,
                role='employee',  # Only employees
                status='approved'
            ).exclude(department__isnull=True)  # Only those with departments
            _log_to_terminal("_GET_TARGET_USERS - Specific users", 
                        {'requested_ids': user_ids, 'found_count': users.count()}, 
                        level="DEBUG")
        
        # Apply exclusions if specified
        if exclude_user_ids and users.exists():
            exclude_count = users.filter(id__in=exclude_user_ids).count()
            users = users.exclude(id__in=exclude_user_ids)
            _log_to_terminal("_GET_TARGET_USERS - After exclusions", 
                        {'excluded_count': exclude_count, 'remaining_count': users.count()}, 
                        level="DEBUG")
        
        return users.distinct()

    
    @staticmethod
    def create_all_employees_assignments(task_id, start_time, end_time, assigned_by=None,
                                        priority='medium', assignment_date=None, notes=None):
        """
        Assign task to all active employees (with departments)
        """
        return TaskAssignmentService.create_bulk_assignments(
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            assigned_by=assigned_by,
            priority=priority,
            assignment_date=assignment_date,
            notes=notes,
            assign_to_all_employees=True
        )

    @staticmethod
    def create_all_users_assignments(task_id, start_time, end_time, assigned_by=None,
                                            priority='medium', assignment_date=None, notes=None):
                """
                Assign task to all active users (but only employees with departments will get assignments)
                """
                # This will still only create assignments for employees with departments
                return TaskAssignmentService.create_bulk_assignments(
                    task_id=task_id,
                    start_time=start_time,
                    end_time=end_time,
                    assigned_by=assigned_by,
                    priority=priority,
                    assignment_date=assignment_date,
                    notes=notes,
                    assign_to_all_users=True
                )
            
        
    @staticmethod
    def create_department_assignments(task_id, department_id, start_time, end_time,
                                    assigned_by=None, priority='medium', 
                                    assignment_date=None, notes=None, exclude_user_ids=None):
        """
        Assign a task to all employees in a specific department
        """
        # Verify department exists and is active
        try:
            department = Department.objects.get(id=department_id)
            if department.status != 'active':
                raise ValueError(f"Department '{department.name}' is not active")
        except Department.DoesNotExist:
            raise ValueError(f"Department with ID {department_id} not found")
        
        return TaskAssignmentService.create_bulk_assignments(
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            assigned_by=assigned_by,
            priority=priority,
            assignment_date=assignment_date,
            notes=notes,
            department_id=department_id,
            exclude_user_ids=exclude_user_ids
        )
        
    @staticmethod
    def create_role_based_assignments(task_id, role, start_time, end_time,
                                    assigned_by=None, priority='medium',
                                    assignment_date=None, notes=None, exclude_user_ids=None):
        """
        Assign a task to all users with a specific role (admin, manager, analyst, employee)
        Only users with departments will get assignments
        """
        users = CustomUser.objects.filter(
            role=role,
            is_active=True,
            status='approved' if role == 'employee' else None
        ).exclude(department__isnull=True)
        
        if exclude_user_ids:
            users = users.exclude(id__in=exclude_user_ids)
        
        _log_to_terminal(f"CREATE_ROLE_BASED_ASSIGNMENTS - {role} users", 
                        {'count': users.count()}, 
                        level="INFO")
        
        return TaskAssignmentService.create_bulk_assignments(
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            assigned_by=assigned_by,
            priority=priority,
            assignment_date=assignment_date,
            notes=notes,
            user_ids=list(users.values_list('id', flat=True))
        )
    
    
    @staticmethod
    def create_user_list_assignments(task_id, user_ids, start_time, end_time,
                                    assigned_by=None, priority='medium',
                                    assignment_date=None, notes=None):
        """
        Convenience method for assigning a task to a specific list of users
        """
        return TaskAssignmentService.create_bulk_assignments(
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            assigned_by=assigned_by,
            priority=priority,
            assignment_date=assignment_date,
            notes=notes,
            user_ids=user_ids
        )


class TaskNotificationService:
    """Service for sending task-related notifications"""
    
    REMINDER_MINUTES = [30, 15, 10, 5]
    
    @staticmethod
    def send_task_reminders():
        """
        Send reminders at 30, 15, 10, and 5 minutes before activity ends
        """
        now = timezone.now()
        
        for minutes in TaskNotificationService.REMINDER_MINUTES:
            reminder_time = now + timedelta(minutes=minutes)
            window_start = reminder_time - timedelta(minutes=1)
            window_end = reminder_time + timedelta(minutes=1)
            
            upcoming_assignments = TaskAssignment.objects.filter(
                status='active',
                end_time__gte=window_start,
                end_time__lte=window_end
            ).select_related('user', 'task')
            
            for assignment in upcoming_assignments:
                reminder_key = f"{assignment.id}_{minutes}min"
                
                if not assignment.metadata:
                    assignment.metadata = {}
                
                sent_reminders = assignment.metadata.get('sent_reminders', [])
                
                if reminder_key not in sent_reminders:
                    TaskNotificationService._send_task_reminder(
                        assignment=assignment,
                        minutes_remaining=minutes
                    )
                    sent_reminders.append(reminder_key)
                    assignment.metadata['sent_reminders'] = sent_reminders
                    assignment.save(update_fields=['metadata'])
    
    @staticmethod
    def _send_task_reminder(assignment, minutes_remaining):
        """Send task reminder notification"""
        try:
            from notificationApp.models import Notification
            
            message = f"⏰ {minutes_remaining} minutes remaining on {assignment.task.name}."
            
            if minutes_remaining <= 5:
                priority = 'high'
            elif minutes_remaining <= 10:
                priority = 'medium'
            else:
                priority = 'low'
            
            Notification.objects.create(
                user=assignment.user,
                notification_type='task_end_reminder',
                title=f'{minutes_remaining} Minutes Remaining',
                message=message,
                priority=priority,
                action_url='/assignments/current/',
                action_text='View Schedule',
                metadata={
                    'current_task': assignment.task.name,
                    'minutes_remaining': minutes_remaining,
                    'end_time': assignment.end_time.isoformat()
                }
            ).mark_as_sent()
            
            logger.info(
                f"Sent {minutes_remaining}-minute reminder to {assignment.user.full_name} "
                f"for task {assignment.task.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send task reminder: {str(e)}")
    
    @staticmethod
    def check_missed_assignments():
        """Mark assignments as missed if not started on time"""
        now = timezone.now()
        
        missed_assignments = TaskAssignment.objects.filter(
            status='scheduled',
            end_time__lt=now - timedelta(minutes=5)
        )
        
        count = 0
        for assignment in missed_assignments:
            assignment.status = 'missed'
            assignment.save()
            
            from activityApp.models import Activity
            Activity.log_activity(
                activity_type='task_assignment_missed',
                user=assignment.user,
                description=f'Task "{assignment.task.name}" marked as missed',
                related_task_id=assignment.task.id,
                related_assignment_id=assignment.id,
                status_code='200'
            )
            count += 1
        
        if count > 0:
            logger.info(f"Marked {count} assignments as missed")
        
        return count