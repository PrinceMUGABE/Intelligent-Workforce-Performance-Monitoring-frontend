from django.contrib import admin
from .models import DayOffChangeRequest


@admin.register(DayOffChangeRequest)
class DayOffChangeRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'current_day_off',
        'requested_day_off',
        'status',
        'effective_from',
        'created_at',
        'approved_by'
    ]
    
    list_filter = [
        'status',
        'current_day_off',
        'requested_day_off',
        'effective_from',
        'created_at',
        'approved_at'
    ]
    
    search_fields = [
        'user__full_name',
        'user__email',
        'reason',
        'approval_notes'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'approved_at',
        'cancelled_at'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'user',
                'reason',
                'effective_from'
            )
        }),
        ('Day Off Details', {
            'fields': (
                'current_day_off',
                'requested_day_off'
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                'approved_by',
                'approved_at',
                'approval_notes',
                'cancelled_by',
                'cancelled_at',
                'cancellation_reason'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        if obj:  # Editing existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields