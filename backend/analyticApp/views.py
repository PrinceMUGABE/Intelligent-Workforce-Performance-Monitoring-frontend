# analyticApp/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q, F, Case, When, Value, FloatField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import month_abbr
import traceback

from userApp.models import CustomUser
from departmentApp.models import Department
from taskApp.models import Task
from taskAssignmentApp.models import TaskAssignment
from requestApp.models import DayOffChangeRequest
from activityApp.models import Activity

from .serializers import (
    AnalyticsDashboardSerializer,
    DepartmentAnalyticsSerializer,
    UserAnalyticsSerializer,
    SystemOverviewSerializer
)


# ==================== HELPER FUNCTIONS ====================

def calculate_trend_percentage(current, previous):
    """Calculate percentage change between current and previous values"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_date_range(time_range='6months'):
    """Get start and end dates based on time range"""
    end_date = timezone.now().date()
    
    if time_range == '1month':
        start_date = end_date - timedelta(days=30)
    elif time_range == '3months':
        start_date = end_date - timedelta(days=90)
    elif time_range == '6months':
        start_date = end_date - timedelta(days=180)
    elif time_range == '1year':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=180)  # Default to 6 months
    
    return start_date, end_date


def calculate_performance_score(completed, total, missed=0):
    """Calculate performance score based on completed, total, and missed tasks"""
    if total == 0:
        return 0.0
    
    completion_rate = (completed / total) * 100
    miss_penalty = (missed / total) * 10 if missed > 0 else 0
    
    score = max(0, completion_rate - miss_penalty)
    return round(score, 2)


def generate_insights(data):
    """Generate actionable insights based on analytics data"""
    insights = []
    now = timezone.now()
    
    # Check department performance
    for dept in data.get('department_performance', []):
        if dept['performance'] >= 90:
            insights.append({
                'type': 'success',
                'title': 'Strong Performance',
                'description': f"{dept['department']} department shows excellent performance at {dept['performance']:.1f}%",
                'priority': 'low',
                'created_at': now
            })
        elif dept['performance'] < 70:
            insights.append({
                'type': 'warning',
                'title': 'Attention Needed',
                'description': f"{dept['department']} department performance is below target at {dept['performance']:.1f}%",
                'priority': 'high',
                'created_at': now
            })
    
    # Check overall trends
    monthly_trends = data.get('monthly_trends', [])
    if len(monthly_trends) >= 2:
        latest = monthly_trends[-1]
        previous = monthly_trends[-2]
        
        if latest['productivity'] > previous['productivity']:
            insights.append({
                'type': 'success',
                'title': 'Positive Trend',
                'description': f"Productivity increased by {latest['productivity'] - previous['productivity']:.1f}% this month",
                'priority': 'medium',
                'created_at': now
            })
        elif latest['productivity'] < previous['productivity'] - 5:
            insights.append({
                'type': 'warning',
                'title': 'Declining Productivity',
                'description': f"Productivity decreased by {previous['productivity'] - latest['productivity']:.1f}% this month",
                'priority': 'high',
                'created_at': now
            })
    
    # Check pending day-off requests
    dayoff_data = data.get('dayoff_analytics', {})
    if dayoff_data.get('pending_requests', 0) > 5:
        insights.append({
            'type': 'info',
            'title': 'Pending Requests',
            'description': f"{dayoff_data['pending_requests']} day-off requests awaiting approval",
            'priority': 'medium',
            'created_at': now
        })
    
    # Check task completion rate
    task_completion = data.get('task_completion_rate', {})
    if task_completion.get('value', 0) >= 85:
        insights.append({
            'type': 'success',
            'title': 'High Task Completion',
            'description': f"Task completion rate is strong at {task_completion.get('value', 0):.1f}%",
            'priority': 'low',
            'created_at': now
        })
    
    return insights


# ==================== ANALYTICS ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics_dashboard(request):
    """
    Get comprehensive analytics dashboard data
    
    Query parameters:
    - time_range: 1month, 3months, 6months, 1year (default: 6months)
    - department_id: Filter by specific department (optional)
    """
    try:
        user = request.user
        
        # Only allow admin, manager, and analyst to access analytics
        if user.role not in ['admin', 'manager', 'analyst']:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only admins, managers, and analysts can access analytics.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        time_range = request.GET.get('time_range', '6months')
        department_id = request.GET.get('department_id', None)
        
        start_date, end_date = get_date_range(time_range)
        
        # Base querysets
        employees_qs = CustomUser.objects.filter(role='employee')
        if department_id:
            employees_qs = employees_qs.filter(department_id=department_id)
        
        assignments_qs = TaskAssignment.objects.filter(
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        if department_id:
            assignments_qs = assignments_qs.filter(department_id=department_id)
        
        # Calculate key metrics
        total_employees = employees_qs.count()
        active_employees = employees_qs.filter(availability_status='active').count()
        
        # Previous period for trend calculation
        prev_start = start_date - (end_date - start_date)
        prev_assignments = TaskAssignment.objects.filter(
            assignment_date__gte=prev_start,
            assignment_date__lt=start_date
        )
        if department_id:
            prev_assignments = prev_assignments.filter(department_id=department_id)
        
        # Performance metrics
        total_assignments = assignments_qs.count()
        completed_assignments = assignments_qs.filter(status='completed').count()
        prev_total = prev_assignments.count()
        prev_completed = prev_assignments.filter(status='completed').count()
        
        current_completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        prev_completion_rate = (prev_completed / prev_total * 100) if prev_total > 0 else 0
        
        # Top performers (users with highest completion rates)
        top_performers_data = []
        for emp in employees_qs.filter(availability_status='active'):
            emp_assignments = assignments_qs.filter(user=emp)
            emp_completed = emp_assignments.filter(status='completed').count()
            emp_total = emp_assignments.count()
            
            if emp_total > 0:
                completion_rate = (emp_completed / emp_total) * 100
                if completion_rate >= 80:  # Only include high performers
                    top_performers_data.append({
                        'user_id': emp.id,
                        'full_name': emp.full_name,
                        'email': emp.email,
                        'department': emp.department.name if emp.department else 'N/A',
                        'tasks_completed': emp_completed,
                        'tasks_active': emp_assignments.filter(status='active').count(),
                        'tasks_missed': emp_assignments.filter(status='missed').count(),
                        'completion_rate': round(completion_rate, 2),
                        'performance_score': calculate_performance_score(
                            emp_completed, 
                            emp_total, 
                            emp_assignments.filter(status='missed').count()
                        )
                    })
        
        top_performers_data.sort(key=lambda x: x['performance_score'], reverse=True)
        top_performers_count = len(top_performers_data)
        
        # Monthly trends (last 7 months)
        monthly_trends = []
        for i in range(6, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = end_date
            else:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
                month_end = next_month - timedelta(days=1)
            
            month_assignments = assignments_qs.filter(
                assignment_date__gte=month_start,
                assignment_date__lte=month_end
            )
            
            month_total = month_assignments.count()
            month_completed = month_assignments.filter(status='completed').count()
            month_active_employees = employees_qs.filter(
                availability_status='active',
                created_at__lte=month_end
            ).count()
            
            productivity = (month_completed / month_total * 100) if month_total > 0 else 0
            attendance = (month_active_employees / total_employees * 100) if total_employees > 0 else 0
            
            monthly_trends.append({
                'month': month_abbr[month_start.month],
                'productivity': round(productivity, 2),
                'attendance': round(attendance, 2),
                'quality': round((productivity + attendance) / 2, 2),
                'task_completion': round(productivity, 2),
                'active_employees': month_active_employees
            })
        
        # Department performance
        departments = Department.objects.filter(status='active')
        if department_id:
            departments = departments.filter(id=department_id)
        
        dept_performance = []
        for dept in departments:
            dept_employees = employees_qs.filter(department=dept)
            dept_assignments = assignments_qs.filter(department=dept)
            
            dept_total = dept_assignments.count()
            dept_completed = dept_assignments.filter(status='completed').count()
            dept_pending = dept_assignments.filter(status='scheduled').count()
            
            completion_rate = (dept_completed / dept_total * 100) if dept_total > 0 else 0
            
            dept_performance.append({
                'department': dept.name,
                'department_id': dept.id,
                'performance': round(completion_rate, 2),
                'employees': dept_employees.count(),
                'active_employees': dept_employees.filter(availability_status='active').count(),
                'tasks_completed': dept_completed,
                'tasks_pending': dept_pending,
                'avg_completion_rate': round(completion_rate, 2)
            })
        
        # Task status distribution
        task_statuses = assignments_qs.values('status').annotate(count=Count('id'))
        total_for_percentage = assignments_qs.count()
        
        task_distribution = []
        for status_data in task_statuses:
            task_distribution.append({
                'status': status_data['status'],
                'count': status_data['count'],
                'percentage': round((status_data['count'] / total_for_percentage * 100), 2) if total_for_percentage > 0 else 0
            })
        
        # Day-off analytics
        dayoff_requests = DayOffChangeRequest.objects.all()
        if department_id:
            dayoff_requests = dayoff_requests.filter(user__department_id=department_id)
        
        total_dayoff = dayoff_requests.count()
        pending_dayoff = dayoff_requests.filter(status='pending').count()
        approved_dayoff = dayoff_requests.filter(status='approved').count()
        rejected_dayoff = dayoff_requests.filter(status='rejected').count()
        cancelled_dayoff = dayoff_requests.filter(status='cancelled').count()
        
        # Group by requested day
        dayoff_by_day = {}
        for day_choice in DayOffChangeRequest.DAY_CHOICES:
            day_value = day_choice[0]
            count = dayoff_requests.filter(requested_day_off=day_value).count()
            if count > 0:
                dayoff_by_day[day_value] = count
        
        # Recent requests
        recent_dayoff = dayoff_requests.order_by('-created_at')[:5]
        recent_requests_data = [{
            'id': req.id,
            'user': req.user.full_name,
            'requested_day': req.requested_day_off,
            'status': req.status,
            'created_at': req.created_at.isoformat()
        } for req in recent_dayoff]
        
        dayoff_analytics = {
            'total_requests': total_dayoff,
            'pending_requests': pending_dayoff,
            'approved_requests': approved_dayoff,
            'rejected_requests': rejected_dayoff,
            'cancelled_requests': cancelled_dayoff,
            'approval_rate': round((approved_dayoff / total_dayoff * 100), 2) if total_dayoff > 0 else 0,
            'rejection_rate': round((rejected_dayoff / total_dayoff * 100), 2) if total_dayoff > 0 else 0,
            'by_day': dayoff_by_day,
            'recent_requests': recent_requests_data
        }
        
        # Workload distribution
        workload_data = []
        for emp in employees_qs.filter(availability_status='active'):
            emp_assignments = assignments_qs.filter(user=emp)
            total_tasks = emp_assignments.count()
            active_tasks = emp_assignments.filter(status='active').count()
            completed_tasks = emp_assignments.filter(status='completed').count()
            
            workload_score = (active_tasks * 2) + (total_tasks * 0.5)
            
            workload_data.append({
                'user_id': emp.id,
                'full_name': emp.full_name,
                'total_tasks': total_tasks,
                'active_tasks': active_tasks,
                'completed_tasks': completed_tasks,
                'workload_score': round(workload_score, 2)
            })
        
        # Compile all data
        dashboard_data = {
            'avg_performance': {
                'value': round(current_completion_rate, 2),
                'trend': calculate_trend_percentage(current_completion_rate, prev_completion_rate),
                'previous_value': round(prev_completion_rate, 2)
            },
            'total_employees': {
                'value': total_employees,
                'trend': 0,  # Can be calculated if we track historical data
                'previous_value': total_employees
            },
            'active_employees': {
                'value': active_employees,
                'trend': calculate_trend_percentage(active_employees, total_employees - active_employees if total_employees > 0 else 0),
                'previous_value': total_employees - active_employees
            },
            'top_performers': {
                'value': top_performers_count,
                'trend': 0,
                'previous_value': top_performers_count
            },
            'task_completion_rate': {
                'value': round(current_completion_rate, 2),
                'trend': calculate_trend_percentage(current_completion_rate, prev_completion_rate),
                'previous_value': round(prev_completion_rate, 2)
            },
            'monthly_trends': monthly_trends,
            'department_performance': dept_performance,
            'task_status_distribution': task_distribution,
            'dayoff_analytics': dayoff_analytics,
            'top_performers_list': top_performers_data[:10],  # Top 10
            'workload_distribution': workload_data,
            'insights': [],  # Will be generated
            'generated_at': timezone.now(),
            'period_start': start_date,
            'period_end': end_date,
            'total_tasks': total_assignments,
            'total_departments': departments.count()
        }
        
        # Generate insights
        dashboard_data['insights'] = generate_insights(dashboard_data)
        
        # Serialize
        serializer = AnalyticsDashboardSerializer(dashboard_data)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_all',
            user=user,
            status_code='200',
            description=f"Viewed analytics dashboard (time_range: {time_range}, department: {department_id or 'all'})",
            request=request,
            response_data={'time_range': time_range, 'department_id': department_id}
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_analytics_dashboard: {error_message}")
        print(traceback.format_exc())
        
        # Log error activity
        Activity.log_activity(
            activity_type='api_error',
            user=user if 'user' in locals() else None,
            status_code='500',
            description=f"Error retrieving analytics dashboard: {error_message}",
            request=request
        )
        
        return Response(
            {
                'error': 'An error occurred while retrieving analytics.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_analytics(request, department_id):
    """Get detailed analytics for a specific department"""
    try:
        user = request.user
        
        # Permission check
        if user.role not in ['admin', 'manager', 'analyst']:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get department
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return Response(
                {'error': 'Department not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        time_range = request.GET.get('time_range', '6months')
        start_date, end_date = get_date_range(time_range)
        
        # Employee metrics
        employees = CustomUser.objects.filter(department=department, role='employee')
        total_employees = employees.count()
        active_employees = employees.filter(availability_status='active').count()
        inactive_employees = total_employees - active_employees
        
        # Task metrics
        assignments = TaskAssignment.objects.filter(
            department=department,
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        total_assignments = assignments.count()
        completed = assignments.filter(status='completed').count()
        active = assignments.filter(status='active').count()
        pending = assignments.filter(status='scheduled').count()
        missed = assignments.filter(status='missed').count()
        
        completion_rate = (completed / total_assignments * 100) if total_assignments > 0 else 0
        
        # Employee performance
        employee_performance = []
        for emp in employees:
            emp_assignments = assignments.filter(user=emp)
            emp_total = emp_assignments.count()
            emp_completed = emp_assignments.filter(status='completed').count()
            emp_missed = emp_assignments.filter(status='missed').count()
            
            if emp_total > 0:
                employee_performance.append({
                    'user_id': emp.id,
                    'full_name': emp.full_name,
                    'email': emp.email,
                    'department': department.name,
                    'tasks_completed': emp_completed,
                    'tasks_active': emp_assignments.filter(status='active').count(),
                    'tasks_missed': emp_missed,
                    'completion_rate': round((emp_completed / emp_total * 100), 2),
                    'performance_score': calculate_performance_score(emp_completed, emp_total, emp_missed)
                })
        
        # Monthly trends
        monthly_trends = []
        for i in range(6, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = end_date
            else:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
                month_end = next_month - timedelta(days=1)
            
            month_assignments = assignments.filter(
                assignment_date__gte=month_start,
                assignment_date__lte=month_end
            )
            
            month_total = month_assignments.count()
            month_completed = month_assignments.filter(status='completed').count()
            
            productivity = (month_completed / month_total * 100) if month_total > 0 else 0
            
            monthly_trends.append({
                'month': month_abbr[month_start.month],
                'productivity': round(productivity, 2),
                'attendance': 100,  # Placeholder
                'quality': round(productivity, 2),
                'task_completion': round(productivity, 2),
                'active_employees': active_employees
            })
        
        # Task distribution
        task_statuses = assignments.values('status').annotate(count=Count('id'))
        task_distribution = []
        for status_data in task_statuses:
            task_distribution.append({
                'status': status_data['status'],
                'count': status_data['count'],
                'percentage': round((status_data['count'] / total_assignments * 100), 2) if total_assignments > 0 else 0
            })
        
        dept_data = {
            'department_id': department.id,
            'department_name': department.name,
            'status': department.status,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'total_tasks_assigned': total_assignments,
            'completed_tasks': completed,
            'active_tasks': active,
            'pending_tasks': pending,
            'missed_tasks': missed,
            'completion_rate': round(completion_rate, 2),
            'average_performance_score': round(sum(emp['performance_score'] for emp in employee_performance) / len(employee_performance), 2) if employee_performance else 0,
            'employee_performance': employee_performance,
            'monthly_trends': monthly_trends,
            'task_distribution': task_distribution
        }
        
        serializer = DepartmentAnalyticsSerializer(dept_data)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_department',
            user=user,
            status_code='200',
            description=f"Viewed analytics for department: {department.name}",
            request=request,
            related_department_id=department_id
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_department_analytics: {error_message}")
        print(traceback.format_exc())
        
        return Response(
            {'error': 'An error occurred while retrieving department analytics.', 'detail': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analytics(request, user_id):
    """Get detailed analytics for a specific user"""
    try:
        current_user = request.user
        
        # Permission check
        if current_user.role not in ['admin', 'manager', 'analyst'] and current_user.id != user_id:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        time_range = request.GET.get('time_range', '6months')
        start_date, end_date = get_date_range(time_range)
        
        # Task metrics
        assignments = TaskAssignment.objects.filter(
            user=target_user,
            assignment_date__gte=start_date,
            assignment_date__lte=end_date
        )
        
        total_tasks = assignments.count()
        completed = assignments.filter(status='completed').count()
        active = assignments.filter(status='active').count()
        scheduled = assignments.filter(status='scheduled').count()
        missed = assignments.filter(status='missed').count()
        cancelled = assignments.filter(status='cancelled').count()
        
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
        performance_score = calculate_performance_score(completed, total_tasks, missed)
        
        # On-time completion (tasks completed before end_time)
        on_time_completed = assignments.filter(
            status='completed',
            actual_end_time__lte=F('end_time')
        ).count()
        on_time_rate = (on_time_completed / completed * 100) if completed > 0 else 0
        
        # Day-off requests
        dayoff_requests = DayOffChangeRequest.objects.filter(user=target_user)
        total_dayoff = dayoff_requests.count()
        pending_dayoff = dayoff_requests.filter(status='pending').count()
        approved_dayoff = dayoff_requests.filter(status='approved').count()
        
        # Recent tasks
        recent_tasks = []
        for task in assignments.order_by('-created_at')[:5]:
            recent_tasks.append({
                'id': task.id,
                'task_name': task.task.name,
                'status': task.status,
                'start_time': task.start_time.isoformat(),
                'end_time': task.end_time.isoformat()
            })
        
        # Recent completions
        recent_completions = []
        for task in assignments.filter(status='completed').order_by('-actual_end_time')[:5]:
            recent_completions.append({
                'id': task.id,
                'task_name': task.task.name,
                'completed_at': task.actual_end_time.isoformat() if task.actual_end_time else None
            })
        
        # Monthly performance
        monthly_performance = []
        for i in range(6, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                month_end = end_date
            else:
                next_month = (month_start + timedelta(days=32)).replace(day=1)
                month_end = next_month - timedelta(days=1)
            
            month_assignments = assignments.filter(
                assignment_date__gte=month_start,
                assignment_date__lte=month_end
            )
            
            month_total = month_assignments.count()
            month_completed = month_assignments.filter(status='completed').count()
            
            productivity = (month_completed / month_total * 100) if month_total > 0 else 0
            
            monthly_performance.append({
                'month': month_abbr[month_start.month],
                'productivity': round(productivity, 2),
                'attendance': 100,
                'quality': round(productivity, 2),
                'task_completion': round(productivity, 2),
                'active_employees': 1
            })
        
        user_data = {
            'user_id': target_user.id,
            'full_name': target_user.full_name,
            'email': target_user.email,
            'role': target_user.role,
            'department': target_user.department.name if target_user.department else None,
            'status': target_user.status,
            'day_off': target_user.day_off,
            'total_tasks': total_tasks,
            'completed_tasks': completed,
            'active_tasks': active,
            'scheduled_tasks': scheduled,
            'missed_tasks': missed,
            'cancelled_tasks': cancelled,
            'completion_rate': round(completion_rate, 2),
            'performance_score': performance_score,
            'on_time_completion_rate': round(on_time_rate, 2),
            'total_dayoff_requests': total_dayoff,
            'pending_dayoff_requests': pending_dayoff,
            'approved_dayoff_requests': approved_dayoff,
            'recent_tasks': recent_tasks,
            'recent_completions': recent_completions,
            'monthly_performance': monthly_performance
        }
        
        serializer = UserAnalyticsSerializer(user_data)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_user',
            user=current_user,
            status_code='200',
            description=f"Viewed analytics for user: {target_user.full_name}",
            request=request,
            related_user_id=user_id
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_user_analytics: {error_message}")
        print(traceback.format_exc())
        
        return Response(
            {'error': 'An error occurred while retrieving user analytics.', 'detail': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_overview(request):
    """Get high-level system overview metrics"""
    try:
        user = request.user
        
        # Permission check
        if user.role not in ['admin', 'manager', 'analyst']:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate metrics
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # System totals
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(availability_status='active').count()
        total_departments = Department.objects.count()
        active_departments = Department.objects.filter(status='active').count()
        total_tasks = Task.objects.count()
        active_task_types = Task.objects.filter(status='active').count()
        
        # Assignment metrics
        all_assignments = TaskAssignment.objects.all()
        total_assignments = all_assignments.count()
        active_assignments = all_assignments.filter(status='active').count()
        completed_assignments = all_assignments.filter(status='completed').count()
        pending_assignments = all_assignments.filter(status='scheduled').count()
        
        # Performance
        overall_completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        
        # Day-off requests
        total_dayoff = DayOffChangeRequest.objects.count()
        pending_dayoff = DayOffChangeRequest.objects.filter(status='pending').count()
        
        # Recent activity
        tasks_today = TaskAssignment.objects.filter(
            status='completed',
            actual_end_time__date=today
        ).count()
        
        tasks_week = TaskAssignment.objects.filter(
            status='completed',
            actual_end_time__date__gte=week_start
        ).count()
        
        tasks_month = TaskAssignment.objects.filter(
            status='completed',
            actual_end_time__date__gte=month_start
        ).count()
        
        overview_data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_departments': total_departments,
            'active_departments': active_departments,
            'total_tasks': total_tasks,
            'active_task_types': active_task_types,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'completed_assignments': completed_assignments,
            'pending_assignments': pending_assignments,
            'overall_completion_rate': round(overall_completion_rate, 2),
            'average_performance_score': round(overall_completion_rate, 2),  # Simplified
            'total_dayoff_requests': total_dayoff,
            'pending_dayoff_requests': pending_dayoff,
            'tasks_completed_today': tasks_today,
            'tasks_completed_this_week': tasks_week,
            'tasks_completed_this_month': tasks_month,
            'generated_at': timezone.now()
        }
        
        serializer = SystemOverviewSerializer(overview_data)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_organization',
            user=user,
            status_code='200',
            description="Viewed system overview analytics",
            request=request
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_system_overview: {error_message}")
        print(traceback.format_exc())
        
        return Response(
            {'error': 'An error occurred while retrieving system overview.', 'detail': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )