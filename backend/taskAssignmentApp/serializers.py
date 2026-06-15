from rest_framework import serializers
from .models import TaskAssignment, TaskAssignmentTemplate, TaskOverload
from django.contrib.auth import get_user_model
from userApp.models import CustomUser
from taskApp.models import Task
from departmentApp.models import Department
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class LocalUserSerializer(serializers.ModelSerializer):
    """Local serializer for user data - avoids circular imports"""
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'work_mail_address', 
            'full_name', 'role', 'department_id', 'status'
        ]
        read_only_fields = fields


class LocalTaskSerializer(serializers.ModelSerializer):
    """Local serializer for task data - FIXED: imports from taskApp.models"""
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'status', 'created_at']
        read_only_fields = fields


class LocalDepartmentSerializer(serializers.ModelSerializer):
    """Local serializer for department data"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'status']
        read_only_fields = fields


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for task assignments - FIXED: proper field mappings"""
    user_details = LocalUserSerializer(source='user', read_only=True)
    task_details = LocalTaskSerializer(source='task', read_only=True)
    department_details = LocalDepartmentSerializer(source='department', read_only=True)
    assigned_by_details = LocalUserSerializer(source='assigned_by', read_only=True)
    modified_by_details = LocalUserSerializer(source='modified_by', read_only=True)
    
    # Calculated fields
    duration_minutes = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    actual_duration_minutes = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    can_start = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    time_until_start_minutes = serializers.SerializerMethodField()
    time_until_end_minutes = serializers.SerializerMethodField()
    time_until_end_days = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'user', 'user_details',
            'task', 'task_details',
            'department', 'department_details',
            'assignment_date', 'start_time', 'end_time',
            'actual_start_time', 'actual_end_time',
            'status', 'priority', 'sequence_order',
            'is_modified', 'modification_reason',
            'assigned_by', 'assigned_by_details',
            'modified_by', 'modified_by_details',
            'notes', 'reminder_sent', 'reminder_sent_at',
            'duration_minutes', 'duration_days', 'actual_duration_minutes',
            'is_current', 'can_start', 'is_overdue',
            'time_until_start_minutes', 'time_until_end_minutes', 'time_until_end_days',
            'created_at', 'updated_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'actual_start_time', 'actual_end_time',
            'reminder_sent', 'reminder_sent_at',
            'created_at', 'updated_at', 'metadata'
        ]
        extra_kwargs = {
            'sequence_order': {'required': False, 'default': 1},
            'assignment_date': {'required': False},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def get_duration_minutes(self, obj):
        return obj.duration_minutes if hasattr(obj, 'duration_minutes') else 0
    
    def get_duration_days(self, obj):
        return obj.duration_days if hasattr(obj, 'duration_days') else 0
    
    def get_actual_duration_minutes(self, obj):
        return obj.actual_duration_minutes if hasattr(obj, 'actual_duration_minutes') else None
    
    def get_is_current(self, obj):
        return obj.is_current if hasattr(obj, 'is_current') else False
    
    def get_can_start(self, obj):
        return obj.can_start if hasattr(obj, 'can_start') else False
    
    def get_is_overdue(self, obj):
        return obj.is_overdue if hasattr(obj, 'is_overdue') else False
    
    def get_time_until_start_minutes(self, obj):
        return obj.time_until_start_minutes if hasattr(obj, 'time_until_start_minutes') else 0
    
    def get_time_until_end_minutes(self, obj):
        return obj.time_until_end_minutes if hasattr(obj, 'time_until_end_minutes') else 0
    
    def get_time_until_end_days(self, obj):
        return obj.time_until_end_days if hasattr(obj, 'time_until_end_days') else 0
    
    def validate(self, data):
        """Additional validation for assignments"""
        # Ensure start_time and end_time are provided
        if not data.get('start_time') and not self.instance:
            raise serializers.ValidationError({'start_time': 'Start time is required.'})
        
        if not data.get('end_time') and not self.instance:
            raise serializers.ValidationError({'end_time': 'End time is required.'})
        
        # Validate time range if both are provided
        start_time = data.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = data.get('end_time', getattr(self.instance, 'end_time', None))
        
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time.'
                })
        
        return data


