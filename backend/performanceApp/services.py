# performanceApp/services.py
from django.db.models import FloatField
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta, datetime
from collections import defaultdict

from userApp.models import CustomUser
from taskAssignmentApp.models import TaskAssignment
from activityApp.models import Activity, ActivitySummary
from departmentApp.models import Department
import logging

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Service class for calculating role-based performance metrics"""
    
    # Activity type categories for grouping
    ACTIVITY_CATEGORIES = {
        'authentication': [
            'user_login', 'user_logout', 'user_registration', 
            'password_reset_request', 'password_reset_complete',
            'password_change', 'otp_request', 'otp_verification'
        ],
        'user_management': [
            'user_create', 'user_update', 'user_delete', 
            'user_activate', 'user_deactivate', 'user_status_change',
            'profile_update', 'user_view', 'users_list'
        ],
        'user_day_off': [
            'user_day_off_set', 'user_day_off_update', 'user_day_off_clear',
            'user_day_off_view', 'user_day_off_list', 'user_day_off_stats_view',
            'user_day_off_bulk_update'
        ],
        'department': [
            'department_create', 'department_update', 'department_delete',
            'department_view', 'departments_list', 'department_employees_view'
        ],
        'task': [
            'task_create', 'task_update', 'task_delete', 'task_view',
            'tasks_list', 'task_view_by_name', 'task_status_change'
        ],
        'task_assignment': [
            'task_assignment_create', 'task_assignment_update', 'task_assignment_delete',
            'task_assignment_view', 'task_assignments_list', 'task_assignment_start',
            'task_assignment_complete', 'task_assignment_missed', 'task_assignment_reassign',
            'task_assignment_modify', 'task_assignment_priority_change',
            'task_assignment_status_update', 'task_assignment_bulk_create',
            'task_assignment_bulk_delete', 'task_assignment_bulk_update',
            'task_assignment_missed_check', 'task_assignment_status_transitions_view'
        ],
        'task_assignment_status': [
            'task_assignment_status_scheduled_to_active',
            'task_assignment_status_scheduled_to_completed',
            'task_assignment_status_scheduled_to_reassigned',
            'task_assignment_status_scheduled_to_cancelled',
            'task_assignment_status_active_to_completed',
            'task_assignment_status_active_to_reassigned',
            'task_assignment_status_active_to_cancelled',
            'task_assignment_status_missed_to_reassigned',
            'task_assignment_status_missed_to_cancelled'
        ],
        'dayoff_request': [
            'dayoff_request_create', 'dayoff_request_create_own', 'dayoff_request_create_for_user',
            'dayoff_request_bulk_create', 'dayoff_request_view', 'dayoff_request_view_own',
            'dayoff_request_view_for_user', 'dayoff_requests_list', 'dayoff_requests_list_all',
            'dayoff_requests_list_pending', 'dayoff_requests_list_approved',
            'dayoff_requests_list_rejected', 'dayoff_request_update', 'dayoff_request_update_own',
            'dayoff_request_update_for_user', 'dayoff_request_approve', 'dayoff_request_reject',
            'dayoff_request_cancel', 'dayoff_request_reopen', 'dayoff_request_delete',
            'dayoff_request_delete_own', 'dayoff_request_delete_for_user', 'dayoff_request_bulk_delete',
            'dayoff_request_stats_view', 'dayoff_request_stats_by_user',
            'dayoff_request_stats_by_department', 'dayoff_request_stats_by_date_range',
            'dayoff_request_bulk_view'
        ],
        'dayoff_request_status': [
            'dayoff_request_status_change', 'dayoff_request_pending_to_approved',
            'dayoff_request_pending_to_rejected', 'dayoff_request_approved_to_cancelled',
            'dayoff_request_rejected_to_pending', 'dayoff_request_cancelled_to_pending'
        ],
        'notification': [
            'notification_sent', 'notification_viewed', 'notification_cleared'
        ],
        'contact': [
            'contact_submission'
        ],
        'performance': [
            'performance_view_own', 'performance_view_user', 'performance_view_all',
            'performance_view_department', 'performance_view_departments',
            'performance_view_organization'
        ],
        'api': [
            'api_request', 'api_error'
        ]
    }
    
    # Activity weightage based on importance and complexity
    ACTIVITY_WEIGHTS = {
        # Authentication (low weight - routine)
        'user_login': 1,
        'user_logout': 1,
        'user_registration': 5,
        'password_reset_request': 3,
        'password_reset_complete': 3,
        'password_change': 3,
        'otp_request': 2,
        'otp_verification': 2,
        
        # User Management (medium-high weight)
        'user_create': 10,
        'user_update': 8,
        'user_delete': 15,
        'user_activate': 7,
        'user_deactivate': 7,
        'user_status_change': 7,
        'profile_update': 5,
        'user_view': 2,
        'users_list': 3,
        
        # User Day-Off (medium weight)
        'user_day_off_set': 6,
        'user_day_off_update': 5,
        'user_day_off_clear': 4,
        'user_day_off_view': 2,
        'user_day_off_list': 3,
        'user_day_off_stats_view': 4,
        'user_day_off_bulk_update': 10,
        
        # Department (medium weight)
        'department_create': 10,
        'department_update': 8,
        'department_delete': 12,
        'department_view': 2,
        'departments_list': 3,
        'department_employees_view': 4,
        
        # Task (high weight)
        'task_create': 8,
        'task_update': 6,
        'task_delete': 10,
        'task_view': 2,
        'tasks_list': 3,
        'task_view_by_name': 2,
        'task_status_change': 5,
        
        # Task Assignment (high weight)
        'task_assignment_create': 8,
        'task_assignment_update': 6,
        'task_assignment_delete': 10,
        'task_assignment_view': 2,
        'task_assignments_list': 3,
        'task_assignment_start': 5,
        'task_assignment_complete': 8,
        'task_assignment_missed': 2,  # Negative weight handled separately
        'task_assignment_reassign': 6,
        'task_assignment_modify': 5,
        'task_assignment_priority_change': 4,
        'task_assignment_bulk_create': 15,
        'task_assignment_bulk_delete': 15,
        'task_assignment_bulk_update': 12,
        'task_assignment_missed_check': 3,
        'task_assignment_status_transitions_view': 3,
        
        # Task Assignment Status (high weight - critical operations)
        'task_assignment_status_scheduled_to_active': 7,
        'task_assignment_status_scheduled_to_completed': 9,
        'task_assignment_status_scheduled_to_reassigned': 6,
        'task_assignment_status_scheduled_to_cancelled': 5,
        'task_assignment_status_active_to_completed': 10,
        'task_assignment_status_active_to_reassigned': 7,
        'task_assignment_status_active_to_cancelled': 6,
        'task_assignment_status_missed_to_reassigned': 8,
        'task_assignment_status_missed_to_cancelled': 5,
        
        # Day-Off Request (medium weight)
        'dayoff_request_create': 6,
        'dayoff_request_create_own': 5,
        'dayoff_request_create_for_user': 7,
        'dayoff_request_bulk_create': 12,
        'dayoff_request_view': 2,
        'dayoff_request_view_own': 2,
        'dayoff_request_view_for_user': 3,
        'dayoff_requests_list': 3,
        'dayoff_requests_list_all': 4,
        'dayoff_requests_list_pending': 4,
        'dayoff_requests_list_approved': 4,
        'dayoff_requests_list_rejected': 4,
        'dayoff_request_update': 5,
        'dayoff_request_update_own': 4,
        'dayoff_request_update_for_user': 6,
        'dayoff_request_approve': 8,
        'dayoff_request_reject': 8,
        'dayoff_request_cancel': 5,
        'dayoff_request_reopen': 6,
        'dayoff_request_delete': 7,
        'dayoff_request_delete_own': 6,
        'dayoff_request_delete_for_user': 8,
        'dayoff_request_bulk_delete': 12,
        'dayoff_request_stats_view': 4,
        'dayoff_request_stats_by_user': 4,
        'dayoff_request_stats_by_department': 5,
        'dayoff_request_stats_by_date_range': 5,
        'dayoff_request_bulk_view': 4,
        
        # Day-Off Request Status (medium weight)
        'dayoff_request_status_change': 5,
        'dayoff_request_pending_to_approved': 8,
        'dayoff_request_pending_to_rejected': 8,
        'dayoff_request_approved_to_cancelled': 6,
        'dayoff_request_rejected_to_pending': 6,
        'dayoff_request_cancelled_to_pending': 6,
        
        # Notification (low weight)
        'notification_sent': 1,
        'notification_viewed': 1,
        'notification_cleared': 1,
        
        # Contact (medium weight)
        'contact_submission': 5,
        
        # Performance (medium weight)
        'performance_view_own': 3,
        'performance_view_user': 4,
        'performance_view_all': 5,
        'performance_view_department': 4,
        'performance_view_departments': 5,
        'performance_view_organization': 6,
        
        # API (low weight)
        'api_request': 1,
        'api_error': 0,  # Negative weight handled separately
    }
    
    # Status weight multipliers
    STATUS_WEIGHTS = {
        # Success responses (2xx)
        '200': 1.0,  # OK - Standard success
        '201': 1.2,  # Created - Resource creation
        '202': 1.1,  # Accepted - Async operation
        '204': 1.0,  # No Content - Success but no data
        
        # Client errors (4xx) - Penalize based on severity
        '400': 0.3,  # Bad Request - User error
        '401': 0.1,  # Unauthorized - Not logged in
        '403': 0.2,  # Forbidden - Permission issue
        '404': 0.4,  # Not Found - Missing resource
        '409': 0.5,  # Conflict - Data conflict
        '422': 0.3,  # Unprocessable Entity - Validation error
        
        # Server errors (5xx) - Heavy penalty
        '500': 0.0,  # Internal Server Error - System error
        '502': 0.0,  # Bad Gateway - System error
        '503': 0.0,  # Service Unavailable - System error
    }
    
    # Critical activity types that should have higher impact
    CRITICAL_ACTIVITIES = [
        'user_create', 'user_delete', 'department_create', 'department_delete',
        'task_delete', 'task_assignment_delete', 'task_assignment_bulk_delete',
        'dayoff_request_approve', 'dayoff_request_reject', 'dayoff_request_delete',
        'password_change', 'user_status_change'
    ]
    
    @staticmethod
    def calculate_user_performance(user, start_date=None, end_date=None):
        """
        Calculate performance metrics based on user role:
        - Employees: Task completion + Activity logs
        - Admin/Manager/Analyst: Activity logs only (weighted by type and status)
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Base user data
        performance_data = {
            'user_id': user.id,
            'full_name': user.full_name,
            'work_mail_address': user.work_mail_address,
            'role': user.role,
            'department_id': user.department.id if user.department else None,
            'department_name': user.department.name if user.department else None,
            'period_start': start_date,
            'period_end': end_date
        }
        
        if user.role == 'employee':
            # Calculate task-based metrics for employees
            task_metrics = PerformanceCalculator._calculate_employee_task_metrics(
                user, start_date, end_date
            )
            performance_data.update(task_metrics)
            
            # Also include activity metrics for employees
            activity_metrics = PerformanceCalculator._calculate_activity_metrics(
                user, start_date, end_date
            )
            performance_data['activity_metrics'] = activity_metrics
        else:
            # Calculate comprehensive activity-based metrics for staff
            activity_metrics = PerformanceCalculator._calculate_activity_metrics(
                user, start_date, end_date
            )
            performance_data.update(activity_metrics)
        
        return performance_data
    
    @staticmethod
    def _calculate_activity_metrics(user, start_date, end_date):
        """
        Calculate comprehensive activity-based metrics considering:
        - Activity type weights
        - Status code success rates
        - Critical activity completion
        - Category breakdown
        """
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time())
        )
        
        activities = Activity.objects.filter(
            user=user,
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        total_activities = activities.count()
        if total_activities == 0:
            return PerformanceCalculator._get_empty_activity_metrics()
        
        # 1. Calculate weighted activity score
        weighted_score = 0
        total_weight_possible = 0
        
        # Track metrics by category
        category_metrics = defaultdict(lambda: {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'weighted_score': 0,
            'critical_count': 0,
            'critical_success': 0
        })
        
        # Track status code distribution
        status_distribution = defaultdict(int)
        
        # Track specific important metrics
        critical_activities_total = 0
        critical_activities_success = 0
        successful_activities = 0
        failed_activities = 0
        
        # Activity type breakdown
        activity_type_breakdown = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'weighted_score': 0
        })
        
        for activity in activities:
            activity_type = activity.activity_type
            status_code = activity.status_code
            is_success = activity.is_success()
            
            # Get weight for this activity type
            weight = PerformanceCalculator.ACTIVITY_WEIGHTS.get(activity_type, 1)
            total_weight_possible += weight
            
            # Get status multiplier
            status_multiplier = PerformanceCalculator.STATUS_WEIGHTS.get(
                status_code, 
                0.5 if is_success else 0.1  # Default values
            )
            
            # Calculate weighted contribution
            contribution = weight * status_multiplier
            weighted_score += contribution
            
            # Update success/failure counts
            if is_success:
                successful_activities += 1
            else:
                failed_activities += 1
            
            # Update status distribution
            status_distribution[status_code] += 1
            
            # Determine category
            category = PerformanceCalculator._get_activity_category(activity_type)
            
            # Update category metrics
            category_metrics[category]['total'] += 1
            category_metrics[category]['weighted_score'] += contribution
            if is_success:
                category_metrics[category]['successful'] += 1
            else:
                category_metrics[category]['failed'] += 1
            
            # Track critical activities
            if activity_type in PerformanceCalculator.CRITICAL_ACTIVITIES:
                critical_activities_total += 1
                category_metrics[category]['critical_count'] += 1
                if is_success:
                    critical_activities_success += 1
                    category_metrics[category]['critical_success'] += 1
            
            # Update activity type breakdown
            activity_type_breakdown[activity_type]['count'] += 1
            if is_success:
                activity_type_breakdown[activity_type]['success_count'] += 1
            activity_type_breakdown[activity_type]['weighted_score'] += contribution
        
        # Calculate normalized activity score (0-100)
        activity_score = 0
        if total_weight_possible > 0:
            activity_score = (weighted_score / total_weight_possible) * 100
        
        # Calculate success rate
        success_rate = (successful_activities / total_activities * 100) if total_activities > 0 else 0
        
        # Calculate critical activity success rate
        critical_success_rate = 0
        if critical_activities_total > 0:
            critical_success_rate = (critical_activities_success / critical_activities_total * 100)
        
        # Calculate category scores
        category_scores = {}
        for category, metrics in category_metrics.items():
            if metrics['total'] > 0:
                category_scores[category] = {
                    'total': metrics['total'],
                    'successful': metrics['successful'],
                    'failed': metrics['failed'],
                    'success_rate': (metrics['successful'] / metrics['total'] * 100),
                    'weighted_score': metrics['weighted_score'],
                    'critical_count': metrics['critical_count'],
                    'critical_success_rate': (metrics['critical_success'] / metrics['critical_count'] * 100) if metrics['critical_count'] > 0 else 0
                }
        
        # Calculate daily activity average
        days_diff = (end_date - start_date).days + 1
        daily_avg = total_activities / days_diff if days_diff > 0 else 0
        
        # Get activity timeline (last 30 days)
        timeline = PerformanceCalculator._get_activity_timeline(user, start_date, end_date)
        
        # Calculate trend
        trend = PerformanceCalculator._calculate_activity_trend(
            user, start_date, end_date, activity_score
        )
        
        # Get most common activity types
        most_common = sorted(
            activity_type_breakdown.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]
        
        most_common_activities = [
            {
                'type': activity_type,
                'count': data['count'],
                'success_rate': (data['success_count'] / data['count'] * 100) if data['count'] > 0 else 0,
                'weighted_score': data['weighted_score']
            }
            for activity_type, data in most_common
        ]
        
        return {
            # Core metrics
            'total_activities': total_activities,
            'successful_activities': successful_activities,
            'failed_activities': failed_activities,
            'activity_success_rate': round(success_rate, 2),
            
            # Weighted performance score
            'activity_performance_score': round(activity_score, 2),
            'critical_activity_success_rate': round(critical_success_rate, 2),
            
            # Volume metrics
            'daily_activity_avg': round(daily_avg, 2),
            'status_distribution': dict(status_distribution),
            
            # Category breakdown
            'category_metrics': category_scores,
            
            # Most common activities
            'most_common_activities': most_common_activities,
            
            # Timeline and trend
            'activity_timeline': timeline,
            'performance_trend': trend,
            
            # Metric type
            'metric_type': 'activity_based'
        }
    
    @staticmethod
    def _get_empty_activity_metrics():
        """Return empty metrics structure"""
        return {
            'total_activities': 0,
            'successful_activities': 0,
            'failed_activities': 0,
            'activity_success_rate': 0,
            'activity_performance_score': 0,
            'critical_activity_success_rate': 0,
            'daily_activity_avg': 0,
            'status_distribution': {},
            'category_metrics': {},
            'most_common_activities': [],
            'activity_timeline': [],
            'performance_trend': 'stable',
            'metric_type': 'activity_based'
        }
    
    @staticmethod
    def _get_activity_category(activity_type):
        """Determine category of an activity type"""
        for category, types in PerformanceCalculator.ACTIVITY_CATEGORIES.items():
            if activity_type in types:
                return category
        return 'other'
    
    @staticmethod
    def _get_activity_timeline(user, start_date, end_date):
        """Get daily activity timeline"""
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time())
        )
        
        # Get all activities for the period
        activities = Activity.objects.filter(
            user=user,
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        ).order_by('created_at')
        
        # Group activities by date in Python
        daily_data = defaultdict(lambda: {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'weighted_score': 0,
            'total_weight': 0
        })
        
        for activity in activities:
            date_key = activity.created_at.date()
            
            # Update counts
            daily_data[date_key]['total'] += 1
            
            if activity.is_success():
                daily_data[date_key]['successful'] += 1
            else:
                daily_data[date_key]['failed'] += 1
            
            # Calculate weighted contribution
            weight = PerformanceCalculator.ACTIVITY_WEIGHTS.get(activity.activity_type, 1)
            status_multiplier = PerformanceCalculator.STATUS_WEIGHTS.get(
                activity.status_code,
                0.5 if activity.is_success() else 0.1
            )
            
            daily_data[date_key]['weighted_score'] += weight * status_multiplier
            daily_data[date_key]['total_weight'] += weight
        
        # Build timeline
        timeline = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date in daily_data:
                data = daily_data[current_date]
                success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                avg_weighted_score = (data['weighted_score'] / data['total_weight'] * 100) if data['total_weight'] > 0 else 0
                
                timeline.append({
                    'date': current_date.isoformat(),
                    'total': data['total'],
                    'successful': data['successful'],
                    'failed': data['failed'],
                    'success_rate': round(success_rate, 2),
                    'weighted_score': round(avg_weighted_score, 2)
                })
            else:
                timeline.append({
                    'date': current_date.isoformat(),
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0,
                    'weighted_score': 0
                })
            
            current_date += timedelta(days=1)
        
        return timeline
    
    @staticmethod
    def _calculate_activity_trend(user, start_date, end_date, current_score):
        """Calculate performance trend based on activity score"""
        # Compare with previous period
        period_length = (end_date - start_date).days
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length)
        
        # Get previous period activities
        prev_start_datetime = timezone.make_aware(
            datetime.combine(prev_start, datetime.min.time())
        )
        prev_end_datetime = timezone.make_aware(
            datetime.combine(prev_end, datetime.max.time())
        )
        
        prev_activities = Activity.objects.filter(
            user=user,
            created_at__gte=prev_start_datetime,
            created_at__lte=prev_end_datetime
        )
        
        # Calculate simple score for previous period
        prev_total = prev_activities.count()
        if prev_total == 0:
            prev_score = 0
        else:
            prev_successful = prev_activities.filter(status_code__startswith='2').count()
            prev_score = (prev_successful / prev_total * 100) if prev_total > 0 else 0
        
        diff = current_score - prev_score
        if diff > 5:
            return 'improving'
        elif diff < -5:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _calculate_employee_task_metrics(user, start_date, end_date):
        """Calculate task completion metrics for employees"""
        assignments = TaskAssignment.objects.filter(
            user=user,
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        # Task counts by status
        total_assigned = assignments.count()
        completed = assignments.filter(status='completed').count()
        active = assignments.filter(status='active').count()
        scheduled = assignments.filter(status='scheduled').count()
        missed = assignments.filter(status='missed').count()
        cancelled = assignments.filter(status__in=['cancelled', 'reassigned']).count()
        
        # Overdue tasks
        overdue = assignments.filter(
            status='scheduled',
            end_time__lt=timezone.now()
        ).count()
        
        # Calculate completion rate
        completion_rate = 0
        if total_assigned > 0:
            completion_rate = round((completed / total_assigned) * 100, 2)
        
        # Calculate on-time completion rate
        on_time_rate = 0
        if completed > 0:
            on_time_completed = assignments.filter(
                status='completed',
                actual_end_time__lte=F('end_time')
            ).count()
            on_time_rate = round((on_time_completed / completed) * 100, 2)
        
        # Calculate average completion time (in hours)
        avg_completion_time = 0
        completed_with_times = assignments.filter(
            status='completed',
            actual_start_time__isnull=False,
            actual_end_time__isnull=False
        )
        
        if completed_with_times.exists():
            total_hours = 0
            for assignment in completed_with_times:
                duration = assignment.actual_end_time - assignment.actual_start_time
                total_hours += duration.total_seconds() / 3600
            avg_completion_time = round(total_hours / completed_with_times.count(), 2)
        
        # Calculate productivity score
        productivity_score = PerformanceCalculator._calculate_task_productivity_score(
            total_assigned, completed, active, missed
        )
        
        # Calculate trend
        performance_trend = PerformanceCalculator._calculate_task_trend(
            user, start_date, end_date
        )
        
        # Department comparison
        dept_comparison = 0
        if user.department:
            dept_avg = PerformanceCalculator._get_department_avg_completion(
                user.department, start_date, end_date
            )
            dept_comparison = round(completion_rate - dept_avg, 2)
        
        return {
            # Task metrics
            'total_assigned_tasks': total_assigned,
            'completed_tasks': completed,
            'active_tasks': active,
            'scheduled_tasks': scheduled,
            'missed_tasks': missed,
            'overdue_tasks': overdue,
            'cancelled_tasks': cancelled,
            
            # Performance scores
            'task_completion_rate': completion_rate,
            'on_time_completion_rate': on_time_rate,
            'productivity_score': productivity_score,
            'avg_completion_time_hours': avg_completion_time,
            
            # Comparison
            'performance_trend': performance_trend,
            'comparison_to_dept_avg': dept_comparison,
            
            # Metric type
            'metric_type': 'task_based'
        }
    
    @staticmethod
    def _calculate_task_productivity_score(total, completed, active, missed):
        """Calculate productivity score for task-based performance"""
        if total == 0:
            return 0
        
        # Weights
        COMPLETED_WEIGHT = 0.7
        ACTIVE_WEIGHT = 0.2
        MISSED_PENALTY = 0.1
        
        completed_score = (completed / total) * 100 * COMPLETED_WEIGHT
        active_score = (active / total) * 100 * ACTIVE_WEIGHT
        missed_penalty = (missed / total) * 100 * MISSED_PENALTY
        
        score = completed_score + active_score - missed_penalty
        return max(0, min(100, round(score, 2)))
    
    @staticmethod
    def _calculate_task_trend(user, start_date, end_date):
        """Calculate performance trend based on task completion"""
        mid_point = start_date + (end_date - start_date) / 2
        
        first_half = TaskAssignment.objects.filter(
            user=user,
            assignment_date__gte=start_date,
            assignment_date__lt=mid_point
        )
        second_half = TaskAssignment.objects.filter(
            user=user,
            assignment_date__gte=mid_point,
            assignment_date__lte=end_date
        )
        
        first_rate = PerformanceCalculator._get_completion_rate(first_half)
        second_rate = PerformanceCalculator._get_completion_rate(second_half)
        
        diff = second_rate - first_rate
        if diff > 5:
            return 'improving'
        elif diff < -5:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _get_completion_rate(assignments):
        """Calculate completion rate for assignments"""
        total = assignments.count()
        if total == 0:
            return 0
        completed = assignments.filter(status='completed').count()
        return (completed / total) * 100
    
    @staticmethod
    def _get_department_avg_completion(department, start_date, end_date):
        """Get average completion rate for department"""
        dept_assignments = TaskAssignment.objects.filter(
            department=department,
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        total = dept_assignments.count()
        if total == 0:
            return 0
        
        completed = dept_assignments.filter(status='completed').count()
        return (completed / total) * 100
    
    @staticmethod
    def get_performance_trends(user, days=30):
        """Get daily performance trends for a user"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        if user.role == 'employee':
            return PerformanceCalculator._get_employee_trends(user, start_date, end_date)
        else:
            return PerformanceCalculator._get_staff_trends(user, start_date, end_date)
    
    @staticmethod
    def _get_employee_trends(user, start_date, end_date):
        """Get daily task-based trends for employees"""
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            day_assignments = TaskAssignment.objects.filter(
                user=user,
                assignment_date=current_date
            )
            
            total = day_assignments.count()
            completed = day_assignments.filter(status='completed').count()
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            # Calculate daily productivity score
            productivity_score = PerformanceCalculator._calculate_task_productivity_score(
                total, completed, 
                day_assignments.filter(status='active').count(),
                day_assignments.filter(status='missed').count()
            )
            
            trends.append({
                'date': current_date,
                'completed_tasks': completed,
                'completion_rate': round(completion_rate, 2),
                'productivity_score': productivity_score
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def _get_staff_trends(user, start_date, end_date):
        """Get daily activity-based trends for staff"""
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
            
            day_activities = Activity.objects.filter(
                user=user,
                created_at__gte=day_start,
                created_at__lte=day_end
            )
            
            total = day_activities.count()
            successful = day_activities.filter(status_code__startswith='2').count()
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Calculate weighted score for the day
            weighted_score = 0
            total_weight = 0
            
            for activity in day_activities:
                weight = PerformanceCalculator.ACTIVITY_WEIGHTS.get(activity.activity_type, 1)
                status_multiplier = PerformanceCalculator.STATUS_WEIGHTS.get(
                    activity.status_code, 
                    0.5 if activity.is_success() else 0.1
                )
                weighted_score += weight * status_multiplier
                total_weight += weight
            
            performance_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0
            
            trends.append({
                'date': current_date,
                'activities': total,
                'successful': successful,
                'success_rate': round(success_rate, 2),
                'performance_score': round(performance_score, 2)
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def get_department_performance(department, start_date=None, end_date=None):
        """Calculate performance metrics for a department"""
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Get all employees in department
        employees = CustomUser.objects.filter(
            department=department,
            role='employee',
            is_active=True,
            status='approved'
        )
        
        employee_count = employees.count()
        
        # Get all assignments for department
        assignments = TaskAssignment.objects.filter(
            department=department,
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        total_assigned = assignments.count()
        completed = assignments.filter(status='completed').count()
        active = assignments.filter(status='active').count()
        missed = assignments.filter(status='missed').count()
        
        # Calculate averages
        avg_completion_rate = 0
        if total_assigned > 0:
            avg_completion_rate = round((completed / total_assigned) * 100, 2)
        
        # Calculate individual performances for top performers
        top_performers = []
        for employee in employees[:5]:  # Top 5 employees
            perf = PerformanceCalculator.calculate_user_performance(employee, start_date, end_date)
            if perf.get('task_completion_rate', 0) > 0:
                top_performers.append({
                    'user_id': employee.id,
                    'full_name': employee.full_name,
                    'completion_rate': perf.get('task_completion_rate', 0),
                    'productivity_score': perf.get('productivity_score', 0),
                    'completed_tasks': perf.get('completed_tasks', 0)
                })
        
        # Sort by completion rate
        top_performers = sorted(top_performers, key=lambda x: x['completion_rate'], reverse=True)[:3]
        
        return {
            'department_id': department.id,
            'department_name': department.name,
            'employee_count': employee_count,
            'total_assigned_tasks': total_assigned,
            'completed_tasks': completed,
            'active_tasks': active,
            'missed_tasks': missed,
            'avg_task_completion_rate': avg_completion_rate,
            'avg_productivity_score': PerformanceCalculator._calculate_avg_productivity(employees, start_date, end_date),
            'avg_on_time_completion_rate': PerformanceCalculator._calculate_avg_on_time_rate(employees, start_date, end_date),
            'top_performers': top_performers
        }
    
    @staticmethod
    def _calculate_avg_productivity(employees, start_date, end_date):
        """Calculate average productivity score for a group of employees"""
        if not employees.exists():
            return 0
        
        total_score = 0
        count = 0
        for employee in employees:
            perf = PerformanceCalculator.calculate_user_performance(employee, start_date, end_date)
            total_score += perf.get('productivity_score', 0)
            count += 1
        
        return round(total_score / count, 2) if count > 0 else 0
    
    @staticmethod
    def _calculate_avg_on_time_rate(employees, start_date, end_date):
        """Calculate average on-time completion rate for a group of employees"""
        if not employees.exists():
            return 0
        
        total_rate = 0
        count = 0
        for employee in employees:
            perf = PerformanceCalculator.calculate_user_performance(employee, start_date, end_date)
            total_rate += perf.get('on_time_completion_rate', 0)
            count += 1
        
        return round(total_rate / count, 2) if count > 0 else 0
    
    @staticmethod
    def get_organization_performance(start_date=None, end_date=None):
        """Calculate organization-wide performance metrics"""
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Basic counts
        total_employees = CustomUser.objects.filter(
            role='employee',
            is_active=True,
            status='approved'
        ).count()
        
        total_departments = Department.objects.filter(status='active').count()
        
        # Task metrics
        assignments = TaskAssignment.objects.filter(
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        total_tasks_assigned = assignments.count()
        total_tasks_completed = assignments.filter(status='completed').count()
        total_active_tasks = assignments.filter(status='active').count()
        total_missed_tasks = assignments.filter(status='missed').count()
        
        # Overall scores
        overall_completion_rate = 0
        if total_tasks_assigned > 0:
            overall_completion_rate = round((total_tasks_completed / total_tasks_assigned) * 100, 2)
        
        # Department performance breakdown
        departments = Department.objects.filter(status='active')
        department_performance = []
        for dept in departments[:10]:  # Top 10 departments
            dept_perf = PerformanceCalculator.get_department_performance(dept, start_date, end_date)
            department_performance.append(dept_perf)
        
        # Top employees organization-wide
        employees = CustomUser.objects.filter(
            role='employee',
            is_active=True,
            status='approved'
        )[:20]  # Top 20 employees
        
        top_employees = []
        for employee in employees:
            perf = PerformanceCalculator.calculate_user_performance(employee, start_date, end_date)
            if perf.get('task_completion_rate', 0) > 0:
                top_employees.append(perf)
        
        # Sort by completion rate
        top_employees = sorted(top_employees, key=lambda x: x['task_completion_rate'], reverse=True)[:10]
        
        # Calculate overall productivity score
        overall_productivity_score = PerformanceCalculator._calculate_avg_productivity(
            CustomUser.objects.filter(role='employee', is_active=True),
            start_date,
            end_date
        )
        
        return {
            'total_employees': total_employees,
            'total_departments': total_departments,
            'total_tasks_assigned': total_tasks_assigned,
            'total_tasks_completed': total_tasks_completed,
            'total_active_tasks': total_active_tasks,
            'total_missed_tasks': total_missed_tasks,
            'overall_completion_rate': overall_completion_rate,
            'overall_productivity_score': overall_productivity_score,
            'department_performance': department_performance,
            'top_employees': top_employees,
            'period_start': start_date,
            'period_end': end_date
        }
    
    @staticmethod
    def get_detailed_activity_analysis(user, start_date=None, end_date=None):
        """
        Get detailed analysis of user's activities including:
        - Activity type distribution
        - Status code analysis
        - Time-based patterns
        - Success/failure analysis
        """
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(
            datetime.combine(start_date, datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            datetime.combine(end_date, datetime.max.time())
        )
        
        activities = Activity.objects.filter(
            user=user,
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        # Activity type analysis
        type_analysis = []
        for activity_type in PerformanceCalculator.ACTIVITY_WEIGHTS.keys():
            type_activities = activities.filter(activity_type=activity_type)
            count = type_activities.count()
            if count > 0:
                successful = type_activities.filter(status_code__startswith='2').count()
                failed = type_activities.filter(
                    Q(status_code__startswith='4') | Q(status_code__startswith='5')
                ).count()
                
                # Status distribution for this type
                status_dist = {}
                for status_code in ['200', '201', '400', '401', '403', '404', '500']:
                    status_count = type_activities.filter(status_code=status_code).count()
                    if status_count > 0:
                        status_dist[status_code] = status_count
                
                type_analysis.append({
                    'activity_type': activity_type,
                    'total': count,
                    'successful': successful,
                    'failed': failed,
                    'success_rate': round(successful / count * 100, 2) if count > 0 else 0,
                    'status_distribution': status_dist,
                    'weight': PerformanceCalculator.ACTIVITY_WEIGHTS.get(activity_type, 1)
                })
        
        # Hourly distribution
        hourly_distribution = (
            activities
            .annotate(hour=TruncHour('created_at'))
            .values('hour')
            .annotate(
                total=Count('id'),
                successful=Count('id', filter=Q(status_code__startswith='2'))
            )
            .order_by('hour')
        )
        
        # Status code analysis
        status_analysis = []
        for status_code, _ in Activity.STATUS_CHOICES:
            count = activities.filter(status_code=status_code).count()
            if count > 0:
                status_analysis.append({
                    'status_code': status_code,
                    'count': count,
                    'percentage': round(count / activities.count() * 100, 2) if activities.count() > 0 else 0
                })
        
        return {
            'total_activities': activities.count(),
            'activity_type_analysis': type_analysis,
            'hourly_distribution': list(hourly_distribution),
            'status_analysis': status_analysis,
            'period': {
                'start': start_date,
                'end': end_date
            }
        }