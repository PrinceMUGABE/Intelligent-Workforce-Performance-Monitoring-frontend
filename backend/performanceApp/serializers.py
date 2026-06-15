from rest_framework import serializers
from django.db.models import Avg, Count, Q, F, Sum, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from userApp.models import CustomUser
from taskApp.models import Task
from taskAssignmentApp.models import TaskAssignment
from activityApp.models import Activity
from departmentApp.models import Department


class UserPerformanceSerializer(serializers.Serializer):
    """Serializer for individual user performance metrics"""
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()
    work_mail_address = serializers.CharField()
    role = serializers.CharField()
    department_id = serializers.IntegerField(allow_null=True)
    department_name = serializers.CharField(allow_null=True)
    
    # Task metrics
    total_assigned_tasks = serializers.IntegerField(default=0)
    completed_tasks = serializers.IntegerField(default=0)
    active_tasks = serializers.IntegerField(default=0)
    scheduled_tasks = serializers.IntegerField(default=0)
    missed_tasks = serializers.IntegerField(default=0)
    overdue_tasks = serializers.IntegerField(default=0)
    cancelled_tasks = serializers.IntegerField(default=0)
    
    # Performance scores
    task_completion_rate = serializers.FloatField(default=0)
    productivity_score = serializers.FloatField(default=0)
    on_time_completion_rate = serializers.FloatField(default=0)
    
    # Time metrics
    avg_completion_time_hours = serializers.FloatField(default=0)
    total_work_hours = serializers.FloatField(default=0)
    
    # Activity metrics (for admin/analyst)
    total_activities = serializers.IntegerField(default=0)
    recent_activities = serializers.IntegerField(default=0)
    activity_types = serializers.DictField(default=dict)
    
    # Trends
    performance_trend = serializers.CharField(default='stable')
    comparison_to_dept_avg = serializers.FloatField(default=0)
    
    # Period
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    class Meta:
        fields = '__all__'


class DepartmentPerformanceSerializer(serializers.Serializer):
    """Serializer for department-level performance metrics"""
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    employee_count = serializers.IntegerField(default=0)
    
    # Department metrics
    total_assigned_tasks = serializers.IntegerField(default=0)
    completed_tasks = serializers.IntegerField(default=0)
    active_tasks = serializers.IntegerField(default=0)
    missed_tasks = serializers.IntegerField(default=0)
    
    # Department scores
    avg_task_completion_rate = serializers.FloatField(default=0)
    avg_productivity_score = serializers.FloatField(default=0)
    avg_on_time_completion_rate = serializers.FloatField(default=0)
    
    # Top performers
    top_performers = serializers.ListField(child=serializers.DictField(), default=list)
    
    class Meta:
        fields = '__all__'


class OrganizationPerformanceSerializer(serializers.Serializer):
    """Serializer for organization-wide performance metrics"""
    total_employees = serializers.IntegerField(default=0)
    total_departments = serializers.IntegerField(default=0)
    total_tasks_assigned = serializers.IntegerField(default=0)
    total_tasks_completed = serializers.IntegerField(default=0)
    total_active_tasks = serializers.IntegerField(default=0)
    total_missed_tasks = serializers.IntegerField(default=0)
    
    # Overall scores
    overall_completion_rate = serializers.FloatField(default=0)
    overall_productivity_score = serializers.FloatField(default=0)
    
    # Department breakdown
    department_performance = DepartmentPerformanceSerializer(many=True, default=list)
    
    # Top employees
    top_employees = UserPerformanceSerializer(many=True, default=list)
    
    class Meta:
        fields = '__all__'


class PerformanceTrendSerializer(serializers.Serializer):
    """Serializer for performance trends over time"""
    date = serializers.DateField()
    completed_tasks = serializers.IntegerField(default=0)
    completion_rate = serializers.FloatField(default=0)
    productivity_score = serializers.FloatField(default=0)
    
    class Meta:
        fields = '__all__'