class TaskAssignmentModifySerializer(serializers.Serializer):
    """Serializer for modifying task assignments"""
    assignment_id = serializers.IntegerField(required=True)
    new_task_id = serializers.IntegerField(required=False, allow_null=True)
    new_start_time = serializers.DateTimeField(required=False, allow_null=True)
    new_end_time = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TaskAssignmentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for task assignment templates - FIXED: removed non-existent fields"""
    task_details = LocalTaskSerializer(source='task', read_only=True)
    department_details = LocalDepartmentSerializer(source='department', read_only=True)
    created_by_details = LocalUserSerializer(source='created_by', read_only=True)
    specific_users_details = LocalUserSerializer(source='specific_users', many=True, read_only=True)
    
    class Meta:
        model = TaskAssignmentTemplate
        fields = [
            'id', 'name', 'task', 'task_details',
            'department', 'department_details',
            'start_time', 'duration_minutes', 'priority',
            'is_recurring', 'recurrence_days',
            'assign_to_all_department', 'specific_users', 'specific_users_details',
            'is_active', 'created_by', 'created_by_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'name': {'required': True},
            'task': {'required': True},
            'department': {'required': True},
            'start_time': {'required': True},
            'duration_minutes': {'required': True, 'min_value': 1},
        }


class TaskOverloadSerializer(serializers.ModelSerializer):
    """Serializer for task overloads - FIXED: field name consistency"""
    task_details = LocalTaskSerializer(source='task', read_only=True)
    department_details = LocalDepartmentSerializer(source='department', read_only=True)
    created_by_details = LocalUserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = TaskOverload
        fields = [
            'id', 'task', 'task_details', 'department', 'department_details',
            'overload_date', 'additional_employees_needed',
            'time_slot_start', 'time_slot_end', 'reason',
            'is_resolved', 'resolved_at',
            'created_by', 'created_by_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'resolved_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'overload_date': {'required': True},
            'additional_employees_needed': {'required': True, 'min_value': 1},
            'reason': {'required': True},
        }


class BulkAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk task assignments"""
    task_id = serializers.IntegerField(required=True)
    assignment_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'], default='medium')
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Assignment targets (choose one)
    department_id = serializers.IntegerField(required=False, allow_null=True)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of specific user IDs to assign"
    )
    assign_to_all_employees = serializers.BooleanField(default=False, required=False)
    assign_to_all_users = serializers.BooleanField(default=False, required=False)
    
    def validate(self, data):
        """Validate that at least one target is specified"""
        # Create list of boolean values for each target type
        targets = []
        if data.get('department_id') is not None:
            targets.append('department_id')
        if data.get('user_ids') is not None and len(data.get('user_ids', [])) > 0:
            targets.append('user_ids')
        if data.get('assign_to_all_employees') is True:
            targets.append('assign_to_all_employees')
        if data.get('assign_to_all_users') is True:
            targets.append('assign_to_all_users')
        
        if not targets:
            raise serializers.ValidationError(
                "Must specify at least one target: department_id, user_ids, assign_to_all_employees, or assign_to_all_users"
            )
        
        # Check for mutually exclusive targets
        if len(targets) > 1:
            raise serializers.ValidationError(
                f"Please specify only one target type. Found multiple: {', '.join(targets)}"
            )
        
        return data


class DepartmentBulkAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning tasks to an entire department"""
    task_id = serializers.IntegerField(required=True)
    department_id = serializers.IntegerField(required=True)
    assignment_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'], default='medium')
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    exclude_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Optional: List of user IDs to exclude from department assignment"
    )


class UserListBulkAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning tasks to a list of specific users"""
    task_id = serializers.IntegerField(required=True)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1,
        help_text="List of user IDs to assign the task to"
    )
    assignment_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=True)
    priority = serializers.ChoiceField(choices=['low', 'medium', 'high', 'urgent'], default='medium')
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)