# activityApp/serializers.py

from rest_framework import serializers
from .models import Activity, ActivitySummary
from django.contrib.auth import get_user_model

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for activity logs"""
    class Meta:
        model = User
        fields = ['id', 'full_name', 'work_mail_address', 'role']


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model"""
    user_details = UserBasicSerializer(source='user', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_code_display', read_only=True)
    is_success = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id',
            'activity_type',
            'activity_type_display',
            'user',
            'user_details',
            'status_code',
            'status_display',
            'description',
            'ip_address',
            'device_type',
            'browser',
            'operating_system',
            'request_method',
            'endpoint',
            'related_user_id',
            'related_department_id',
            'created_at',
            'duration_ms',
            'is_success',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'user_details',
            'activity_type_display',
            'status_display',
            'is_success',
        ]


class ActivityDetailSerializer(serializers.ModelSerializer):
    """Detailed activity serializer including request/response data"""
    user_details = UserBasicSerializer(source='user', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_code_display', read_only=True)
    is_success = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ActivityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating activity logs"""
    class Meta:
        model = Activity
        fields = [
            'activity_type',
            'user',
            'status_code',
            'description',
            'ip_address',
            'user_agent',
            'device_type',
            'browser',
            'operating_system',
            'request_method',
            'endpoint',
            'request_data',
            'response_data',
            'related_user_id',
            'related_department_id',
            'duration_ms',
        ]


class ActivitySummarySerializer(serializers.ModelSerializer):
    """Serializer for activity summaries"""
    user_details = UserBasicSerializer(source='user', read_only=True)
    
    class Meta:
        model = ActivitySummary
        fields = [
            'id',
            'period_type',
            'period_start',
            'period_end',
            'user',
            'user_details',
            'activity_type',
            'total_count',
            'success_count',
            'error_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActivityStatsSerializer(serializers.Serializer):
    """Serializer for activity statistics"""
    total_activities = serializers.IntegerField()
    successful_activities = serializers.IntegerField()
    failed_activities = serializers.IntegerField()
    success_rate = serializers.FloatField()
    
    # By activity type
    activities_by_type = serializers.DictField(child=serializers.IntegerField())
    
    # By status code
    activities_by_status = serializers.DictField(child=serializers.IntegerField())
    
    # By device type
    activities_by_device = serializers.DictField(child=serializers.IntegerField())
    
    # By time period
    activities_by_date = serializers.ListField()
    
    # Top users
    top_users = serializers.ListField()


class ActivityFilterSerializer(serializers.Serializer):
    """Serializer for activity filtering parameters"""
    activity_type = serializers.ChoiceField(
        choices=Activity.ACTIVITY_TYPE_CHOICES,
        required=False,
        allow_null=True
    )
    user_id = serializers.IntegerField(required=False, allow_null=True)
    status_code = serializers.ChoiceField(
        choices=Activity.STATUS_CHOICES,
        required=False,
        allow_null=True
    )
    device_type = serializers.CharField(required=False, allow_null=True)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_null=True)