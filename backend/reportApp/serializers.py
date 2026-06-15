# reportApp/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta


class ReportFilterSerializer(serializers.Serializer):
    """Base serializer for report filters"""
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    department_id = serializers.IntegerField(required=False, allow_null=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, allow_null=True)
    
    def validate(self, attrs):
        """Validate date range"""
        # Validate date range
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] > attrs['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        
        return attrs


class UserReportSerializer(serializers.Serializer):
    """Serializer for user data in reports"""
    id = serializers.IntegerField()
    phone_number = serializers.CharField()
    email = serializers.EmailField()
    work_mail_address = serializers.CharField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    department_id = serializers.IntegerField(allow_null=True)
    department_name = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    availability_status = serializers.CharField()
    day_off = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    is_active = serializers.BooleanField()


class DepartmentReportSerializer(serializers.Serializer):
    """Serializer for department data in reports"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    employee_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    created_by_name = serializers.CharField(allow_null=True)


class TaskReportSerializer(serializers.Serializer):
    """Serializer for task data in reports"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    created_by_name = serializers.CharField(allow_null=True)
    total_assignments = serializers.IntegerField()
    completed_assignments = serializers.IntegerField()
    active_assignments = serializers.IntegerField()
    scheduled_assignments = serializers.IntegerField()
    missed_assignments = serializers.IntegerField()


class TaskAssignmentReportSerializer(serializers.Serializer):
    """Serializer for task assignment data in reports"""
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_email = serializers.CharField()
    task_id = serializers.IntegerField()
    task_name = serializers.CharField()
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    assignment_date = serializers.DateField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    actual_start_time = serializers.DateTimeField(allow_null=True)
    actual_end_time = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    priority = serializers.CharField()
    sequence_order = serializers.IntegerField()
    duration_minutes = serializers.FloatField()
    duration_days = serializers.IntegerField()
    actual_duration_minutes = serializers.FloatField(allow_null=True)
    is_modified = serializers.BooleanField()
    assigned_by_name = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class DayOffRequestReportSerializer(serializers.Serializer):
    """Serializer for day-off request data in reports"""
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_email = serializers.CharField()
    current_day_off = serializers.CharField()
    requested_day_off = serializers.CharField()
    effective_from = serializers.DateField()
    status = serializers.CharField()
    reason = serializers.CharField()
    approved_by_name = serializers.CharField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    approval_notes = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class ActivityReportSerializer(serializers.Serializer):
    """Serializer for activity data in reports"""
    id = serializers.IntegerField()
    activity_type = serializers.CharField()
    user_id = serializers.IntegerField(allow_null=True)
    user_name = serializers.CharField(allow_null=True)
    status_code = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    ip_address = serializers.CharField(allow_null=True)
    device_type = serializers.CharField(allow_null=True)
    browser = serializers.CharField(allow_null=True)
    request_method = serializers.CharField(allow_null=True)
    endpoint = serializers.CharField(allow_null=True)
    from_status = serializers.CharField(allow_null=True)
    to_status = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class ReportSummarySerializer(serializers.Serializer):
    """Serializer for report summary data"""
    total_count = serializers.IntegerField()
    filters_applied = serializers.DictField()
    date_range = serializers.DictField()
    generated_at = serializers.DateTimeField()
    generated_by = serializers.CharField()
    report_type = serializers.CharField()


class UserReportResponseSerializer(serializers.Serializer):
    """Complete user report response"""
    summary = ReportSummarySerializer()
    users = UserReportSerializer(many=True)
    statistics = serializers.DictField()


class DepartmentReportResponseSerializer(serializers.Serializer):
    """Complete department report response"""
    summary = ReportSummarySerializer()
    departments = DepartmentReportSerializer(many=True)
    statistics = serializers.DictField()


class TaskReportResponseSerializer(serializers.Serializer):
    """Complete task report response"""
    summary = ReportSummarySerializer()
    tasks = TaskReportSerializer(many=True)
    statistics = serializers.DictField()


class TaskAssignmentReportResponseSerializer(serializers.Serializer):
    """Complete task assignment report response"""
    summary = ReportSummarySerializer()
    assignments = TaskAssignmentReportSerializer(many=True)
    statistics = serializers.DictField()


class DayOffReportResponseSerializer(serializers.Serializer):
    """Complete day-off report response"""
    summary = ReportSummarySerializer()
    day_off_requests = DayOffRequestReportSerializer(many=True)
    statistics = serializers.DictField()


class ActivityReportResponseSerializer(serializers.Serializer):
    """Complete activity report response"""
    summary = ReportSummarySerializer()
    activities = ActivityReportSerializer(many=True)
    statistics = serializers.DictField()


class PerformanceReportResponseSerializer(serializers.Serializer):
    """Complete performance report response"""
    summary = ReportSummarySerializer()
    performance_data = serializers.DictField()
    statistics = serializers.DictField()


class OrganizationReportResponseSerializer(serializers.Serializer):
    """Complete organization report response"""
    summary = ReportSummarySerializer()
    organization_data = serializers.DictField()
    statistics = serializers.DictField()