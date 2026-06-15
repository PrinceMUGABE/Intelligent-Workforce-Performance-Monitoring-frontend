from django.db import models
from django.utils.timezone import now
from django.conf import settings


class Activity(models.Model):
    """Model to track all user activities in the system"""
    
    # Activity Types
    ACTIVITY_TYPE_CHOICES = [
        # Authentication Activities
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('user_registration', 'User Registration'),
        ('password_reset_request', 'Password Reset Request'),
        ('password_reset_complete', 'Password Reset Complete'),
        ('password_change', 'Password Change'),
        ('otp_request', 'OTP Request'),
        ('otp_verification', 'OTP Verification'),
        
        # User Management Activities
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('user_delete', 'User Deleted'),
        ('user_activate', 'User Activated'),
        ('user_deactivate', 'User Deactivated'),
        ('user_status_change', 'User Status Changed'),
        ('profile_update', 'Profile Updated'),
        ('user_view', 'User Viewed'),
        ('users_list', 'Users List Viewed'),
        
        # ===== User Day-Off Field Activities (User App) =====
        ('user_day_off_set', 'User Day-Off Set'),
        ('user_day_off_update', 'User Day-Off Updated'),
        ('user_day_off_clear', 'User Day-Off Cleared'),
        ('user_day_off_view', 'User Day-Off Viewed'),
        ('user_day_off_list', 'User Day-Off List Viewed'),
        ('user_day_off_stats_view', 'User Day-Off Statistics Viewed'),
        ('user_day_off_bulk_update', 'User Day-Off Bulk Updated'),
        # ====================================================
        
        # Department Management Activities
        ('department_create', 'Department Created'),
        ('department_update', 'Department Updated'),
        ('department_delete', 'Department Deleted'),
        ('department_view', 'Department Viewed'),
        ('departments_list', 'Departments List Viewed'),
        ('department_employees_view', 'Department Employees View'),
        
        # Task Management Activities
        ('task_create', 'Task Created'),
        ('task_update', 'Task Updated'),
        ('task_delete', 'Task Deleted'),
        ('task_view', 'Task Viewed'),
        ('tasks_list', 'Tasks List Viewed'),
        ('task_view_by_name', 'Task Viewed By Name'),
        ('task_status_change', 'Task Status Changed'),
        
        # Task Assignment Activities
        ('task_assignment_create', 'Task Assignment Created'),
        ('task_assignment_update', 'Task Assignment Updated'),
        ('task_assignment_delete', 'Task Assignment Deleted'),
        ('task_assignment_view', 'Task Assignment Viewed'),
        ('task_assignments_list', 'Task Assignments List Viewed'),
        ('task_assignment_start', 'Task Assignment Started'),
        ('task_assignment_complete', 'Task Assignment Completed'),
        ('task_assignment_missed', 'Task Assignment Missed'),
        ('task_assignment_reassign', 'Task Assignment Reassigned'),
        ('task_assignment_modify', 'Task Assignment Modified'),
        ('task_assignment_priority_change', 'Task Assignment Priority Changed'),
        
        # Task Assignment Status Change Activities
        ('task_assignment_status_update', 'Task Assignment Status Updated'),
        ('task_assignment_status_scheduled_to_active', 'Task Assignment Status: Scheduled → Active'),
        ('task_assignment_status_scheduled_to_completed', 'Task Assignment Status: Scheduled → Completed'),
        ('task_assignment_status_scheduled_to_reassigned', 'Task Assignment Status: Scheduled → Reassigned'),
        ('task_assignment_status_scheduled_to_cancelled', 'Task Assignment Status: Scheduled → Cancelled'),
        ('task_assignment_status_active_to_completed', 'Task Assignment Status: Active → Completed'),
        ('task_assignment_status_active_to_reassigned', 'Task Assignment Status: Active → Reassigned'),
        ('task_assignment_status_active_to_cancelled', 'Task Assignment Status: Active → Cancelled'),
        ('task_assignment_status_missed_to_reassigned', 'Task Assignment Status: Missed → Reassigned'),
        ('task_assignment_status_missed_to_cancelled', 'Task Assignment Status: Missed → Cancelled'),
        
        # Task Assignment Bulk Operations
        ('task_assignment_bulk_create', 'Task Assignment Bulk Created'),
        ('task_assignment_bulk_delete', 'Task Assignment Bulk Deleted'),
        ('task_assignment_bulk_update', 'Task Assignment Bulk Updated'),
        
        # Task Assignment Status Check Activities
        ('task_assignment_missed_check', 'Task Assignment Missed Check Run'),
        ('task_assignment_status_transitions_view', 'Task Assignment Status Transitions Viewed'),
        
        # ===== Day-Off Request Activities (Request App) =====
        # Create operations
        ('dayoff_request_create', 'Day-Off Request Created'),
        ('dayoff_request_create_own', 'Day-Off Request Created (Self)'),
        ('dayoff_request_create_for_user', 'Day-Off Request Created (For Another User)'),
        ('dayoff_request_bulk_create', 'Day-Off Requests Bulk Created'),
        
        # Read operations
        ('dayoff_request_view', 'Day-Off Request Viewed'),
        ('dayoff_request_view_own', 'Day-Off Request Viewed (Self)'),
        ('dayoff_request_view_for_user', 'Day-Off Request Viewed (For Another User)'),
        ('dayoff_requests_list', 'Day-Off Requests List Viewed'),
        ('dayoff_requests_list_all', 'All Day-Off Requests Viewed'),
        ('dayoff_requests_list_pending', 'Pending Day-Off Requests Viewed'),
        ('dayoff_requests_list_approved', 'Approved Day-Off Requests Viewed'),
        ('dayoff_requests_list_rejected', 'Rejected Day-Off Requests Viewed'),
        
        # Update operations
        ('dayoff_request_update', 'Day-Off Request Updated'),
        ('dayoff_request_update_own', 'Day-Off Request Updated (Self)'),
        ('dayoff_request_update_for_user', 'Day-Off Request Updated (For Another User)'),
        
        # Approval/Rejection operations
        ('dayoff_request_approve', 'Day-Off Request Approved'),
        ('dayoff_request_reject', 'Day-Off Request Rejected'),
        ('dayoff_request_cancel', 'Day-Off Request Cancelled'),
        ('dayoff_request_reopen', 'Day-Off Request Reopened'),
        
        # Delete operations
        ('dayoff_request_delete', 'Day-Off Request Deleted'),
        ('dayoff_request_delete_own', 'Day-Off Request Deleted (Self)'),
        ('dayoff_request_delete_for_user', 'Day-Off Request Deleted (For Another User)'),
        ('dayoff_request_bulk_delete', 'Day-Off Requests Bulk Deleted'),
        
        # Statistics and reporting
        ('dayoff_request_stats_view', 'Day-Off Request Statistics Viewed'),
        ('dayoff_request_stats_by_user', 'User Day-Off Request Statistics Viewed'),
        ('dayoff_request_stats_by_department', 'Department Day-Off Request Statistics Viewed'),
        ('dayoff_request_stats_by_date_range', 'Day-Off Request Date Range Statistics Viewed'),
        ('dayoff_request_bulk_view', 'Day-Off Requests Bulk Viewed'),
        
        # Status change tracking
        ('dayoff_request_status_change', 'Day-Off Request Status Changed'),
        ('dayoff_request_pending_to_approved', 'Day-Off Request: Pending → Approved'),
        ('dayoff_request_pending_to_rejected', 'Day-Off Request: Pending → Rejected'),
        ('dayoff_request_approved_to_cancelled', 'Day-Off Request: Approved → Cancelled'),
        ('dayoff_request_rejected_to_pending', 'Day-Off Request: Rejected → Pending'),
        ('dayoff_request_cancelled_to_pending', 'Day-Off Request: Cancelled → Pending'),
        # ====================================================
        
        # Notification Activities
        ('notification_sent', 'Notification Sent'),
        ('notification_viewed', 'Notification Viewed'),
        ('notification_cleared', 'Notification Cleared'),
        
        # Contact Activities
        ('contact_submission', 'Contact Form Submitted'),
        
        # Performance Activities
        ('performance_view_own', 'Own Performance Viewed'),
        ('performance_view_user', 'User Performance Viewed'),
        ('performance_view_all', 'All Performances Viewed'),
        ('performance_view_department', 'Department Performance Viewed'),
        ('performance_view_departments', 'All Departments Performance Viewed'),
        ('performance_view_organization', 'Organization Performance Viewed'),
        
        # API Activities
        ('api_request', 'API Request'),
        ('api_error', 'API Error'),
    ]
    
    # Status Choices based on HTTP status codes
    STATUS_CHOICES = [
        # Success responses (2xx)
        ('200', '200 - OK'),
        ('201', '201 - Created'),
        ('202', '202 - Accepted'),
        ('204', '204 - No Content'),
        
        # Client errors (4xx)
        ('400', '400 - Bad Request'),
        ('401', '401 - Unauthorized'),
        ('403', '403 - Forbidden'),
        ('404', '404 - Not Found'),
        ('409', '409 - Conflict'),
        ('422', '422 - Unprocessable Entity'),
        
        # Server errors (5xx)
        ('500', '500 - Internal Server Error'),
        ('502', '502 - Bad Gateway'),
        ('503', '503 - Service Unavailable'),
    ]
    
    # Day-Off Request Status Choices (for the request app)
    DAYOFF_REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Fields
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES,
        help_text="Type of activity performed"
    )
    
    user = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_activities',
        help_text="User who performed the activity"
    )
    
    status_code = models.CharField(
        max_length=3,
        choices=STATUS_CHOICES,
        default='200',
        help_text="HTTP status code returned by the system"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the activity"
    )
    
    # System information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string from the request"
    )
    
    device_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Type of device used (Mobile, Desktop, Tablet)"
    )
    
    browser = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Browser used"
    )
    
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Operating system used"
    )
    
    # Additional metadata
    request_method = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    
    endpoint = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="API endpoint accessed"
    )
    
    request_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Request payload (sanitized - no sensitive data)"
    )
    
    response_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Response data (sanitized - no sensitive data)"
    )
    
    # Related objects (for tracking what was affected)
    related_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of user that was affected by this activity"
    )
    
    related_task_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of task that was affected by this activity"
    )
    
    related_department_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of department that was affected by this activity"
    )
    
    related_assignment_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of task assignment that was affected by this activity"
    )
    
    # ===== For User App: Direct day-off field on user =====
    related_dayoff_user_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of user whose day-off field was affected (User App)"
    )
    
    # ===== For Request App: Day-off change requests =====
    related_dayoff_request_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of day-off change request that was affected by this activity (Request App)"
    )
    
    # Status transition tracking (for task assignments)
    from_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Original status before transition (for status changes)"
    )
    
    to_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="New status after transition (for status changes)"
    )
    
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for status change or other actions"
    )
    
    # ===== Day-off specific tracking fields =====
    # For User App: Track changes to user.day_off field
    from_day = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Original day before day-off change (User App)"
    )
    
    to_day = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="New day after day-off change (User App)"
    )
    
    # For Request App: Track day-off request details
    requested_day = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Day requested in day-off request (Request App)"
    )
    
    request_status = models.CharField(
        max_length=20,
        choices=DAYOFF_REQUEST_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Status of the day-off request (Request App)"
    )
    
    from_request_status = models.CharField(
        max_length=20,
        choices=DAYOFF_REQUEST_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Original status of day-off request before change"
    )
    
    to_request_status = models.CharField(
        max_length=20,
        choices=DAYOFF_REQUEST_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="New status of day-off request after change"
    )
    
    request_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes or reason for day-off request"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=now,
        help_text="Exact date and time when activity was performed"
    )
    
    # Performance metrics
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration of the request in milliseconds"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['status_code', '-created_at']),
            models.Index(fields=['related_assignment_id', '-created_at']),
            models.Index(fields=['related_dayoff_request_id', '-created_at']),
            models.Index(fields=['related_dayoff_user_id', '-created_at']),
            # Indexes for status transition queries
            models.Index(fields=['from_status', '-created_at']),
            models.Index(fields=['to_status', '-created_at']),
            models.Index(fields=['activity_type', 'from_status', 'to_status']),
            # Indexes for day-off request queries
            models.Index(fields=['request_status', '-created_at']),
            models.Index(fields=['from_request_status', 'to_request_status']),
            models.Index(fields=['requested_day', '-created_at']),
        ]
    
    def __str__(self):
        user_info = f"{self.user.full_name}" if self.user else "Anonymous"
        activity_display = self.get_activity_type_display()
        
        # Add status transition info if available
        if self.from_status and self.to_status:
            return f"{user_info} - {activity_display} ({self.from_status} → {self.to_status}) - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add day-off request status transition info if available
        if self.from_request_status and self.to_request_status:
            return f"{user_info} - {activity_display} (Request: {self.from_request_status} → {self.to_request_status}) - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add day-off change info if available
        if self.from_day and self.to_day:
            return f"{user_info} - {activity_display} (Day-off: {self.from_day} → {self.to_day}) - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return f"{user_info} - {activity_display} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def is_success(self):
        """Check if the activity was successful"""
        return self.status_code.startswith('2')
    
    def is_client_error(self):
        """Check if the activity resulted in a client error"""
        return self.status_code.startswith('4')
    
    def is_server_error(self):
        """Check if the activity resulted in a server error"""
        return self.status_code.startswith('5')
    
    def get_status_transition_display(self):
        """Get a formatted display of the status transition"""
        if self.from_status and self.to_status:
            return f"{self.from_status} → {self.to_status}"
        return None
    
    def get_request_status_transition_display(self):
        """Get a formatted display of the request status transition"""
        if self.from_request_status and self.to_request_status:
            return f"{self.from_request_status} → {self.to_request_status}"
        return None
    
    def get_day_off_change_display(self):
        """Get a formatted display of the day-off change"""
        if self.from_day and self.to_day:
            return f"{self.from_day} → {self.to_day}"
        return None
    
    @classmethod
    def log_activity(cls, activity_type, user=None, status_code='200', description='',
                     request=None, related_user_id=None, related_department_id=None,
                     related_task_id=None, related_assignment_id=None, 
                     related_dayoff_request_id=None, related_dayoff_user_id=None,
                     duration_ms=None, request_data=None, response_data=None,
                     from_status=None, to_status=None, reason=None,
                     from_day=None, to_day=None, requested_day=None,
                     request_status=None, from_request_status=None, 
                     to_request_status=None, request_notes=None):
        """
        Convenience method to log an activity
        """
        activity_data = {
            'activity_type': activity_type,
            'user': user,
            'status_code': str(status_code),
            'description': description,
            'related_user_id': related_user_id,
            'related_department_id': related_department_id,
            'related_task_id': related_task_id,
            'related_assignment_id': related_assignment_id,
            'related_dayoff_request_id': related_dayoff_request_id,
            'related_dayoff_user_id': related_dayoff_user_id,
            'duration_ms': duration_ms,
            'request_data': request_data,
            'response_data': response_data,
            'from_status': from_status,
            'to_status': to_status,
            'reason': reason,
            'from_day': from_day,
            'to_day': to_day,
            'requested_day': requested_day,
            'request_status': request_status,
            'from_request_status': from_request_status,
            'to_request_status': to_request_status,
            'request_notes': request_notes,
        }
        
        if request:
            # Extract system information from request
            activity_data.update(cls._extract_request_info(request))
        
        return cls.objects.create(**activity_data)
    
    @classmethod
    def log_user_day_off_change(cls, user, target_user, from_day, to_day, 
                                reason=None, request=None, status_code='200'):
        """
        Convenience method for logging changes to the user.day_off field (User App)
        """
        # Determine if user is changing their own day-off or someone else's
        if user and target_user and user.id == target_user.id:
            activity_type = 'user_day_off_update'
            description = f"User {user.email} updated their day-off from {from_day} to {to_day}"
        else:
            activity_type = 'user_day_off_update'
            description = f"User {user.email} updated day-off of user {target_user.email} from {from_day} to {to_day}"
        
        if reason:
            description += f". Reason: {reason}"
        
        return cls.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_user_id=target_user.id,
            related_dayoff_user_id=target_user.id,
            from_day=from_day,
            to_day=to_day,
            reason=reason
        )
    
    @classmethod
    def log_dayoff_request_creation(cls, user, target_user, requested_day, 
                                    request_obj=None, request=None, status_code='201'):
        """
        Convenience method for logging day-off request creation (Request App)
        """
        # Determine if user is creating request for themselves or someone else
        if user and target_user and user.id == target_user.id:
            activity_type = 'dayoff_request_create_own'
            description = f"User {user.email} created a day-off request for {requested_day}"
        else:
            activity_type = 'dayoff_request_create_for_user'
            description = f"User {user.email} created a day-off request for user {target_user.email} for {requested_day}"
        
        request_id = request_obj.id if request_obj else None
        
        return cls.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_user_id=target_user.id,
            related_dayoff_request_id=request_id,
            requested_day=requested_day,
            request_status='pending',
            request_notes=request_obj.notes if request_obj and hasattr(request_obj, 'notes') else None
        )
    
    @classmethod
    def log_dayoff_request_status_change(cls, user, target_user, request_obj,
                                        from_status, to_status, reason=None,
                                        request=None, status_code='200'):
        """
        Convenience method for logging day-off request status changes (Request App)
        """
        # Map status transitions to activity types
        transition_map = {
            ('pending', 'approved'): 'dayoff_request_pending_to_approved',
            ('pending', 'rejected'): 'dayoff_request_pending_to_rejected',
            ('approved', 'cancelled'): 'dayoff_request_approved_to_cancelled',
            ('rejected', 'pending'): 'dayoff_request_rejected_to_pending',
            ('cancelled', 'pending'): 'dayoff_request_cancelled_to_pending',
        }
        
        # Get specific activity type or use generic one
        activity_type = transition_map.get(
            (from_status, to_status), 
            'dayoff_request_status_change'
        )
        
        description = f"Day-off request for {target_user.email} changed from {from_status} to {to_status}"
        if reason:
            description += f". Reason: {reason}"
        
        return cls.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_user_id=target_user.id,
            related_dayoff_request_id=request_obj.id,
            requested_day=request_obj.requested_day if hasattr(request_obj, 'requested_day') else None,
            from_request_status=from_status,
            to_request_status=to_status,
            reason=reason,
            request_notes=request_obj.notes if hasattr(request_obj, 'notes') else None
        )
    
    @classmethod
    def log_dayoff_request_deletion(cls, user, target_user, request_obj,
                                   reason=None, request=None, status_code='200'):
        """
        Convenience method for logging day-off request deletion (Request App)
        """
        # Determine if user is deleting their own request or someone else's
        if user and target_user and user.id == target_user.id:
            activity_type = 'dayoff_request_delete_own'
            description = f"User {user.email} deleted their day-off request for {request_obj.requested_day if hasattr(request_obj, 'requested_day') else 'unknown day'}"
        else:
            activity_type = 'dayoff_request_delete_for_user'
            description = f"User {user.email} deleted day-off request for user {target_user.email}"
        
        if reason:
            description += f". Reason: {reason}"
        
        return cls.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_user_id=target_user.id,
            related_dayoff_request_id=request_obj.id,
            requested_day=request_obj.requested_day if hasattr(request_obj, 'requested_day') else None,
            request_status=request_obj.status if hasattr(request_obj, 'status') else None,
            reason=reason
        )
    
    @classmethod
    def log_status_transition(cls, assignment, user, from_status, to_status, 
                              reason=None, request=None, status_code='200'):
        """
        Convenience method specifically for logging task assignment status transitions
        """
        # Map status transitions to activity types
        transition_map = {
            ('scheduled', 'active'): 'task_assignment_status_scheduled_to_active',
            ('scheduled', 'completed'): 'task_assignment_status_scheduled_to_completed',
            ('scheduled', 'reassigned'): 'task_assignment_status_scheduled_to_reassigned',
            ('scheduled', 'cancelled'): 'task_assignment_status_scheduled_to_cancelled',
            ('active', 'completed'): 'task_assignment_status_active_to_completed',
            ('active', 'reassigned'): 'task_assignment_status_active_to_reassigned',
            ('active', 'cancelled'): 'task_assignment_status_active_to_cancelled',
            ('missed', 'reassigned'): 'task_assignment_status_missed_to_reassigned',
            ('missed', 'cancelled'): 'task_assignment_status_missed_to_cancelled',
        }
        
        # Get specific activity type or use generic one
        activity_type = transition_map.get(
            (from_status, to_status), 
            'task_assignment_status_update'
        )
        
        description = f"Task assignment status changed from {from_status} to {to_status}"
        if reason:
            description += f". Reason: {reason}"
        
        return cls.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_user_id=assignment.user_id,
            related_task_id=assignment.task_id,
            related_assignment_id=assignment.id,
            related_department_id=assignment.department_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason
        )
    
    @staticmethod
    def _extract_request_info(request):
        """Extract system information from Django request object"""
        from user_agents import parse
        
        info = {}
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            info['ip_address'] = x_forwarded_for.split(',')[0]
        else:
            info['ip_address'] = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        info['user_agent'] = user_agent_string
        
        # Parse user agent for device details
        if user_agent_string:
            user_agent = parse(user_agent_string)
            
            # Device type
            if user_agent.is_mobile:
                info['device_type'] = 'Mobile'
            elif user_agent.is_tablet:
                info['device_type'] = 'Tablet'
            elif user_agent.is_pc:
                info['device_type'] = 'Desktop'
            else:
                info['device_type'] = 'Unknown'
            
            # Browser
            browser_family = user_agent.browser.family
            browser_version = user_agent.browser.version_string
            info['browser'] = f"{browser_family} {browser_version}" if browser_version else browser_family
            
            # Operating System
            os_family = user_agent.os.family
            os_version = user_agent.os.version_string
            info['operating_system'] = f"{os_family} {os_version}" if os_version else os_family
        
        # Request method and endpoint
        info['request_method'] = request.method
        info['endpoint'] = request.path
        
        return info


class ActivitySummary(models.Model):
    """Model to store aggregated activity statistics for performance optimization"""
    
    PERIOD_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    user = models.ForeignKey(
        'userApp.CustomUser',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activity_summaries'
    )
    
    activity_type = models.CharField(max_length=50, null=True, blank=True)
    
    total_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Additional metrics for status transitions
    status_transition_counts = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON field storing counts of status transitions by type"
    )
    
    # Additional metrics for day-off requests
    dayoff_request_counts = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON field storing counts of day-off requests by status"
    )
    
    dayoff_request_by_day = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON field storing counts of day-off requests by requested day"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start']
        verbose_name = 'Activity Summary'
        verbose_name_plural = 'Activity Summaries'
        indexes = [
            models.Index(fields=['period_type', 'period_start']),
            models.Index(fields=['user', 'period_type', 'period_start']),
            models.Index(fields=['activity_type', 'period_type', 'period_start']),
        ]
        unique_together = ['period_type', 'period_start', 'user', 'activity_type']
    
    def __str__(self):
        user_info = f"{self.user.full_name}" if self.user else "All Users"
        activity_info = self.activity_type or "All Activities"
        return f"{user_info} - {activity_info} - {self.period_type} ({self.period_start.date()})"