from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from userApp.models import CustomUser

class DayOffChangeRequest(models.Model):
    """Model for handling day-off change requests (shift functionality removed)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
        ('none', 'No Day Off'),
    ]
    
    # Request metadata
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='day_off_requests',
        help_text="Employee making the request"
    )
    
    reason = models.TextField(
        help_text="Reason for the day-off change request"
    )
    
    current_day_off = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        help_text="Current day off of the employee"
    )
    
    requested_day_off = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        help_text="Requested new day off"
    )
    
    # Effective date
    effective_from = models.DateField(
        help_text="Date when the change should take effect if approved"
    )
    
    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_day_off_requests',
        help_text="Manager or admin who approved/rejected the request"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when request was approved/rejected"
    )
    
    approval_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from approver (reason for rejection, etc.)"
    )
    
    cancelled_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_day_off_requests',
        help_text="User who cancelled the request (employee themselves)"
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when request was cancelled"
    )
    
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for cancellation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Exact time the request was sent"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Day Off Change Request'
        verbose_name_plural = 'Day Off Change Requests'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['effective_from']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validate the request data"""
        super().clean()
        
        # Validate requested day off is provided
        if not self.requested_day_off:
            raise ValidationError({
                'requested_day_off': 'Requested day off must be provided.'
            })
        
        # Validate effective date is not in the past
        if self.effective_from and self.effective_from < timezone.now().date():
            raise ValidationError({
                'effective_from': 'Effective date cannot be in the past.'
            })
        
        # Validate new day off is different from current
        if (self.requested_day_off and self.current_day_off and 
            self.requested_day_off == self.current_day_off):
            raise ValidationError({
                'requested_day_off': 'Requested day off must be different from current day off.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to perform validation and set current values"""
        # Set current values from user if not already set
        if not self.pk:  # Only on creation
            if not self.current_day_off:
                self.current_day_off = self.user.day_off or 'none'
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def approve(self, approved_by_user, notes=None):
        """Approve the request and apply changes to user"""
        if self.status != 'pending':
            raise ValidationError("Only pending requests can be approved.")
        
        # Check if approver has permission
        if not (approved_by_user.role in ['admin', 'manager']):
            raise ValidationError("You don't have permission to approve this request.")
        
        # Update request status
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
        
        # Update user's day off
        self.user.day_off = self.requested_day_off
        self.user.save(update_fields=['day_off', 'updated_at'])
    
    def reject(self, rejected_by_user, reason=None):
        """Reject the request without applying changes"""
        if self.status != 'pending':
            raise ValidationError("Only pending requests can be rejected.")
        
        # Check if rejector has permission
        if not (rejected_by_user.role in ['admin', 'manager']):
            raise ValidationError("You don't have permission to reject this request.")
        
        self.status = 'rejected'
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.approval_notes = reason or 'Request rejected'
        self.save()
    
    def cancel(self, cancelled_by_user, reason=None):
        """Cancel the request (only by the requesting employee)"""
        if self.status != 'pending':
            raise ValidationError("Only pending requests can be cancelled.")
        
        # Check if user has permission to cancel
        if cancelled_by_user != self.user:
            raise ValidationError("Only the request owner can cancel this request.")
        
        self.status = 'cancelled'
        self.cancelled_by = cancelled_by_user
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
    
    def delete_request(self, deleting_user):
        """Delete the request (only pending or cancelled requests)"""
        if self.status not in ['pending', 'cancelled']:
            raise ValidationError("Only pending or cancelled requests can be deleted.")
        
        # Check if user has permission to delete
        if not (deleting_user.role in ['admin', 'manager'] or deleting_user == self.user):
            raise ValidationError("You don't have permission to delete this request.")
        
        self.delete()
    
    @property
    def is_pending(self):
        """Check if request is pending"""
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        """Check if request is approved"""
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        """Check if request is rejected"""
        return self.status == 'rejected'
    
    @property
    def is_cancelled(self):
        """Check if request is cancelled"""
        return self.status == 'cancelled'
    
    @property
    def can_be_modified(self):
        """Check if request can still be modified"""
        return self.status == 'pending'
    
    @property
    def can_be_deleted(self):
        """Check if request can be deleted"""
        return self.status in ['pending', 'cancelled']
    
    @property
    def days_until_effective(self):
        """Calculate days until the change becomes effective"""
        if self.effective_from:
            delta = self.effective_from - timezone.now().date()
            return delta.days
        return None