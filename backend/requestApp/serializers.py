from django.utils import timezone
from rest_framework import serializers
from .models import DayOffChangeRequest
from userApp.models import CustomUser

class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for CustomUser"""
    # For properties that are methods on the model, we need to use serializers.SerializerMethodField
    is_admin = serializers.SerializerMethodField()
    is_manager = serializers.SerializerMethodField()
    is_analyst = serializers.SerializerMethodField()
    is_employee = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'full_name',
            'email',
            'phone_number',
            'role',
            'status',
            'day_off',
            'is_admin',
            'is_manager',
            'is_analyst',
            'is_employee',
            'created_at',
        ]
    
    def get_is_admin(self, obj):
        return obj.is_admin
    
    def get_is_manager(self, obj):
        return obj.is_manager
    
    def get_is_analyst(self, obj):
        return obj.is_analyst
    
    def get_is_employee(self, obj):
        return obj.is_employee


class DayOffChangeRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing day-off change requests (minimal data)"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True, allow_null=True)
    cancelled_by_name = serializers.CharField(source='cancelled_by.full_name', read_only=True, allow_null=True)
    days_until_effective = serializers.ReadOnlyField()
    user_details = UserDetailSerializer(source='user', read_only=True)
    
    class Meta:
        model = DayOffChangeRequest
        fields = [
            'id',
            'user_name',
            'user_email',
            'user_role',
            'reason',
            'current_day_off',
            'requested_day_off',
            'effective_from',
            'days_until_effective',
            'status',
            'approved_by_name',
            'approved_at',
            'approval_notes',
            'cancelled_by_name',
            'cancelled_at',
            'cancellation_reason',
            'created_at',
            'updated_at',
            'user_details',
            'can_be_modified',
            'can_be_deleted'
        ]


class DayOffChangeRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for day-off change requests with full associated data"""
    user = UserDetailSerializer(read_only=True)
    approved_by = UserDetailSerializer(read_only=True, allow_null=True)
    cancelled_by = UserDetailSerializer(read_only=True, allow_null=True)
    
    # Read-only properties
    is_pending = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    is_rejected = serializers.ReadOnlyField()
    is_cancelled = serializers.ReadOnlyField()
    can_be_modified = serializers.ReadOnlyField()
    can_be_deleted = serializers.ReadOnlyField()
    days_until_effective = serializers.ReadOnlyField()
    
    class Meta:
        model = DayOffChangeRequest
        fields = [
            'id',
            'user',
            'reason',
            'current_day_off',
            'requested_day_off',
            'effective_from',
            'status',
            'approved_by',
            'approved_at',
            'approval_notes',
            'cancelled_by',
            'cancelled_at',
            'cancellation_reason',
            'created_at',
            'updated_at',
            'is_pending',
            'is_approved',
            'is_rejected',
            'is_cancelled',
            'can_be_modified',
            'can_be_deleted',
            'days_until_effective'
        ]


class DayOffChangeRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating day-off change requests"""
    
    class Meta:
        model = DayOffChangeRequest
        fields = [
            'reason',
            'requested_day_off',
            'effective_from'
        ]
    
    def validate(self, data):
        """Validate the request data"""
        requested_day_off = data.get('requested_day_off')
        effective_from = data.get('effective_from')
        user = self.context['request'].user
        
        # Validate requested day off
        if not requested_day_off:
            raise serializers.ValidationError({
                'requested_day_off': 'Requested day off is required.'
            })
        
        # Check if requested day off is different from current
        if requested_day_off == (user.day_off or 'none'):
            raise serializers.ValidationError({
                'requested_day_off': 'Requested day off must be different from your current day off.'
            })
        
        # Validate effective date
        if effective_from and effective_from < timezone.now().date():
            raise serializers.ValidationError({
                'effective_from': 'Effective date cannot be in the past.'
            })
        
        return data
    
    def create(self, validated_data):
        """Create a new day-off change request"""
        # Get user from context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Set current day off from user
        validated_data['current_day_off'] = user.day_off or 'none'
        
        return super().create(validated_data)


class DayOffChangeRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating day-off change requests (only pending ones)"""
    
    class Meta:
        model = DayOffChangeRequest
        fields = [
            'reason',
            'requested_day_off',
            'effective_from'
        ]
    
    def validate(self, data):
        """Validate update data"""
        instance = self.instance
        user = self.context['request'].user
        
        # Can only update pending requests
        if instance.status != 'pending':
            raise serializers.ValidationError(
                "Only pending requests can be updated."
            )
        
        # Check if user is the owner
        if user != instance.user:
            raise serializers.ValidationError(
                "You can only update your own requests."
            )
        
        # Validate requested day off if provided
        requested_day_off = data.get('requested_day_off', instance.requested_day_off)
        if requested_day_off == (user.day_off or 'none'):
            raise serializers.ValidationError({
                'requested_day_off': 'Requested day off must be different from your current day off.'
            })
        
        # Validate effective date if provided
        effective_from = data.get('effective_from', instance.effective_from)
        if effective_from and effective_from < timezone.now().date():
            raise serializers.ValidationError({
                'effective_from': 'Effective date cannot be in the past.'
            })
        
        return data


class DayOffChangeRequestActionSerializer(serializers.Serializer):
    """Serializer for approve/reject/cancel actions"""
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)