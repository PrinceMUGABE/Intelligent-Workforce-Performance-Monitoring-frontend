# reportApp/permissions.py
from rest_framework import permissions


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Permission to check if user is authenticated and has active status
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.status == 'approved' and
            request.user.availability_status == 'active'
        )


class CanGenerateUserReports(permissions.BasePermission):
    """
    Permission for generating user reports
    Only admin, manager, and analyst can generate user reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            request.user.role in ['admin', 'manager', 'analyst']
        )


class CanGenerateDepartmentReports(permissions.BasePermission):
    """
    Permission for generating department reports
    Only admin, manager, and analyst can generate department reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            request.user.role in ['admin', 'manager', 'analyst']
        )


class CanGenerateTaskReports(permissions.BasePermission):
    """
    Permission for generating task reports
    Admin, manager, and analyst can generate all task reports
    Employees can only generate their own task reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )


class CanGenerateTaskAssignmentReports(permissions.BasePermission):
    """
    Permission for generating task assignment reports
    Admin, manager, and analyst can generate all assignment reports
    Employees can only generate their own assignment reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )


class CanGenerateDayOffReports(permissions.BasePermission):
    """
    Permission for generating day-off reports
    Admin, manager, and analyst can generate all day-off reports
    Employees can only view their own day-off information
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )


class CanGenerateActivityReports(permissions.BasePermission):
    """
    Permission for generating activity reports
    Only admin and analyst can generate activity reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            request.user.role in ['admin', 'analyst']
        )


class CanGeneratePerformanceReports(permissions.BasePermission):
    """
    Permission for generating performance reports
    Admin, manager, and analyst can generate all performance reports
    Employees can only generate their own performance reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )


class CanGenerateOrganizationReports(permissions.BasePermission):
    """
    Permission for generating organization-wide reports
    Only admin and analyst can generate organization reports
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            request.user.role in ['admin', 'analyst']
        )