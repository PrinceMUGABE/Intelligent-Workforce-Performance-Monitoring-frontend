# taskAssignmentApp/tasks.py - Updated without shift dependency

from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from .services import TaskAssignmentService, TaskNotificationService
from departmentApp.models import Department
from userApp.models import CustomUser
from .models import TaskAssignmentTemplate, TaskAssignment
import logging


logger = logging.getLogger(__name__)


@shared_task
def send_task_reminders():
    """
    Send reminders for upcoming task deadlines
    Runs every 2 minutes
    """
    try:
        logger.info("Starting task reminder check...")
        TaskNotificationService.send_task_reminders()
        logger.info("Task reminder check completed")
        return "Task reminders sent"
    except Exception as e:
        logger.error(f"Error sending task reminders: {str(e)}")
        raise


@shared_task
def check_missed_assignments():
    """Check and mark missed assignments - runs every 10 minutes"""
    try:
        logger.info("Starting missed assignments check...")
        count = TaskNotificationService.check_missed_assignments()
        logger.info(f"Marked {count} assignments as missed")
        return f"Marked {count} assignments as missed"
    except Exception as e:
        logger.error(f"Error checking missed assignments: {str(e)}")
        raise


@shared_task
def generate_daily_assignments():
    """
    Generate daily assignments based on templates
    Runs daily at 6:00 AM for the current day
    """
    try:
        today = timezone.now().date()
        
        # Get all active departments
        departments = Department.objects.filter(status='active')
        
        total_assignments = 0
        departments_processed = []
        
        for department in departments:
            # Check if assignments already exist for today
            existing = TaskAssignment.objects.filter(
                assignment_date=today,
                department=department
            ).exists()
            
            if not existing:
                # Create assignments for this department
                assignments = TaskAssignmentService.create_daily_assignments_for_department(
                    date=today,
                    department=department,
                    assigned_by=None  # System generated
                )
                
                total_assignments += len(assignments)
                departments_processed.append(department.name)
        
        if total_assignments > 0:
            logger.info(
                f"Generated {total_assignments} assignments for {len(departments_processed)} departments"
            )
            return f"Created {total_assignments} assignments for {len(departments_processed)} departments"
        else:
            return "No assignments needed at this time"
            
    except Exception as e:
        logger.error(f"Error generating daily assignments: {str(e)}")
        raise


@shared_task
def cleanup_old_assignments():
    """
    Clean up old completed assignments
    Runs weekly to remove assignments older than 30 days
    """
    try:
        cutoff_date = timezone.now().date() - timedelta(days=30)
        
        # Get completed assignments older than 30 days
        old_assignments = TaskAssignment.objects.filter(
            assignment_date__lt=cutoff_date,
            status='completed'
        )
        
        count = old_assignments.count()
        old_assignments.delete()
        
        logger.info(f"Cleaned up {count} old assignments")
        return f"Cleaned up {count} old assignments"
        
    except Exception as e:
        logger.error(f"Error cleaning up old assignments: {str(e)}")
        raise