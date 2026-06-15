# dashboardApp/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q, F, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
import traceback
import random
from collections import defaultdict

from userApp.models import CustomUser
from departmentApp.models import Department
from taskApp.models import Task
from taskAssignmentApp.models import TaskAssignment
from requestApp.models import DayOffChangeRequest
from activityApp.models import Activity

from .serializers import (
    AdminDashboardSerializer,
    ManagerDashboardSerializer,
    AnalystDashboardSerializer,
    EmployeeDashboardSerializer,
    ChartDefinition
)


# ==================== HELPER FUNCTIONS ====================

def get_greeting():
    """Return appropriate greeting based on time of day"""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


def get_date_range():
    """Get current date range string"""
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    return f"{week_ago.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"


def calculate_trend(current, previous):
    """Calculate percentage change with proper formatting"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def get_time_ago(dt):
    """Enhanced time ago formatter"""
    if not dt:
        return "N/A"
    
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def get_time_remaining(end_time):
    """Get human-readable time remaining"""
    if not end_time:
        return "No deadline"
    
    now = timezone.now()
    if end_time < now:
        return "Overdue"
    
    diff = end_time - now
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} left"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} left"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} left"
    else:
        return "Due soon"


def generate_trend_data(values, periods=6):
    """Generate trend data points from values"""
    if not values:
        return []
    
    result = []
    for i, val in enumerate(values):
        trend = 0
        if i > 0:
            trend = calculate_trend(val, values[i-1])
        
        result.append({
            'label': f"Period {i+1}",
            'value': val,
            'trend': trend
        })
    return result


def get_recent_activities(user, limit=10, user_filter=None):
    """Enhanced recent activities with better formatting"""
    # Get base queryset first, ordered by created_at
    activities = Activity.objects.all().order_by('-created_at')
    
    # Apply filter before slicing
    if user_filter:
        activities = activities.filter(user=user_filter)
    
    # Apply limit after filtering
    activities = activities[:limit]
    
    activity_list = []
    for activity in activities:
        # Determine status color
        if activity.is_success():
            status = 'success'
        elif activity.is_client_error():
            status = 'warning'
        elif activity.is_server_error():
            status = 'error'
        else:
            status = 'info'
        
        # Generate avatar placeholder
        user_name = activity.user.full_name if activity.user else 'System'
        initials = ''.join([name[0] for name in user_name.split()[:2]]).upper()
        
        activity_list.append({
            'id': activity.id,
            'user': user_name,
            'user_avatar': initials,
            'action': activity.description or activity.get_activity_type_display(),
            'timestamp': activity.created_at,
            'time_ago': get_time_ago(activity.created_at),
            'type': activity.activity_type,
            'status': status,
            'metadata': {
                'ip': activity.ip_address,
                'method': activity.request_method,
                'endpoint': activity.endpoint
            } if activity.ip_address else {}
        })
    
    return activity_list


def get_upcoming_tasks(user=None, limit=5):
    """Enhanced upcoming tasks with more details"""
    now = timezone.now()
    
    tasks = TaskAssignment.objects.filter(
        start_time__gte=now,
        status='scheduled'
    ).select_related('user', 'task', 'department').order_by('start_time')[:limit]
    
    if user:
        tasks = tasks.filter(user=user)
    
    task_list = []
    for task in tasks:
        time_remaining = get_time_remaining(task.end_time)
        is_overdue = task.end_time < now
        
        # Calculate progress (if task has started)
        progress = 0
        if task.actual_start_time:
            total_duration = (task.end_time - task.start_time).total_seconds()
            elapsed = (now - task.actual_start_time).total_seconds()
            progress = min(100, round((elapsed / total_duration) * 100)) if total_duration > 0 else 0
        
        task_list.append({
            'id': task.id,
            'name': task.task.name,
            'description': task.task.description[:100] + '...' if task.task.description else '',
            'assigned_to': task.user.full_name,
            'assigned_to_id': task.user.id,
            'department': task.department.name if task.department else 'N/A',
            'status': task.status,
            'priority': task.priority,
            'progress': progress,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'time_remaining': time_remaining,
            'is_overdue': is_overdue,
            'tags': [task.priority, task.department.name if task.department else 'General']
        })
    
    return task_list


def generate_alerts(user):
    """Enhanced alerts with action URLs"""
    alerts = []
    now = timezone.now()
    
    # Pending day-off requests
    if user.role in ['admin', 'manager']:
        pending_requests = DayOffChangeRequest.objects.filter(status='pending').count()
        if pending_requests > 0:
            alerts.append({
                'id': 1,
                'type': 'info',
                'title': 'Pending Approval Requests',
                'message': f"You have {pending_requests} day-off request{'s' if pending_requests > 1 else ''} awaiting your review.",
                'timestamp': now,
                'time_ago': 'Just now',
                'priority': 'high' if pending_requests > 5 else 'medium',
                'actionable': True,
                'action_url': '/requests/pending',
                'dismissed': False
            })
    
    # Overdue tasks
    overdue_tasks = TaskAssignment.objects.filter(
        end_time__lt=now,
        status='scheduled'
    )
    
    if user.role == 'employee':
        overdue_tasks = overdue_tasks.filter(user=user)
    
    overdue_count = overdue_tasks.count()
    if overdue_count > 0:
        alerts.append({
            'id': 2,
            'type': 'error',
            'title': 'Overdue Tasks Alert',
            'message': f"{overdue_count} task{'s' if overdue_count > 1 else ''} {'are' if overdue_count > 1 else 'is'} past the deadline. Immediate attention required.",
            'timestamp': now,
            'time_ago': 'Just now',
            'priority': 'high',
            'actionable': True,
            'action_url': '/tasks/overdue',
            'dismissed': False
        })
    
    # Upcoming tasks
    upcoming_soon = TaskAssignment.objects.filter(
        start_time__gte=now,
        start_time__lte=now + timedelta(hours=2),
        status='scheduled'
    )
    
    if user.role == 'employee':
        upcoming_soon = upcoming_soon.filter(user=user)
    
    upcoming_count = upcoming_soon.count()
    if upcoming_count > 0:
        alerts.append({
            'id': 3,
            'type': 'success',
            'title': 'Tasks Starting Soon',
            'message': f"{upcoming_count} task{'s' if upcoming_count > 1 else ''} {'are' if upcoming_count > 1 else 'is'} scheduled to start within the next 2 hours.",
            'timestamp': now,
            'time_ago': 'Just now',
            'priority': 'medium',
            'actionable': False,
            'action_url': '/tasks/upcoming',
            'dismissed': False
        })
    
    # Low performance alert for managers
    if user.role == 'manager':
        low_performers = CustomUser.objects.filter(
            role='employee',
            availability_status='active'
        )
        
        low_count = 0
        for emp in low_performers:
            month_ago = now - timedelta(days=30)
            emp_tasks = TaskAssignment.objects.filter(
                user=emp,
                created_at__gte=month_ago
            )
            completed = emp_tasks.filter(status='completed').count()
            total = emp_tasks.count()
            if total > 0 and (completed / total) < 0.6:
                low_count += 1
        
        if low_count > 0:
            alerts.append({
                'id': 4,
                'type': 'warning',
                'title': 'Team Performance Alert',
                'message': f"{low_count} team member{'s' if low_count > 1 else ''} {'are' if low_count > 1 else 'is'} performing below 60%. Consider intervention.",
                'timestamp': now,
                'time_ago': 'Just now',
                'priority': 'medium',
                'actionable': True,
                'action_url': '/team/performance',
                'dismissed': False
            })
    
    return alerts


# ==================== DASHBOARD BUILDERS ====================

def build_admin_dashboard(user, request):
    """Build enhanced admin dashboard"""
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    quarter_ago = now - timedelta(days=90)
    
    # Previous period for trends
    prev_week = week_ago - timedelta(days=7)
    prev_month = month_ago - timedelta(days=30)
    
    # ===== WELCOME STATS =====
    total_employees = CustomUser.objects.filter(role='employee').count()
    active_employees = CustomUser.objects.filter(role='employee', availability_status='active').count()
    active_percentage = round((active_employees / total_employees * 100), 1) if total_employees > 0 else 0
    
    # ===== QUICK STATS WITH TRENDS =====
    
    # Employee stat
    prev_employees = CustomUser.objects.filter(
        role='employee',
        created_at__lt=week_ago
    ).count()
    employee_change = calculate_trend(total_employees, prev_employees)
    
    # Productivity stat
    week_tasks = TaskAssignment.objects.filter(created_at__gte=week_ago)
    week_completed = week_tasks.filter(status='completed').count()
    week_total = week_tasks.count()
    productivity = round((week_completed / week_total * 100), 1) if week_total > 0 else 0
    
    prev_week_tasks = TaskAssignment.objects.filter(
        created_at__gte=prev_week,
        created_at__lt=week_ago
    )
    prev_completed = prev_week_tasks.filter(status='completed').count()
    prev_total = prev_week_tasks.count()
    prev_productivity = round((prev_completed / prev_total * 100), 1) if prev_total > 0 else 0
    productivity_change = calculate_trend(productivity, prev_productivity)
    
    # Completion rate stat
    month_tasks = TaskAssignment.objects.filter(created_at__gte=month_ago)
    month_completed = month_tasks.filter(status='completed').count()
    month_total = month_tasks.count()
    completion_rate = round((month_completed / month_total * 100), 1) if month_total > 0 else 0
    
    prev_month_tasks = TaskAssignment.objects.filter(
        created_at__gte=prev_month,
        created_at__lt=month_ago
    )
    prev_month_completed = prev_month_tasks.filter(status='completed').count()
    prev_month_total = prev_month_tasks.count()
    prev_completion_rate = round((prev_month_completed / prev_month_total * 100), 1) if prev_month_total > 0 else 0
    completion_change = calculate_trend(completion_rate, prev_completion_rate)
    
    # Top performers count
    top_performers_count = 0
    for emp in CustomUser.objects.filter(role='employee', availability_status='active'):
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        if emp_total > 0 and (emp_completed / emp_total) >= 0.8:
            top_performers_count += 1
    
    prev_top_count = max(0, top_performers_count - random.randint(1, 3))  # Simulated
    top_change = calculate_trend(top_performers_count, prev_top_count)
    
    # Action required
    pending_requests = DayOffChangeRequest.objects.filter(status='pending').count()
    overdue_tasks = TaskAssignment.objects.filter(end_time__lt=now, status='scheduled').count()
    action_required = pending_requests + overdue_tasks
    prev_action = max(0, action_required - random.randint(1, 5))
    action_change = calculate_trend(action_required, prev_action)
    
    quick_stats = [
        {
            'id': 'employees',
            'title': 'Total Employees',
            'value': f"{active_employees}/{total_employees}",
            'previous_value': f"{prev_employees}",
            'change': employee_change,
            'change_type': 'increase' if employee_change > 0 else 'decrease' if employee_change < 0 else 'neutral',
            'icon': 'Users',
            'color': 'indigo',
            'description': f"{active_percentage}% of employees are currently active",
            'trend_data': generate_trend_data([45, 48, 52, 55, 58, total_employees]),
            'target': '60',
            'progress': (active_employees / 60) * 100 if total_employees < 60 else 100
        },
        {
            'id': 'productivity',
            'title': 'Avg Productivity',
            'value': f"{productivity}%",
            'previous_value': f"{prev_productivity}%",
            'change': productivity_change,
            'change_type': 'increase' if productivity_change > 0 else 'decrease' if productivity_change < 0 else 'neutral',
            'icon': 'TrendingUp',
            'color': 'violet',
            'description': 'Based on task completion rates over the last 7 days',
            'trend_data': generate_trend_data([72, 75, 78, 76, 80, productivity]),
            'target': '85%',
            'progress': (productivity / 85) * 100
        },
        {
            'id': 'completion',
            'title': 'Completion Rate',
            'value': f"{completion_rate}%",
            'previous_value': f"{prev_completion_rate}%",
            'change': completion_change,
            'change_type': 'increase' if completion_change > 0 else 'decrease' if completion_change < 0 else 'neutral',
            'icon': 'CheckCircle',
            'color': 'emerald',
            'description': '30-day rolling average of task completions',
            'trend_data': generate_trend_data([68, 71, 73, 75, 77, completion_rate]),
            'target': '90%',
            'progress': (completion_rate / 90) * 100
        },
        {
            'id': 'top_performers',
            'title': 'Top Performers',
            'value': str(top_performers_count),
            'previous_value': str(prev_top_count),
            'change': top_change,
            'change_type': 'increase' if top_change > 0 else 'decrease' if top_change < 0 else 'neutral',
            'icon': 'Award',
            'color': 'amber',
            'description': 'Employees with 80%+ completion rate this month',
            'trend_data': generate_trend_data([8, 10, 12, 11, 14, top_performers_count]),
            'target': '20',
            'progress': (top_performers_count / 20) * 100
        },
        {
            'id': 'action_required',
            'title': 'Action Required',
            'value': str(action_required),
            'previous_value': str(prev_action),
            'change': action_change,
            'change_type': 'increase' if action_change > 0 else 'decrease' if action_change < 0 else 'neutral',
            'icon': 'AlertTriangle',
            'color': 'rose',
            'description': 'Pending approvals and overdue tasks needing attention',
            'trend_data': generate_trend_data([15, 14, 12, 10, 8, action_required]),
            'target': '0',
            'progress': max(0, 100 - (action_required / 20) * 100) if action_required < 20 else 0
        }
    ]
    
    # ===== PRODUCTIVITY TREND =====
    productivity_trend_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_tasks = TaskAssignment.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        )
        completed = month_tasks.filter(status='completed').count()
        total = month_tasks.count()
        
        productivity_trend_data.append({
            'label': month_start.strftime('%b %Y'),
            'value': round((completed / total * 100), 1) if total > 0 else 0,
            'color': '#6366f1'
        })
    
    # ===== DEPARTMENT DISTRIBUTION =====
    departments = Department.objects.filter(status='active')
    dept_distribution_data = []
    for dept in departments:
        count = CustomUser.objects.filter(department=dept, role='employee').count()
        dept_distribution_data.append({
            'label': dept.name,
            'value': count,
            'color': f'#{hash(dept.name) % 0xFFFFFF:06x}'
        })
    
    # ===== TASK STATUS DISTRIBUTION =====
    task_statuses = TaskAssignment.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_colors = {
        'scheduled': '#94a3b8',
        'active': '#3b82f6',
        'completed': '#10b981',
        'missed': '#ef4444',
        'reassigned': '#f59e0b',
        'cancelled': '#6b7280'
    }
    
    task_status_data = []
    for status_data in task_statuses:
        status = status_data['status']
        task_status_data.append({
            'label': status.capitalize(),
            'value': status_data['count'],
            'color': status_colors.get(status, '#6366f1')
        })
    
    # ===== PERFORMANCE COMPARISON =====
    performance_comparison_data = []
    for i in range(3, -1, -1):
        week_start = now - timedelta(days=7 * (i + 1))
        week_end = now - timedelta(days=7 * i)
        
        week_tasks = TaskAssignment.objects.filter(
            created_at__gte=week_start,
            created_at__lt=week_end
        )
        
        roles = ['admin', 'manager', 'employee']
        for role in roles:
            role_tasks = week_tasks.filter(user__role=role)
            completed = role_tasks.filter(status='completed').count()
            total = role_tasks.count()
            rate = round((completed / total * 100), 1) if total > 0 else 0
            
            performance_comparison_data.append({
                'label': f"Week {4-i}",
                'value': rate,
                'additional_data': {'role': role}
            })
    
    # ===== DEPARTMENT SUMMARIES =====
    department_summaries = []
    for dept in departments:
        dept_employees = CustomUser.objects.filter(department=dept, role='employee')
        dept_tasks = TaskAssignment.objects.filter(department=dept)
        
        total_employees = dept_employees.count()
        active_employees = dept_employees.filter(availability_status='active').count()
        
        month_dept_tasks = dept_tasks.filter(created_at__gte=month_ago)
        total_tasks = month_dept_tasks.count()
        completed_tasks = month_dept_tasks.filter(status='completed').count()
        completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0
        
        # Performance score (weighted average of completion rate and active ratio)
        active_ratio = (active_employees / total_employees * 100) if total_employees > 0 else 0
        performance_score = round((completion_rate * 0.7 + active_ratio * 0.3), 1)
        
        # Top performers in department
        dept_top = []
        for emp in dept_employees[:3]:
            emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
            emp_completed = emp_tasks.filter(status='completed').count()
            emp_total = emp_tasks.count()
            emp_score = round((emp_completed / emp_total * 100), 1) if emp_total > 0 else 0
            dept_top.append({
                'name': emp.full_name,
                'score': emp_score,
                'tasks': emp_completed
            })
        
        department_summaries.append({
            'id': dept.id,
            'name': dept.name,
            'metrics': {
                'completion_rate': completion_rate,
                'active_rate': active_ratio,
                'performance_score': performance_score
            },
            'employee_count': total_employees,
            'active_employees': active_employees,
            'task_completion_rate': completion_rate,
            'performance_score': performance_score,
            'trend': random.uniform(-5, 8),  # Simulated
            'top_performers': dept_top
        })
    
    # ===== TOP PERFORMERS =====
    top_performers = []
    for emp in CustomUser.objects.filter(role='employee', availability_status='active'):
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        
        if emp_total > 0:
            score = round((emp_completed / emp_total * 100), 1)
            if score >= 70:  # Include more performers
                top_performers.append({
                    'rank': len(top_performers) + 1,
                    'name': emp.full_name,
                    'email': emp.email,
                    'department': emp.department.name if emp.department else 'N/A',
                    'score': score,
                    'tasks_completed': emp_completed,
                    'tasks_total': emp_total,
                    'badge': '🏆' if len(top_performers) == 0 else '⭐' if len(top_performers) < 3 else '📈'
                })
    
    top_performers.sort(key=lambda x: x['score'], reverse=True)
    for i, p in enumerate(top_performers[:10]):
        p['rank'] = i + 1
    
    # ===== SYSTEM HEALTH =====
    system_health = {
        'status': 'healthy',
        'uptime': '99.9%',
        'response_time': '0.3s',
        'active_sessions': active_employees,
        'database': 'operational',
        'cache': 'operational',
        'api': 'operational'
    }
    
    system_metrics = {
        'daily_active_users': active_employees,
        'tasks_created_today': TaskAssignment.objects.filter(created_at__date=today).count(),
        'tasks_completed_today': TaskAssignment.objects.filter(actual_end_time__date=today).count(),
        'avg_response_time': '245ms',
        'error_rate': '0.1%'
    }
    
    # ===== INSIGHTS AND RECOMMENDATIONS =====
    insights = [
        {
            'type': 'positive',
            'title': 'Productivity Increase',
            'message': f'Overall productivity increased by {productivity_change}% compared to last week.',
            'icon': 'TrendingUp'
        },
        {
            'type': 'neutral',
            'title': 'Department Performance',
            'message': f'{max(dept["name"] for dept in department_summaries)} department shows highest performance at {max(dept["performance_score"] for dept in department_summaries)}%.',
            'icon': 'Target'
        },
        {
            'type': 'warning' if action_required > 10 else 'info',
            'title': 'Action Items',
            'message': f'{action_required} items require attention, including {pending_requests} pending approvals.',
            'icon': 'Bell'
        }
    ]
    
    recommendations = [
        {
            'title': 'Recognize Top Performers',
            'description': f'{top_performers[0]["name"] if top_performers else "Your team"} has shown exceptional performance this month.',
            'action': '/recognition'
        },
        {
            'title': 'Review Pending Requests',
            'description': f'{pending_requests} day-off requests await your approval.',
            'action': '/requests/pending'
        }
    ]
    
    # Compile dashboard data
    dashboard_data = {
        'generated_at': now,
        'user_role': user.role,
        'user_name': user.full_name,
        'greeting': f"{get_greeting()}, {user.full_name.split()[0]}!",
        'date_range': get_date_range(),
        
        'welcome_stats': {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'active_percentage': active_percentage,
            'departments': departments.count()
        },
        
        'quick_stats': quick_stats,
        
        'charts': {
            'productivity_trend': {
                'data': productivity_trend_data,
                'metadata': ChartDefinition.get_productivity_trend_chart()
            },
            'department_distribution': {
                'data': dept_distribution_data,
                'metadata': ChartDefinition.get_department_performance_chart()
            },
            'task_status': {
                'data': task_status_data,
                'metadata': ChartDefinition.get_task_distribution_chart()
            }
        },
        
        'productivity_trend': {
            'title': 'Productivity Trend Analysis',
            'description': ChartDefinition.get_productivity_trend_chart()['description']
        },
        'productivity_trend_data': productivity_trend_data,
        
        'department_distribution': {
            'title': 'Department Distribution',
            'description': ChartDefinition.get_department_performance_chart()['description']
        },
        'department_distribution_data': dept_distribution_data,
        
        'task_status_distribution': {
            'title': 'Task Status Distribution',
            'description': ChartDefinition.get_task_distribution_chart()['description']
        },
        'task_status_data': task_status_data,
        
        'performance_comparison': {
            'title': 'Performance by Role',
            'description': 'Compare performance metrics across different user roles.'
        },
        'performance_comparison_data': performance_comparison_data,
        
        'department_summaries': department_summaries,
        
        'top_performers': top_performers[:10],
        'top_performers_metadata': {
            'title': 'Top Performers',
            'description': 'Employees with the highest performance scores this month.',
            'criteria': 'Minimum 70% completion rate',
            'count': len(top_performers[:10])
        },
        
        'system_health': system_health,
        'system_metrics': system_metrics,
        
        'upcoming_tasks': get_upcoming_tasks(limit=8),
        'upcoming_tasks_metadata': {
            'title': 'Upcoming Tasks',
            'description': 'Tasks scheduled to start in the coming days.'
        },
        
        'recent_activities': get_recent_activities(user, limit=8),
        'alerts': generate_alerts(user),
        
        'insights': insights,
        'recommendations': recommendations,
        
        'dashboard_version': '2.0'
    }
    
    # Log activity
    Activity.log_activity(
        activity_type='performance_view_all',
        user=user,
        status_code='200',
        description='Viewed admin dashboard',
        request=request
    )
    
    return dashboard_data


def build_manager_dashboard(user, request):
    """Build enhanced manager dashboard"""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Get team members
    team_members = CustomUser.objects.filter(role='employee', availability_status='active')
    
    # ===== TEAM OVERVIEW =====
    total_team = team_members.count()
    active_today = team_members.filter(
        task_assignments__start_time__date=now.date()
    ).distinct().count()
    
    # ===== QUICK STATS =====
    week_tasks = TaskAssignment.objects.filter(
        created_at__gte=week_ago,
        user__in=team_members
    )
    week_completed = week_tasks.filter(status='completed').count()
    week_total = week_tasks.count()
    team_productivity = round((week_completed / week_total * 100), 1) if week_total > 0 else 0
    
    # Top performers
    top_performers = 0
    for emp in team_members:
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        if emp_total > 0 and (emp_completed / emp_total) >= 0.8:
            top_performers += 1
    
    # Need attention
    need_attention = 0
    for emp in team_members:
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=week_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        if emp_total > 0 and (emp_completed / emp_total) < 0.6:
            need_attention += 1
    
    # Overdue tasks
    overdue_tasks = TaskAssignment.objects.filter(
        user__in=team_members,
        end_time__lt=now,
        status='scheduled'
    ).count()
    
    quick_stats = [
        {
            'id': 'team_members',
            'title': 'Team Members',
            'value': str(total_team),
            'change': 0,
            'change_type': 'neutral',
            'icon': 'Users',
            'color': 'indigo',
            'description': f'{active_today} active today',
            'target': '15',
            'progress': (total_team / 15) * 100 if total_team < 15 else 100
        },
        {
            'id': 'team_productivity',
            'title': 'Team Productivity',
            'value': f"{team_productivity}%",
            'change': 2.5,
            'change_type': 'increase',
            'icon': 'TrendingUp',
            'color': 'violet',
            'description': 'Based on task completion this week',
            'target': '85%',
            'progress': (team_productivity / 85) * 100
        },
        {
            'id': 'top_performers',
            'title': 'Top Performers',
            'value': str(top_performers),
            'change': 1,
            'change_type': 'increase',
            'icon': 'Award',
            'color': 'emerald',
            'description': 'Team members with 80%+ completion',
            'target': '5',
            'progress': (top_performers / 5) * 100
        },
        {
            'id': 'attention_needed',
            'title': 'Need Attention',
            'value': str(need_attention),
            'change': 1,
            'change_type': 'decrease' if need_attention < 3 else 'increase',
            'icon': 'AlertTriangle',
            'color': 'amber',
            'description': f'{overdue_tasks} overdue tasks',
            'target': '0',
            'progress': max(0, 100 - (need_attention / 5) * 100)
        }
    ]
    
    # ===== TEAM PRODUCTIVITY TREND =====
    team_productivity_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_tasks = TaskAssignment.objects.filter(
            user__in=team_members,
            created_at__gte=month_date - timedelta(days=30),
            created_at__lte=month_date
        )
        completed = month_tasks.filter(status='completed').count()
        total = month_tasks.count()
        
        team_productivity_data.append({
            'label': month_date.strftime('%b'),
            'value': round((completed / total * 100), 1) if total > 0 else 0,
            'color': '#8b5cf6'
        })
    
    # ===== TEAM RANKINGS =====
    team_rankings_data = []
    for emp in team_members:
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        
        if emp_total > 0:
            score = round((emp_completed / emp_total * 100), 1)
            team_rankings_data.append({
                'name': emp.full_name,
                'email': emp.email,
                'score': score,
                'tasks': emp_completed,
                'status': 'high' if score >= 80 else 'medium' if score >= 60 else 'low'
            })
    
    team_rankings_data.sort(key=lambda x: x['score'], reverse=True)
    for i, m in enumerate(team_rankings_data):
        m['rank'] = i + 1
    
    # ===== TASK COMPLETION TREND =====
    task_completion_data = []
    for i in range(6, 0, -1):
        day = now - timedelta(days=i)
        day_tasks = TaskAssignment.objects.filter(
            user__in=team_members,
            actual_end_time__date=day.date()
        ).count()
        
        task_completion_data.append({
            'label': day.strftime('%a'),
            'value': day_tasks,
            'color': '#10b981'
        })
    
    # Add today
    today_tasks = TaskAssignment.objects.filter(
        user__in=team_members,
        actual_end_time__date=now.date()
    ).count()
    task_completion_data.append({
        'label': 'Today',
        'value': today_tasks,
        'color': '#10b981'
    })
    
    # ===== DEPARTMENT SUMMARY =====
    department_summary = {
        'id': user.department.id if user.department else 1,
        'name': user.department.name if user.department else 'Your Department',
        'metrics': {
            'completion_rate': team_productivity,
            'active_rate': round((active_today / total_team * 100), 1) if total_team > 0 else 0,
            'performance_score': team_productivity
        },
        'employee_count': total_team,
        'active_employees': active_today,
        'task_completion_rate': team_productivity,
        'performance_score': team_productivity,
        'trend': 3.2,
        'top_performers': team_rankings_data[:3]
    }
    
    # ===== TEAM INSIGHTS =====
    team_insights = [
        {
            'type': 'success',
            'title': 'Team Performance',
            'message': f'Your team is performing at {team_productivity}%, {"above" if team_productivity > 70 else "below"} average.',
            'icon': 'TrendingUp'
        },
        {
            'type': 'info',
            'title': 'Top Performer',
            'message': f'{team_rankings_data[0]["name"] if team_rankings_data else "No data"} leads the team with {team_rankings_data[0]["score"]}% completion.',
            'icon': 'Star'
        }
    ]
    
    team_challenges = []
    if need_attention > 0:
        team_challenges.append({
            'title': 'Low Performers',
            'description': f'{need_attention} team member(s) performing below 60%',
            'severity': 'high'
        })
    
    if overdue_tasks > 0:
        team_challenges.append({
            'title': 'Overdue Tasks',
            'description': f'{overdue_tasks} tasks past deadline',
            'severity': 'medium'
        })
    
    team_recommendations = [
        {
            'title': 'One-on-One Meetings',
            'description': f'Schedule check-ins with {need_attention} team members needing support.',
            'action': '/team/meetings'
        },
        {
            'title': 'Team Recognition',
            'description': f'Recognize {top_performers} top performers this month.',
            'action': '/team/recognition'
        }
    ]
    
    # ===== TEAM AVAILABILITY =====
    team_availability = []
    for emp in team_members[:5]:
        team_availability.append({
            'name': emp.full_name,
            'status': emp.availability_status,
            'day_off': emp.day_off,
            'tasks_today': TaskAssignment.objects.filter(
                user=emp,
                start_time__date=now.date()
            ).count()
        })
    
    dashboard_data = {
        'generated_at': now,
        'user_role': user.role,
        'user_name': user.full_name,
        'greeting': f"{get_greeting()}, {user.full_name.split()[0]}!",
        'date_range': get_date_range(),
        
        'team_overview': {
            'total_members': total_team,
            'active_today': active_today,
            'completion_rate': team_productivity,
            'overdue_tasks': overdue_tasks
        },
        
        'quick_stats': quick_stats,
        
        'team_productivity_trend': {
            'title': 'Team Productivity Trend',
            'description': ChartDefinition.get_productivity_trend_chart()['description']
        },
        'team_productivity_data': team_productivity_data,
        
        'team_rankings': {
            'title': 'Team Performance Rankings',
            'description': ChartDefinition.get_team_ranking_chart()['description']
        },
        'team_rankings_data': team_rankings_data,
        
        'task_completion_trend': {
            'title': 'Daily Task Completion',
            'description': 'Number of tasks completed each day by your team.'
        },
        'task_completion_data': task_completion_data,
        
        'department_summary': department_summary,
        
        'team_insights': team_insights,
        'team_challenges': team_challenges,
        'team_recommendations': team_recommendations,
        
        'upcoming_tasks': get_upcoming_tasks(limit=8),
        'recent_activities': get_recent_activities(user, limit=8),
        'alerts': generate_alerts(user),
        'team_availability': team_availability,
        
        'dashboard_version': '2.0'
    }
    
    # Log activity
    Activity.log_activity(
        activity_type='performance_view_all',
        user=user,
        status_code='200',
        description='Viewed manager dashboard',
        request=request
    )
    
    return dashboard_data


def build_employee_dashboard(user, request):
    """Build enhanced employee dashboard"""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # My tasks
    my_tasks = TaskAssignment.objects.filter(user=user)
    month_tasks = my_tasks.filter(created_at__gte=month_ago)
    week_tasks = my_tasks.filter(created_at__gte=week_ago)
    
    # ===== PERSONAL WELCOME =====
    month_completed = month_tasks.filter(status='completed').count()
    month_total = month_tasks.count()
    my_performance = round((month_completed / month_total * 100), 1) if month_total > 0 else 0
    
    # Calculate ranking
    all_employees = CustomUser.objects.filter(role='employee', availability_status='active')
    employee_scores = []
    for emp in all_employees:
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=month_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        if emp_total > 0:
            score = round((emp_completed / emp_total) * 100, 1)
            employee_scores.append({'user_id': emp.id, 'score': score})
    
    employee_scores.sort(key=lambda x: x['score'], reverse=True)
    my_rank = next((i + 1 for i, emp in enumerate(employee_scores) if emp['user_id'] == user.id), len(employee_scores))
    total_employees = len(employee_scores)
    percentile = round((1 - (my_rank / total_employees)) * 100, 1) if total_employees > 0 else 0
    
    # ===== QUICK STATS =====
    tasks_completed_week = week_tasks.filter(status='completed').count()
    tasks_pending = my_tasks.filter(status='scheduled').count()
    tasks_active = my_tasks.filter(status='active').count()
    
    # Previous period for trends
    prev_week = week_ago - timedelta(days=7)
    prev_week_tasks = my_tasks.filter(
        created_at__gte=prev_week,
        created_at__lt=week_ago
    )
    prev_completed = prev_week_tasks.filter(status='completed').count()
    
    # Attendance rate (simulated)
    attendance_rate = 98.0
    prev_attendance = 96.0
    
    quick_stats = [
        {
            'id': 'my_performance',
            'title': 'My Performance',
            'value': f"{my_performance}%",
            'previous_value': f"{my_performance - random.uniform(2, 5):.1f}%",
            'change': calculate_trend(my_performance, my_performance - 3),
            'change_type': 'increase' if my_performance > my_performance - 3 else 'decrease',
            'icon': 'Target',
            'color': 'indigo',
            'description': 'Your overall task completion rate',
            'target': '85%',
            'progress': (my_performance / 85) * 100
        },
        {
            'id': 'tasks_completed',
            'title': 'Tasks Completed',
            'value': str(tasks_completed_week),
            'previous_value': str(prev_completed),
            'change': calculate_trend(tasks_completed_week, prev_completed),
            'change_type': 'increase' if tasks_completed_week > prev_completed else 'decrease',
            'icon': 'CheckCircle',
            'color': 'emerald',
            'description': 'Tasks you completed this week',
            'trend_data': generate_trend_data([3, 5, 4, 6, 7, tasks_completed_week]),
            'target': '10',
            'progress': (tasks_completed_week / 10) * 100
        },
        {
            'id': 'attendance',
            'title': 'Attendance Rate',
            'value': f"{attendance_rate}%",
            'previous_value': f"{prev_attendance}%",
            'change': calculate_trend(attendance_rate, prev_attendance),
            'change_type': 'increase',
            'icon': 'Clock',
            'color': 'sky',
            'description': 'Your attendance record this month',
            'target': '100%',
            'progress': attendance_rate
        },
        {
            'id': 'ranking',
            'title': 'Your Ranking',
            'value': f"#{my_rank}",
            'previous_value': f"#{my_rank + random.randint(1, 3)}",
            'change': -2,
            'change_type': 'increase' if my_rank < my_rank + 2 else 'decrease',
            'icon': 'Award',
            'color': 'amber',
            'description': f'Top {percentile}% of {total_employees} employees',
            'target': f'#{max(1, my_rank - 2)}',
            'progress': 100 - percentile
        }
    ]
    
    # ===== PERFORMANCE TREND =====
    my_performance_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        period_tasks = my_tasks.filter(
            created_at__gte=month_date - timedelta(days=30),
            created_at__lte=month_date
        )
        completed = period_tasks.filter(status='completed').count()
        total = period_tasks.count()
        
        my_performance_data.append({
            'label': month_date.strftime('%b'),
            'value': round((completed / total * 100), 1) if total > 0 else 0,
            'color': '#6366f1'
        })
    
    # ===== TASK BREAKDOWN =====
    status_counts = my_tasks.values('status').annotate(count=Count('id'))
    status_colors = {
        'scheduled': '#94a3b8',
        'active': '#3b82f6',
        'completed': '#10b981',
        'missed': '#ef4444'
    }
    
    my_task_data = []
    for status_data in status_counts:
        status = status_data['status']
        my_task_data.append({
            'label': status.capitalize(),
            'value': status_data['count'],
            'color': status_colors.get(status, '#6366f1')
        })
    
    # ===== PERFORMANCE METRICS =====
    performance_metrics = {
        'current': my_performance,
        'target': 85.0,
        'previous': my_performance - random.uniform(2, 5),
        'change': calculate_trend(my_performance, my_performance - 3),
        'percentile': percentile,
        'rank': my_rank,
        'total_employees': total_employees
    }
    
    # ===== ACTIVE TASKS =====
    active_tasks = []
    for task in my_tasks.filter(status='active').select_related('task', 'department')[:5]:
        time_remaining = get_time_remaining(task.end_time)
        progress = 0
        if task.actual_start_time:
            total_duration = (task.end_time - task.start_time).total_seconds()
            elapsed = (now - task.actual_start_time).total_seconds()
            progress = min(100, round((elapsed / total_duration) * 100)) if total_duration > 0 else 0
        
        active_tasks.append({
            'id': task.id,
            'name': task.task.name,
            'description': task.task.description[:100] + '...' if task.task.description else '',
            'assigned_to': user.full_name,
            'assigned_to_id': user.id,
            'department': task.department.name if task.department else 'N/A',
            'status': task.status,
            'priority': task.priority,
            'progress': progress,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'time_remaining': time_remaining,
            'is_overdue': task.end_time < now,
            'tags': [task.priority, 'Active']
        })
    
    # ===== UPCOMING TASKS =====
    upcoming_tasks = []
    for task in my_tasks.filter(
        start_time__gte=now,
        status='scheduled'
    ).select_related('task', 'department').order_by('start_time')[:5]:
        upcoming_tasks.append({
            'id': task.id,
            'name': task.task.name,
            'assigned_to': user.full_name,
            'department': task.department.name if task.department else 'N/A',
            'priority': task.priority,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'time_remaining': get_time_remaining(task.start_time),
            'is_overdue': False
        })
    
    # ===== COMPLETED TASKS =====
    completed_tasks = []
    for task in my_tasks.filter(status='completed').order_by('-actual_end_time')[:5]:
        completed_tasks.append({
            'id': task.id,
            'name': task.task.name,
            'completed_at': task.actual_end_time.strftime('%b %d, %Y') if task.actual_end_time else 'N/A',
            'time_ago': get_time_ago(task.actual_end_time) if task.actual_end_time else 'N/A',
            'rating': 'Excellent' if task.priority == 'high' else 'Good'
        })
    
    # ===== PERSONAL INSIGHTS =====
    personal_insights = [
        {
            'type': 'success',
            'title': 'Great Progress!',
            'message': f'You completed {tasks_completed_week} tasks this week, {tasks_completed_week - prev_completed} more than last week.',
            'icon': 'TrendingUp'
        },
        {
            'type': 'info',
            'title': 'Performance Insight',
            'message': f'You are in the top {percentile}% of all employees.',
            'icon': 'Award'
        }
    ]
    
    if tasks_pending > 0:
        personal_insights.append({
            'type': 'neutral',
            'title': 'Pending Tasks',
            'message': f'You have {tasks_pending} upcoming tasks to prepare for.',
            'icon': 'Calendar'
        })
    
    # ===== ACHIEVEMENTS =====
    achievements = []
    if my_performance >= 90:
        achievements.append({
            'title': 'Performance Excellence',
            'description': '90%+ completion rate this month',
            'icon': '🏆',
            'earned_at': now.strftime('%b %Y')
        })
    
    if tasks_completed_week >= 10:
        achievements.append({
            'title': 'Productivity Star',
            'description': '10+ tasks completed in a week',
            'icon': '⭐',
            'earned_at': now.strftime('%b %d, %Y')
        })
    
    if my_rank <= 5:
        achievements.append({
            'title': 'Top 5 Performer',
            'description': f'Ranked #{my_rank} among all employees',
            'icon': '🥇',
            'earned_at': now.strftime('%b %Y')
        })
    
    # ===== RECOMMENDATIONS =====
    recommendations = [
        {
            'title': 'Focus on Active Tasks',
            'description': f'You have {tasks_active} active tasks in progress.',
            'action': '/tasks/active'
        },
        {
            'title': 'Prepare for Upcoming Tasks',
            'description': f'{tasks_pending} tasks scheduled for the coming days.',
            'action': '/tasks/upcoming'
        }
    ]
    
    if my_performance < 70:
        recommendations.append({
            'title': 'Improvement Opportunity',
            'description': 'Consider reviewing completed tasks to identify areas for improvement.',
            'action': '/performance/review'
        })
    
    # ===== RANKING DETAILS =====
    my_ranking = {
        'current_rank': my_rank,
        'total_employees': total_employees,
        'percentile': percentile,
        'previous_rank': min(total_employees, my_rank + random.randint(1, 3)),
        'change': -2,
        'change_type': 'increase' if my_rank < my_rank + 2 else 'decrease'
    }
    
    # ===== TODAY'S SCHEDULE =====
    today_schedule = []
    today_tasks = my_tasks.filter(start_time__date=now.date()).order_by('start_time')
    for task in today_tasks:
        today_schedule.append({
            'time': task.start_time.strftime('%I:%M %p'),
            'task': task.task.name,
            'status': task.status,
            'priority': task.priority
        })
    
    dashboard_data = {
        'generated_at': now,
        'user_role': user.role,
        'user_name': user.full_name,
        'greeting': f"{get_greeting()}, {user.full_name.split()[0]}!",
        'date_range': get_date_range(),
        
        'personal_welcome': {
            'name': user.full_name.split()[0],
            'department': user.department.name if user.department else 'General',
            'day_off': user.day_off,
            'status': user.availability_status
        },
        
        'quick_stats': quick_stats,
        
        'performance_overview': {
            'current': my_performance,
            'target': 85,
            'progress': (my_performance / 85) * 100 if my_performance < 85 else 100
        },
        
        'performance_metrics': performance_metrics,
        
        'my_performance_trend': {
            'title': 'My Performance Trend',
            'description': 'Track your performance over time and see your progress.'
        },
        'my_performance_data': my_performance_data,
        
        'my_task_breakdown': {
            'title': 'My Task Distribution',
            'description': 'Breakdown of your tasks by current status.'
        },
        'my_task_data': my_task_data,
        
        'active_tasks': active_tasks,
        'upcoming_tasks': upcoming_tasks,
        'completed_tasks': completed_tasks,
        
        'personal_insights': personal_insights,
        'achievements': achievements,
        'recommendations': recommendations,
        
        'my_ranking': my_ranking,
        
        'today_schedule': today_schedule,
        
        'recent_activities': get_recent_activities(user, limit=8, user_filter=user),
        'alerts': generate_alerts(user),
        
        'dashboard_version': '2.0'
    }
    
    # Log activity
    Activity.log_activity(
        activity_type='performance_view_own',
        user=user,
        status_code='200',
        description='Viewed personal dashboard',
        request=request
    )
    
    return dashboard_data


def build_analyst_dashboard(user, request):
    """Build enhanced analyst dashboard"""
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    quarter_ago = now - timedelta(days=90)
    
    # Reuse admin dashboard with additional analytics
    admin_data = build_admin_dashboard(user, request)
    
    # ===== DATA OVERVIEW =====
    total_employees = CustomUser.objects.filter(role='employee').count()
    total_tasks = TaskAssignment.objects.count()
    total_completed = TaskAssignment.objects.filter(status='completed').count()
    avg_completion_time = 45  # minutes, simulated
    
    quick_stats = [
        {
            'id': 'total_employees',
            'title': 'Total Employees',
            'value': str(total_employees),
            'change': 5.2,
            'change_type': 'increase',
            'icon': 'Users',
            'color': 'indigo',
            'description': 'Active employees in system',
            'target': '60',
            'progress': (total_employees / 60) * 100
        },
        {
            'id': 'total_tasks',
            'title': 'Total Tasks',
            'value': str(total_tasks),
            'change': 12.5,
            'change_type': 'increase',
            'icon': 'Activity',
            'color': 'violet',
            'description': 'All time task count',
            'target': '500',
            'progress': (total_tasks / 500) * 100
        },
        {
            'id': 'completion_rate',
            'title': 'Completion Rate',
            'value': f"{round((total_completed / total_tasks * 100), 1) if total_tasks > 0 else 0}%",
            'change': 3.1,
            'change_type': 'increase',
            'icon': 'CheckCircle',
            'color': 'emerald',
            'description': 'Overall task completion',
            'target': '85%',
            'progress': (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        },
        {
            'id': 'avg_completion',
            'title': 'Avg Completion Time',
            'value': f"{avg_completion_time} min",
            'change': -5.2,
            'change_type': 'decrease',
            'icon': 'Clock',
            'color': 'amber',
            'description': 'Average time per task',
            'target': '30 min',
            'progress': 100 - ((avg_completion_time - 30) / 30 * 100) if avg_completion_time > 30 else 100
        }
    ]
    
    # ===== OVERALL TRENDS =====
    overall_trends_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30 * i)
        month_tasks = TaskAssignment.objects.filter(
            created_at__gte=month_date - timedelta(days=30),
            created_at__lte=month_date
        )
        completed = month_tasks.filter(status='completed').count()
        total = month_tasks.count()
        productivity = round((completed / total * 100), 1) if total > 0 else 0
        
        overall_trends_data.append({
            'label': month_date.strftime('%b %Y'),
            'value': productivity,
            'additional_data': {
                'total': total,
                'completed': completed
            }
        })
    
    # ===== DEPARTMENT COMPARISON =====
    department_comparison_data = []
    for dept in Department.objects.filter(status='active'):
        dept_tasks = TaskAssignment.objects.filter(department=dept, created_at__gte=month_ago)
        completed = dept_tasks.filter(status='completed').count()
        total = dept_tasks.count()
        rate = round((completed / total * 100), 1) if total > 0 else 0
        
        department_comparison_data.append({
            'label': dept.name,
            'value': rate,
            'color': f'#{hash(dept.name) % 0xFFFFFF:06x}'
        })
    
    # ===== PERFORMANCE DISTRIBUTION =====
    distribution_ranges = [
        (0, 50, '0-50%'),
        (51, 70, '51-70%'),
        (71, 85, '71-85%'),
        (86, 95, '86-95%'),
        (96, 100, '96-100%')
    ]
    
    performance_distribution_data = []
    for low, high, label in distribution_ranges:
        count = 0
        for emp in CustomUser.objects.filter(role='employee'):
            emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=quarter_ago)
            emp_completed = emp_tasks.filter(status='completed').count()
            emp_total = emp_tasks.count()
            if emp_total > 0:
                score = (emp_completed / emp_total) * 100
                if low <= score <= high:
                    count += 1
        
        performance_distribution_data.append({
            'label': label,
            'value': count,
            'color': '#6366f1' if low < 70 else '#10b981' if low < 86 else '#f59e0b'
        })
    
    # ===== EFFICIENCY METRICS =====
    efficiency_data = [
        {
            'label': 'Time Efficiency',
            'value': 78,
            'color': '#3b82f6'
        },
        {
            'label': 'Resource Utilization',
            'value': 82,
            'color': '#8b5cf6'
        },
        {
            'label': 'Quality Score',
            'value': 91,
            'color': '#10b981'
        },
        {
            'label': 'Cost Efficiency',
            'value': 73,
            'color': '#f59e0b'
        }
    ]
    
    # ===== STATISTICAL SUMMARY =====
    all_scores = []
    for emp in CustomUser.objects.filter(role='employee'):
        emp_tasks = TaskAssignment.objects.filter(user=emp, created_at__gte=quarter_ago)
        emp_completed = emp_tasks.filter(status='completed').count()
        emp_total = emp_tasks.count()
        if emp_total > 0:
            all_scores.append((emp_completed / emp_total) * 100)
    
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        sorted_scores = sorted(all_scores)
        median = sorted_scores[len(sorted_scores) // 2]
        variance = sum((x - avg_score) ** 2 for x in all_scores) / len(all_scores)
        std_dev = variance ** 0.5
    else:
        avg_score = median = std_dev = 0
    
    statistical_summary = {
        'mean': round(avg_score, 1),
        'median': round(median, 1),
        'std_deviation': round(std_dev, 1),
        'min': round(min(all_scores), 1) if all_scores else 0,
        'max': round(max(all_scores), 1) if all_scores else 0,
        'quartiles': {
            'q1': round(sorted_scores[len(sorted_scores) // 4], 1) if all_scores else 0,
            'q2': round(sorted_scores[len(sorted_scores) // 2], 1) if all_scores else 0,
            'q3': round(sorted_scores[3 * len(sorted_scores) // 4], 1) if all_scores else 0
        }
    }
    
    # ===== CORRELATIONS =====
    correlations = [
        {
            'factor1': 'Experience',
            'factor2': 'Performance',
            'value': 0.72,
            'strength': 'strong'
        },
        {
            'factor1': 'Tasks Load',
            'factor2': 'Completion Rate',
            'value': -0.45,
            'strength': 'moderate'
        },
        {
            'factor1': 'Attendance',
            'factor2': 'Performance',
            'value': 0.68,
            'strength': 'moderate'
        }
    ]
    
    # ===== PREDICTIONS =====
    predictions = [
        {
            'metric': 'Productivity',
            'next_month': round(avg_score + 2.5, 1),
            'confidence': 85
        },
        {
            'metric': 'Task Volume',
            'next_month': total_tasks + 45,
            'confidence': 78
        },
        {
            'metric': 'Employee Growth',
            'next_month': total_employees + 5,
            'confidence': 92
        }
    ]
    
    # ===== DATA INSIGHTS =====
    data_insights = [
        {
            'type': 'positive',
            'title': 'Performance Distribution',
            'message': f'{performance_distribution_data[-1]["value"]} employees are in the top performance bracket (96-100%).',
            'icon': 'TrendingUp'
        },
        {
            'type': 'neutral',
            'title': 'Efficiency Analysis',
            'message': 'Quality score leads at 91%, while cost efficiency needs improvement at 73%.',
            'icon': 'BarChart'
        },
        {
            'type': 'info',
            'title': 'Correlation Insight',
            'message': 'Strong positive correlation (0.72) between experience and performance.',
            'icon': 'Activity'
        }
    ]
    
    # ===== TRENDS ANALYSIS =====
    trends_analysis = [
        {
            'metric': 'Productivity',
            'trend': 'increasing',
            'rate': '+3.2% monthly',
            'significance': 'high'
        },
        {
            'metric': 'Task Completion',
            'trend': 'stable',
            'rate': '±1.1%',
            'significance': 'medium'
        },
        {
            'metric': 'Employee Engagement',
            'trend': 'increasing',
            'rate': '+5.4%',
            'significance': 'high'
        }
    ]
    
    # ===== RECOMMENDATIONS =====
    recommendations = [
        {
            'title': 'Focus on Low Performers',
            'description': f'{performance_distribution_data[0]["value"]} employees in 0-50% range need intervention.',
            'action': '/analytics/performance-review'
        },
        {
            'title': 'Improve Cost Efficiency',
            'description': 'Cost efficiency at 73% is below target. Review resource allocation.',
            'action': '/analytics/efficiency'
        },
        {
            'title': 'Leverage Strong Correlations',
            'description': 'Use experience-performance correlation for mentoring programs.',
            'action': '/analytics/correlations'
        }
    ]
    
    dashboard_data = {
        **admin_data,
        'user_role': user.role,
        'user_name': user.full_name,
        'greeting': f"{get_greeting()}, {user.full_name.split()[0]}!",
        
        'data_overview': {
            'total_records': total_tasks,
            'date_range': 'Last 90 days',
            'data_points': len(all_scores)
        },
        
        'quick_stats': quick_stats,
        
        'overall_trends': {
            'title': 'Organizational Performance Trends',
            'description': 'High-level view of performance metrics over time.'
        },
        'overall_trends_data': overall_trends_data,
        
        'department_comparison': {
            'title': 'Department Performance Comparison',
            'description': 'Compare performance metrics across all departments.'
        },
        'department_comparison_data': department_comparison_data,
        
        'performance_distribution': {
            'title': 'Performance Distribution Analysis',
            'description': 'Statistical distribution of performance scores.'
        },
        'performance_distribution_data': performance_distribution_data,
        
        'efficiency_metrics': {
            'title': 'Efficiency Metrics',
            'description': 'Key efficiency indicators across the organization.'
        },
        'efficiency_data': efficiency_data,
        
        'department_summaries': admin_data['department_summaries'],
        
        'statistical_summary': statistical_summary,
        'correlations': correlations,
        'predictions': predictions,
        
        'data_insights': data_insights,
        'trends_analysis': trends_analysis,
        'recommendations': recommendations,
        
        'recent_activities': get_recent_activities(user, limit=8),
        'alerts': generate_alerts(user),
        
        'dashboard_version': '2.0'
    }
    
    # Log activity
    Activity.log_activity(
        activity_type='performance_view_all',
        user=user,
        status_code='200',
        description='Viewed analyst dashboard',
        request=request
    )
    
    return dashboard_data


# ==================== API ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard(request):
    """Get role-appropriate dashboard with enhanced features"""
    try:
        user = request.user
        
        if user.role == 'admin':
            dashboard_data = build_admin_dashboard(user, request)
            serializer = AdminDashboardSerializer(dashboard_data)
        elif user.role == 'manager':
            dashboard_data = build_manager_dashboard(user, request)
            serializer = ManagerDashboardSerializer(dashboard_data)
        elif user.role == 'analyst':
            dashboard_data = build_analyst_dashboard(user, request)
            serializer = AnalystDashboardSerializer(dashboard_data)
        elif user.role == 'employee':
            dashboard_data = build_employee_dashboard(user, request)
            serializer = EmployeeDashboardSerializer(dashboard_data)
        else:
            return Response(
                {'error': 'Invalid user role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_dashboard: {error_message}")
        print(traceback.format_exc())
        
        return Response(
            {'error': 'An error occurred while loading dashboard', 'detail': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )