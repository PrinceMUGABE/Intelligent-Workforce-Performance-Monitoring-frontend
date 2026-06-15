# reportApp/utils.py
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, F, Case, When, IntegerField
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Utility class for generating various reports"""
    
    @staticmethod
    def get_date_range_filter(start_date=None, end_date=None, field_name='created_at'):
        """
        Generate date range filter for queries
        """
        filters = Q()
        
        if start_date:
            # Make datetime timezone-aware
            if isinstance(start_date, datetime):
                start_datetime = start_date if timezone.is_aware(start_date) else timezone.make_aware(start_date)
            else:
                start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            filters &= Q(**{f'{field_name}__gte': start_datetime})
        
        if end_date:
            # Make datetime timezone-aware and include the entire end date
            if isinstance(end_date, datetime):
                end_datetime = end_date if timezone.is_aware(end_date) else timezone.make_aware(end_date)
            else:
                end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            filters &= Q(**{f'{field_name}__lte': end_datetime})
        
        return filters
    
    @staticmethod
    def calculate_percentage(part, whole):
        """Calculate percentage safely"""
        if whole == 0:
            return 0
        return round((part / whole) * 100, 2)
    
    @staticmethod
    def get_summary_template(report_type, total_count, filters, user):
        """
        Generate standard summary template for reports
        """
        return {
            'total_count': total_count,
            'filters_applied': {
                'start_date': filters.get('start_date').isoformat() if filters.get('start_date') else None,
                'end_date': filters.get('end_date').isoformat() if filters.get('end_date') else None,
                'department_id': filters.get('department_id'),
                'user_id': filters.get('user_id'),
                'status': filters.get('status'),
            },
            'date_range': {
                'start_date': filters.get('start_date').isoformat() if filters.get('start_date') else None,
                'end_date': filters.get('end_date').isoformat() if filters.get('end_date') else None,
            },
            'generated_at': timezone.now().isoformat(),
            'generated_by': user.full_name if user else 'System',
            'report_type': report_type,
        }


class UserReportGenerator(ReportGenerator):
    """Generate user-related reports"""
    
    @staticmethod
    def generate_user_report(queryset, filters, user):
        """
        Generate comprehensive user report
        """
        users_data = []
        
        for u in queryset:
            users_data.append({
                # 'id': u.id,
                'phone_number': u.phone_number,
                'email': u.email,
                'work_mail_address': u.work_mail_address,
                'full_name': u.full_name,
                'role': u.role,
                # 'department_id': u.department_id,
                'department_name': u.department.name if u.department else None,
                'status': u.status,
                'availability_status': u.availability_status,
                'day_off': u.day_off,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'is_active': u.is_active,
            })
        
        # Calculate statistics
        total_users = len(users_data)
        statistics = {
            'total_users': total_users,
            'by_role': {
                'admin': queryset.filter(role='admin').count(),
                'manager': queryset.filter(role='manager').count(),
                'analyst': queryset.filter(role='analyst').count(),
                'employee': queryset.filter(role='employee').count(),
            },
            'by_status': {
                'pending': queryset.filter(status='pending').count(),
                'approved': queryset.filter(status='approved').count(),
                'rejected': queryset.filter(status='rejected').count(),
            },
            'by_availability': {
                'active': queryset.filter(availability_status='active').count(),
                'inactive': queryset.filter(availability_status='inactive').count(),
            },
            'with_day_off': queryset.exclude(Q(day_off__isnull=True) | Q(day_off='none')).count(),
        }
        
        # Add percentages
        if total_users > 0:
            statistics['percentages'] = {
                'approved': UserReportGenerator.calculate_percentage(
                    statistics['by_status']['approved'], total_users
                ),
                'active': UserReportGenerator.calculate_percentage(
                    statistics['by_availability']['active'], total_users
                ),
            }
        
        summary = UserReportGenerator.get_summary_template(
            'User Report', total_users, filters, user
        )
        
        return {
            'summary': summary,
            'users': users_data,
            'statistics': statistics,
        }


class DepartmentReportGenerator(ReportGenerator):
    """Generate department-related reports"""
    
    @staticmethod
    def generate_department_report(queryset, filters, user):
        """
        Generate comprehensive department report
        """
        departments_data = []
        
        for dept in queryset:
            departments_data.append({
                # 'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'status': dept.status,
                'employee_count': dept.get_employee_count(),
                'created_at': dept.created_at.isoformat() if dept.created_at else None,
                'created_by_name': dept.created_by.full_name if dept.created_by else None,
            })
        
        # Calculate statistics
        total_departments = len(departments_data)
        total_employees = sum([d['employee_count'] for d in departments_data])
        
        statistics = {
            'total_departments': total_departments,
            'active_departments': queryset.filter(status='active').count(),
            'inactive_departments': queryset.filter(status='inactive').count(),
            'total_employees_across_departments': total_employees,
            'average_employees_per_department': round(
                total_employees / total_departments, 2
            ) if total_departments > 0 else 0,
            'departments_by_size': sorted(
                [{'name': d['name'], 'employee_count': d['employee_count']} 
                 for d in departments_data],
                key=lambda x: x['employee_count'],
                reverse=True
            )[:5],  # Top 5
        }
        
        summary = DepartmentReportGenerator.get_summary_template(
            'Department Report', total_departments, filters, user
        )
        
        return {
            'summary': summary,
            'departments': departments_data,
            'statistics': statistics,
        }


class TaskReportGenerator(ReportGenerator):
    """Generate task-related reports"""
    
    @staticmethod
    def generate_task_report(queryset, filters, user):
        """
        Generate comprehensive task report
        """
        from taskAssignmentApp.models import TaskAssignment
        
        tasks_data = []
        
        for task in queryset:
            # Get assignment statistics for this task
            assignments = TaskAssignment.objects.filter(task=task)
            
            if filters.get('start_date') or filters.get('end_date'):
                date_filter = TaskReportGenerator.get_date_range_filter(
                    filters.get('start_date'),
                    filters.get('end_date'),
                    'assignment_date'
                )
                assignments = assignments.filter(date_filter)
            
            tasks_data.append({
                # 'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                'created_by_name': task.created_by.full_name if task.created_by else None,
                'total_assignments': assignments.count(),
                'completed_assignments': assignments.filter(status='completed').count(),
                'active_assignments': assignments.filter(status='active').count(),
                'scheduled_assignments': assignments.filter(status='scheduled').count(),
                'missed_assignments': assignments.filter(status='missed').count(),
            })
        
        # Calculate statistics
        total_tasks = len(tasks_data)
        total_assignments = sum([t['total_assignments'] for t in tasks_data])
        total_completed = sum([t['completed_assignments'] for t in tasks_data])
        
        statistics = {
            'total_tasks': total_tasks,
            'by_status': {
                'pending': queryset.filter(status='pending').count(),
                'active': queryset.filter(status='active').count(),
                'not_active': queryset.filter(status='not-active').count(),
            },
            'total_assignments': total_assignments,
            'total_completed_assignments': total_completed,
            'completion_rate': TaskReportGenerator.calculate_percentage(
                total_completed, total_assignments
            ) if total_assignments > 0 else 0,
            'most_assigned_tasks': sorted(
                [{'name': t['name'], 'assignments': t['total_assignments']} 
                 for t in tasks_data],
                key=lambda x: x['assignments'],
                reverse=True
            )[:5],  # Top 5
        }
        
        summary = TaskReportGenerator.get_summary_template(
            'Task Report', total_tasks, filters, user
        )
        
        return {
            'summary': summary,
            'tasks': tasks_data,
            'statistics': statistics,
        }


class TaskAssignmentReportGenerator(ReportGenerator):
    """Generate task assignment reports"""
    
    @staticmethod
    def generate_assignment_report(queryset, filters, user):
        """
        Generate comprehensive task assignment report
        """
        assignments_data = []
        
        for assignment in queryset:
            assignments_data.append({
                # 'id': assignment.id,
                # 'user_id': assignment.user_id,
                'user_name': assignment.user.full_name,
                'user_email': assignment.user.email,
                'task_id': assignment.task_id,
                'task_name': assignment.task.name,
                # 'department_id': assignment.department_id,
                'department_name': assignment.department.name,
                'assignment_date': assignment.assignment_date.isoformat() if assignment.assignment_date else None,
                'start_time': assignment.start_time.isoformat() if assignment.start_time else None,
                'end_time': assignment.end_time.isoformat() if assignment.end_time else None,
                'actual_start_time': assignment.actual_start_time.isoformat() if assignment.actual_start_time else None,
                'actual_end_time': assignment.actual_end_time.isoformat() if assignment.actual_end_time else None,
                'status': assignment.status,
                'priority': assignment.priority,
                'sequence_order': assignment.sequence_order,
                'duration_minutes': assignment.duration_minutes,
                'duration_days': assignment.duration_days,
                'actual_duration_minutes': assignment.actual_duration_minutes,
                'is_modified': assignment.is_modified,
                'assigned_by_name': assignment.assigned_by.full_name if assignment.assigned_by else None,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
            })
        
        # Calculate statistics
        total_assignments = len(assignments_data)
        
        statistics = {
            'total_assignments': total_assignments,
            'by_status': {
                'scheduled': queryset.filter(status='scheduled').count(),
                'active': queryset.filter(status='active').count(),
                'completed': queryset.filter(status='completed').count(),
                'missed': queryset.filter(status='missed').count(),
                'reassigned': queryset.filter(status='reassigned').count(),
                'cancelled': queryset.filter(status='cancelled').count(),
            },
            'by_priority': {
                'low': queryset.filter(priority='low').count(),
                'medium': queryset.filter(priority='medium').count(),
                'high': queryset.filter(priority='high').count(),
                'urgent': queryset.filter(priority='urgent').count(),
            },
            'completion_rate': TaskAssignmentReportGenerator.calculate_percentage(
                queryset.filter(status='completed').count(),
                total_assignments
            ) if total_assignments > 0 else 0,
            'miss_rate': TaskAssignmentReportGenerator.calculate_percentage(
                queryset.filter(status='missed').count(),
                total_assignments
            ) if total_assignments > 0 else 0,
            'multi_day_assignments': queryset.filter(
                start_time__date__lt=F('end_time__date')
            ).count(),
            'modified_assignments': queryset.filter(is_modified=True).count(),
        }
        
        # Calculate average durations
        completed_assignments = queryset.filter(
            status='completed',
            actual_start_time__isnull=False,
            actual_end_time__isnull=False
        )
        
        if completed_assignments.exists():
            total_actual_duration = sum([
                a.actual_duration_minutes for a in completed_assignments 
                if a.actual_duration_minutes
            ])
            statistics['average_completion_time_minutes'] = round(
                total_actual_duration / completed_assignments.count(), 2
            )
        else:
            statistics['average_completion_time_minutes'] = 0
        
        summary = TaskAssignmentReportGenerator.get_summary_template(
            'Task Assignment Report', total_assignments, filters, user
        )
        
        return {
            'summary': summary,
            'assignments': assignments_data,
            'statistics': statistics,
        }


class DayOffReportGenerator(ReportGenerator):
    """Generate day-off request reports"""
    
    @staticmethod
    def generate_dayoff_report(queryset, filters, user):
        """
        Generate comprehensive day-off request report
        """
        dayoff_requests_data = []
        
        for request in queryset:
            dayoff_requests_data.append({
                # 'id': request.id,
                # 'user_id': request.user_id,
                'user_name': request.user.full_name,
                'user_email': request.user.email,
                'current_day_off': request.current_day_off,
                'requested_day_off': request.requested_day_off,
                'effective_from': request.effective_from.isoformat() if request.effective_from else None,
                'status': request.status,
                'reason': request.reason,
                'approved_by_name': request.approved_by.full_name if request.approved_by else None,
                'approved_at': request.approved_at.isoformat() if request.approved_at else None,
                'approval_notes': request.approval_notes,
                'created_at': request.created_at.isoformat() if request.created_at else None,
            })
        
        # Calculate statistics
        total_requests = len(dayoff_requests_data)
        
        statistics = {
            'total_requests': total_requests,
            'by_status': {
                'pending': queryset.filter(status='pending').count(),
                'approved': queryset.filter(status='approved').count(),
                'rejected': queryset.filter(status='rejected').count(),
                'cancelled': queryset.filter(status='cancelled').count(),
            },
            'approval_rate': DayOffReportGenerator.calculate_percentage(
                queryset.filter(status='approved').count(),
                queryset.exclude(status='cancelled').count()
            ) if queryset.exclude(status='cancelled').count() > 0 else 0,
            'by_requested_day': {},
            'by_current_day': {},
        }
        
        # Count by requested day
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'none']:
            statistics['by_requested_day'][day] = queryset.filter(
                requested_day_off=day
            ).count()
        
        # Count by current day
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'none']:
            statistics['by_current_day'][day] = queryset.filter(
                current_day_off=day
            ).count()
        
        summary = DayOffReportGenerator.get_summary_template(
            'Day-Off Request Report', total_requests, filters, user
        )
        
        return {
            'summary': summary,
            'day_off_requests': dayoff_requests_data,
            'statistics': statistics,
        }


class ActivityReportGenerator(ReportGenerator):
    """Generate activity reports"""
    
    @staticmethod
    def generate_activity_report(queryset, filters, user):
        """
        Generate comprehensive activity report
        Note: queryset should already be a list at this point
        """
        activities_data = []
        
        # Handle both queryset and list inputs
        items = list(queryset) if not isinstance(queryset, list) else queryset
        
        for activity in items:
            activities_data.append({
                # 'id': activity.id,
                'activity_type': activity.activity_type,
                # 'user_id': activity.user_id,
                'user_name': activity.user.full_name if activity.user else None,
                'status_code': activity.status_code,
                'description': activity.description,
                'ip_address': activity.ip_address,
                'device_type': activity.device_type,
                'browser': activity.browser,
                'request_method': activity.request_method,
                'endpoint': activity.endpoint,
                # 'from_status': activity.from_status,
                # 'to_status': activity.to_status,
                'created_at': activity.created_at.isoformat() if activity.created_at else None,
            })
        
        # Calculate statistics
        total_activities = len(activities_data)
        
        # For statistics, we need to work with the original items
        from activityApp.models import Activity
        
        # Count by status code
        status_code_counts = {}
        for activity in items:
            code = activity.status_code
            status_code_counts[code] = status_code_counts.get(code, 0) + 1
        
        # Count by activity type (top 10)
        activity_type_counts = {}
        for activity in items:
            atype = activity.activity_type
            activity_type_counts[atype] = activity_type_counts.get(atype, 0) + 1
        
        # Sort and get top 10
        top_activity_types = dict(sorted(activity_type_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Count by device type
        device_type_counts = {}
        for activity in items:
            dtype = activity.device_type
            if dtype:
                device_type_counts[dtype] = device_type_counts.get(dtype, 0) + 1
        
        # Calculate success rate (2xx status codes)
        success_count = sum(1 for activity in items if activity.status_code and activity.status_code.startswith('2'))
        
        statistics = {
            'total_activities': total_activities,
            'by_status_code': status_code_counts,
            'by_activity_type': top_activity_types,
            'by_device_type': device_type_counts,
            'success_rate': ActivityReportGenerator.calculate_percentage(
                success_count, total_activities
            ) if total_activities > 0 else 0,
        }
        
        summary = ActivityReportGenerator.get_summary_template(
            'Activity Report', total_activities, filters, user
        )
        
        return {
            'summary': summary,
            'activities': activities_data,
            'statistics': statistics,
        }


class PerformanceReportGenerator(ReportGenerator):
    """Generate performance reports"""
    
    @staticmethod
    def generate_performance_report(user_id, filters, requesting_user):
        """
        Generate comprehensive performance report for a user
        """
        from userApp.models import CustomUser
        from taskAssignmentApp.models import TaskAssignment
        
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None
        
        # Get user's assignments
        assignments = TaskAssignment.objects.filter(user_id=user_id)
        
        # Apply date filter if provided
        if filters.get('start_date') or filters.get('end_date'):
            date_filter = PerformanceReportGenerator.get_date_range_filter(
                filters.get('start_date'),
                filters.get('end_date'),
                'assignment_date'
            )
            assignments = assignments.filter(date_filter)
        
        # Calculate performance metrics
        total_assignments = assignments.count()
        completed = assignments.filter(status='completed').count()
        missed = assignments.filter(status='missed').count()
        active = assignments.filter(status='active').count()
        scheduled = assignments.filter(status='scheduled').count()
        
        performance_data = {
            'user': {
                # 'id': target_user.id,
                'full_name': target_user.full_name,
                'email': target_user.email,
                'role': target_user.role,
                'department': target_user.department.name if target_user.department else None,
            },
            'assignment_metrics': {
                'total_assignments': total_assignments,
                'completed': completed,
                'missed': missed,
                'active': active,
                'scheduled': scheduled,
                'reassigned': assignments.filter(status='reassigned').count(),
                'cancelled': assignments.filter(status='cancelled').count(),
            },
            'performance_rates': {
                'completion_rate': PerformanceReportGenerator.calculate_percentage(
                    completed, total_assignments
                ) if total_assignments > 0 else 0,
                'miss_rate': PerformanceReportGenerator.calculate_percentage(
                    missed, total_assignments
                ) if total_assignments > 0 else 0,
            },
        }
        
        # Calculate average completion time
        completed_assignments = assignments.filter(
            status='completed',
            actual_start_time__isnull=False,
            actual_end_time__isnull=False
        )
        
        if completed_assignments.exists():
            total_duration = sum([
                a.actual_duration_minutes for a in completed_assignments 
                if a.actual_duration_minutes
            ])
            performance_data['average_completion_time_minutes'] = round(
                total_duration / completed_assignments.count(), 2
            )
        else:
            performance_data['average_completion_time_minutes'] = 0
        
        # Task breakdown
        task_breakdown = assignments.values('task__name').annotate(
            total=Count('id'),
            completed=Count(Case(When(status='completed', then=1))),
            missed=Count(Case(When(status='missed', then=1))),
        ).order_by('-total')
        
        performance_data['task_breakdown'] = list(task_breakdown)
        
        # Recent assignments (last 10)
        recent_assignments = assignments.order_by('-created_at')[:10]
        performance_data['recent_assignments'] = [
            {
                # 'id': a.id,
                'task__name': a.task.name,
                'status': a.status,
                'assignment_date': a.assignment_date.isoformat() if a.assignment_date else None,
                'created_at': a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_assignments
        ]
        
        statistics = {
            'total_assignments': total_assignments,
            'completion_rate': performance_data['performance_rates']['completion_rate'],
            'miss_rate': performance_data['performance_rates']['miss_rate'],
            'average_completion_time': performance_data['average_completion_time_minutes'],
        }
        
        summary = PerformanceReportGenerator.get_summary_template(
            'Performance Report', total_assignments, filters, requesting_user
        )
        summary['for_user'] = target_user.full_name
        
        return {
            'summary': summary,
            'performance_data': performance_data,
            'statistics': statistics,
        }


class OrganizationReportGenerator(ReportGenerator):
    """Generate organization-wide reports"""
    
    @staticmethod
    def generate_organization_report(filters, user):
        """
        Generate comprehensive organization-wide report
        """
        from userApp.models import CustomUser
        from departmentApp.models import Department
        from taskApp.models import Task
        from taskAssignmentApp.models import TaskAssignment
        from requestApp.models import DayOffChangeRequest
        from activityApp.models import Activity
        
        # Apply date filter
        date_filter = Q()
        if filters.get('start_date') or filters.get('end_date'):
            date_filter = OrganizationReportGenerator.get_date_range_filter(
                filters.get('start_date'),
                filters.get('end_date')
            )
        
        organization_data = {
            'users': {
                'total': CustomUser.objects.count(),
                'by_role': {
                    'admin': CustomUser.objects.filter(role='admin').count(),
                    'manager': CustomUser.objects.filter(role='manager').count(),
                    'analyst': CustomUser.objects.filter(role='analyst').count(),
                    'employee': CustomUser.objects.filter(role='employee').count(),
                },
                'by_status': {
                    'approved': CustomUser.objects.filter(status='approved').count(),
                    'pending': CustomUser.objects.filter(status='pending').count(),
                    'rejected': CustomUser.objects.filter(status='rejected').count(),
                },
                'active_users': CustomUser.objects.filter(
                    availability_status='active'
                ).count(),
            },
            'departments': {
                'total': Department.objects.count(),
                'active': Department.objects.filter(status='active').count(),
                'inactive': Department.objects.filter(status='inactive').count(),
            },
            'tasks': {
                'total': Task.objects.count(),
                'by_status': {
                    'pending': Task.objects.filter(status='pending').count(),
                    'active': Task.objects.filter(status='active').count(),
                    'not_active': Task.objects.filter(status='not-active').count(),
                },
            },
        }
        
        # Task assignments (filtered by date if provided)
        assignments = TaskAssignment.objects.all()
        if date_filter:
            assignments = assignments.filter(date_filter)
        
        organization_data['task_assignments'] = {
            'total': assignments.count(),
            'by_status': {
                'scheduled': assignments.filter(status='scheduled').count(),
                'active': assignments.filter(status='active').count(),
                'completed': assignments.filter(status='completed').count(),
                'missed': assignments.filter(status='missed').count(),
                'reassigned': assignments.filter(status='reassigned').count(),
                'cancelled': assignments.filter(status='cancelled').count(),
            },
            'completion_rate': OrganizationReportGenerator.calculate_percentage(
                assignments.filter(status='completed').count(),
                assignments.count()
            ) if assignments.count() > 0 else 0,
        }
        
        # Day-off requests (filtered by date if provided)
        dayoff_requests = DayOffChangeRequest.objects.all()
        if date_filter:
            dayoff_requests = dayoff_requests.filter(date_filter)
        
        organization_data['day_off_requests'] = {
            'total': dayoff_requests.count(),
            'by_status': {
                'pending': dayoff_requests.filter(status='pending').count(),
                'approved': dayoff_requests.filter(status='approved').count(),
                'rejected': dayoff_requests.filter(status='rejected').count(),
                'cancelled': dayoff_requests.filter(status='cancelled').count(),
            },
        }
        
        # Activities (filtered by date if provided)
        activities = Activity.objects.all()
        if date_filter:
            activities = activities.filter(date_filter)
        
        organization_data['activities'] = {
            'total': activities.count(),
            'successful': activities.filter(status_code__startswith='2').count(),
            'errors': activities.filter(
                Q(status_code__startswith='4') | Q(status_code__startswith='5')
            ).count(),
        }
        
        # Calculate overall statistics
        statistics = {
            'total_users': organization_data['users']['total'],
            'total_departments': organization_data['departments']['total'],
            'total_tasks': organization_data['tasks']['total'],
            'total_assignments': organization_data['task_assignments']['total'],
            'overall_completion_rate': organization_data['task_assignments']['completion_rate'],
            'total_dayoff_requests': organization_data['day_off_requests']['total'],
            'total_activities': organization_data['activities']['total'],
        }
        
        summary = OrganizationReportGenerator.get_summary_template(
            'Organization Report', 0, filters, user
        )
        
        return {
            'summary': summary,
            'organization_data': organization_data,
            'statistics': statistics,
        }