# analyticApp/serializers.py

from rest_framework import serializers
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from userApp.models import CustomUser
from departmentApp.models import Department
from taskApp.models import Task
from taskAssignmentApp.models import TaskAssignment
from requestApp.models import DayOffChangeRequest


class PerformanceMetricSerializer(serializers.Serializer):
    """Serializer for individual performance metrics"""
    value = serializers.FloatField()
    trend = serializers.FloatField()
    previous_value = serializers.FloatField(required=False)
    change = serializers.FloatField(required=False)


class MonthlyTrendSerializer(serializers.Serializer):
    """Serializer for monthly trend data"""
    month = serializers.CharField()
    productivity = serializers.FloatField()
    attendance = serializers.FloatField()
    quality = serializers.FloatField()
    task_completion = serializers.FloatField()
    active_employees = serializers.IntegerField()


class DepartmentPerformanceSerializer(serializers.Serializer):
    """Serializer for department performance data"""
    department = serializers.CharField()
    department_id = serializers.IntegerField()
    performance = serializers.FloatField()
    employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    tasks_pending = serializers.IntegerField()
    avg_completion_rate = serializers.FloatField()


class UserPerformanceSummarySerializer(serializers.Serializer):
    """Serializer for individual user performance summary"""
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.CharField()
    department = serializers.CharField()
    tasks_completed = serializers.IntegerField()
    tasks_active = serializers.IntegerField()
    tasks_missed = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    performance_score = serializers.FloatField()


class TaskStatusDistributionSerializer(serializers.Serializer):
    """Serializer for task status distribution"""
    status = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class DayOffAnalyticsSerializer(serializers.Serializer):
    """Serializer for day-off analytics"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    rejected_requests = serializers.IntegerField()
    cancelled_requests = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    rejection_rate = serializers.FloatField()
    by_day = serializers.DictField()
    recent_requests = serializers.ListField()


class WorkloadDistributionSerializer(serializers.Serializer):
    """Serializer for workload distribution"""
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    active_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    workload_score = serializers.FloatField()


class TimeSeriesDataSerializer(serializers.Serializer):
    """Serializer for time series data"""
    date = serializers.DateField()
    value = serializers.FloatField()
    label = serializers.CharField(required=False)


class InsightSerializer(serializers.Serializer):
    """Serializer for system insights"""
    type = serializers.ChoiceField(choices=['success', 'warning', 'info', 'error'])
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.ChoiceField(choices=['high', 'medium', 'low'])
    created_at = serializers.DateTimeField()


class AnalyticsDashboardSerializer(serializers.Serializer):
    """Main serializer for analytics dashboard data"""
    # Key metrics
    avg_performance = PerformanceMetricSerializer()
    total_employees = PerformanceMetricSerializer()
    active_employees = PerformanceMetricSerializer()
    top_performers = PerformanceMetricSerializer()
    task_completion_rate = PerformanceMetricSerializer()
    
    # Trends
    monthly_trends = MonthlyTrendSerializer(many=True)
    
    # Department data
    department_performance = DepartmentPerformanceSerializer(many=True)
    
    # Task distribution
    task_status_distribution = TaskStatusDistributionSerializer(many=True)
    
    # Day-off analytics
    dayoff_analytics = DayOffAnalyticsSerializer()
    
    # Top performers
    top_performers_list = UserPerformanceSummarySerializer(many=True)
    
    # Workload distribution
    workload_distribution = WorkloadDistributionSerializer(many=True)
    
    # Insights
    insights = InsightSerializer(many=True)
    
    # Metadata
    generated_at = serializers.DateTimeField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_tasks = serializers.IntegerField()
    total_departments = serializers.IntegerField()


class DepartmentAnalyticsSerializer(serializers.Serializer):
    """Detailed analytics for a specific department"""
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    status = serializers.CharField()
    
    # Employee metrics
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    inactive_employees = serializers.IntegerField()
    
    # Task metrics
    total_tasks_assigned = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    active_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    missed_tasks = serializers.IntegerField()
    
    # Performance metrics
    completion_rate = serializers.FloatField()
    average_performance_score = serializers.FloatField()
    
    # Employee performance list
    employee_performance = UserPerformanceSummarySerializer(many=True)
    
    # Monthly trends
    monthly_trends = MonthlyTrendSerializer(many=True)
    
    # Task status distribution
    task_distribution = TaskStatusDistributionSerializer(many=True)


class UserAnalyticsSerializer(serializers.Serializer):
    """Detailed analytics for a specific user"""
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.CharField()
    role = serializers.CharField()
    department = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    day_off = serializers.CharField(allow_null=True)
    
    # Task metrics
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    active_tasks = serializers.IntegerField()
    scheduled_tasks = serializers.IntegerField()
    missed_tasks = serializers.IntegerField()
    cancelled_tasks = serializers.IntegerField()
    
    # Performance metrics
    completion_rate = serializers.FloatField()
    performance_score = serializers.FloatField()
    on_time_completion_rate = serializers.FloatField()
    
    # Day-off requests
    total_dayoff_requests = serializers.IntegerField()
    pending_dayoff_requests = serializers.IntegerField()
    approved_dayoff_requests = serializers.IntegerField()
    
    # Recent activity
    recent_tasks = serializers.ListField()
    recent_completions = serializers.ListField()
    
    # Monthly performance
    monthly_performance = MonthlyTrendSerializer(many=True)


class SystemOverviewSerializer(serializers.Serializer):
    """High-level system overview metrics"""
    # System totals
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    active_departments = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    active_task_types = serializers.IntegerField()
    
    # Current assignments
    total_assignments = serializers.IntegerField()
    active_assignments = serializers.IntegerField()
    completed_assignments = serializers.IntegerField()
    pending_assignments = serializers.IntegerField()
    
    # Performance summary
    overall_completion_rate = serializers.FloatField()
    average_performance_score = serializers.FloatField()
    
    # Day-off summary
    total_dayoff_requests = serializers.IntegerField()
    pending_dayoff_requests = serializers.IntegerField()
    
    # Recent activity summary
    tasks_completed_today = serializers.IntegerField()
    tasks_completed_this_week = serializers.IntegerField()
    tasks_completed_this_month = serializers.IntegerField()
    
    # Generated timestamp
    generated_at = serializers.DateTimeField()