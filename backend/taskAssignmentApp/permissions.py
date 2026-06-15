# taskAssignmentApp/permissions.py

from rest_framework.permissions import BasePermission


class IsAdminOrManager(BasePermission):
    """
    Custom permission to only allow admins and managers
    """
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_manager)
        )


class IsOwnerOrAdminManager(BasePermission):
    """
    Custom permission to allow:
    - Employees to access their own assignments
    - Admins/managers to access all assignments
    """
    def has_object_permission(self, request, view, obj):
        # Admin and manager can access everything
        if request.user.is_admin or request.user.is_manager:
            return True
        
        # Employees can only access their own assignments
        if request.user.is_employee:
            return obj.user_id == request.user.id
        
        return False