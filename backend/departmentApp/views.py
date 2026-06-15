# departmentApp/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from .models import Department
from .serializers import (
    DepartmentSerializer, 
    DepartmentCreateSerializer, 
    DepartmentUpdateSerializer
)
from userApp.models import CustomUser
from activityApp.models import Activity
import time


def is_admin(user):
    """Helper function to check if user is admin"""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'admin'


def log_department_activity(activity_type, user, request, status_code, 
                           description, related_department_id=None, 
                           duration_ms=None, request_data=None, response_data=None):
    """
    Helper function to log department-related activities
    
    Args:
        activity_type: Type of activity (e.g., 'department_create', 'department_update')
        user: User performing the action
        request: Django request object
        status_code: HTTP status code
        description: Description of the activity
        related_department_id: ID of the department being affected
        duration_ms: Duration of the request in milliseconds
        request_data: Request payload (sanitized)
        response_data: Response data (sanitized)
    """
    # Sanitize sensitive data from request_data and response_data
    sanitized_request_data = None
    sanitized_response_data = None
    
    if request_data:
        sanitized_request_data = request_data.copy()
        # Remove sensitive fields if present
        sensitive_fields = ['password', 'token', 'secret', 'key', 'authorization']
        for field in sensitive_fields:
            if field in sanitized_request_data:
                sanitized_request_data[field] = '***REDACTED***'
    
    if response_data:
        sanitized_response_data = response_data.copy()
        # Remove sensitive data from response
        if isinstance(sanitized_response_data, dict):
            if 'token' in sanitized_response_data:
                sanitized_response_data['token'] = '***REDACTED***'
            if 'refresh' in sanitized_response_data:
                sanitized_response_data['refresh'] = '***REDACTED***'
    
    # Log the activity
    Activity.log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request,
        related_department_id=related_department_id,
        duration_ms=duration_ms,
        request_data=sanitized_request_data,
        response_data=sanitized_response_data
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_department(request):
    """
    Create a new department (Admin only)
    """
    start_time = time.time()  # For calculating duration
    
    try:
        # Check if user is admin
        if not is_admin(request.user):
            description = f"User {request.user.email} attempted to create department without admin privileges"
            log_department_activity(
                activity_type='department_create',
                user=request.user,
                request=request,
                status_code='403',
                description=description,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Permission denied. Only administrators can create departments.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate request data
        if not request.data:
            description = f"Admin {request.user.email} attempted to create department with empty data"
            log_department_activity(
                activity_type='department_create',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'No data provided. Please provide department details.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DepartmentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Save with created_by
            department = serializer.save(created_by=request.user)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log successful creation
            description = f"Admin {request.user.email} created department '{department.name}' (ID: {department.id})"
            log_department_activity(
                activity_type='department_create',
                user=request.user,
                request=request,
                status_code='201',
                description=description,
                related_department_id=department.id,
                duration_ms=duration_ms,
                request_data=request.data,
                response_data={'id': department.id, 'name': department.name}
            )
            
            # Return full department details
            response_serializer = DepartmentSerializer(department)
            
            return Response(
                {
                    'success': True,
                    'message': 'Department created successfully.',
                    'data': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        # Log validation failure
        description = f"Admin {request.user.email} failed to create department: validation errors"
        log_department_activity(
            activity_type='department_create',
            user=request.user,
            request=request,
            status_code='400',
            description=description,
            request_data=request.data,
            response_data={'errors': serializer.errors}
        )
        
        return Response(
            {
                'success': False,
                'message': 'Validation failed. Please check your input.',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except IntegrityError as e:
        # Log integrity error
        description = f"Admin {request.user.email} attempted to create department with duplicate name"
        log_department_activity(
            activity_type='department_create',
            user=request.user,
            request=request,
            status_code='400',
            description=description,
            request_data=request.data
        )
        
        return Response(
            {
                'success': False,
                'message': 'A department with this name already exists.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        # Log unexpected error
        description = f"Admin {request.user.email} encountered error while creating department: {str(e)}"
        log_department_activity(
            activity_type='department_create',
            user=request.user,
            request=request,
            status_code='500',
            description=description,
            request_data=request.data
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while creating the department: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_departments(request):
    """
    Get all departments (All authenticated users)
    """
    start_time = time.time()
    
    try:
        departments = Department.objects.all()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            if status_filter not in ['active', 'inactive']:
                # Log invalid filter
                user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
                description = f"User {user_email} used invalid status filter: {status_filter}"
                log_department_activity(
                    activity_type='departments_list',
                    user=request.user if request.user.is_authenticated else None,
                    request=request,
                    status_code='400',
                    description=description,
                    request_data={'status_filter': status_filter}
                )
                
                return Response(
                    {
                        'success': False,
                        'message': 'Invalid status filter. Use "active" or "inactive".'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            departments = departments.filter(status=status_filter)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        serializer = DepartmentSerializer(departments, many=True)
        
        # Log successful retrieval
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        description = f"User {user_email} retrieved {departments.count()} departments"
        log_department_activity(
            activity_type='departments_list',
            user=request.user if request.user.is_authenticated else None,
            request=request,
            status_code='200',
            description=description,
            duration_ms=duration_ms,
            request_data=dict(request.query_params)
        )
        
        return Response(
            {
                'success': True,
                'message': 'Departments retrieved successfully.',
                'count': departments.count(),
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        # Log error
        user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
        description = f"User {user_email} encountered error while retrieving departments: {str(e)}"
        log_department_activity(
            activity_type='departments_list',
            user=request.user if request.user.is_authenticated else None,
            request=request,
            status_code='500',
            description=description
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while retrieving departments: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_by_id(request, department_id):
    """
    Get a single department by ID (All authenticated users)
    """
    start_time = time.time()
    
    try:
        # Validate department_id
        if not department_id:
            description = f"User {request.user.email} requested department without ID"
            log_department_activity(
                activity_type='department_view',
                user=request.user,
                request=request,
                status_code='400',
                description=description
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Department ID is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            description = f"User {request.user.email} requested non-existent department ID: {department_id}"
            log_department_activity(
                activity_type='department_view',
                user=request.user,
                request=request,
                status_code='404',
                description=description,
                related_department_id=department_id
            )
            
            return Response(
                {
                    'success': False,
                    'message': f'Department with ID {department_id} does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            description = f"User {request.user.email} requested department with invalid ID format: {department_id}"
            log_department_activity(
                activity_type='department_view',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                related_department_id=department_id
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Invalid department ID format.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        serializer = DepartmentSerializer(department)
        
        # Log successful view
        description = f"User {request.user.email} viewed department '{department.name}' (ID: {department.id})"
        log_department_activity(
            activity_type='department_view',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_department_id=department.id,
            duration_ms=duration_ms
        )
        
        return Response(
            {
                'success': True,
                'message': 'Department retrieved successfully.',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        # Log error
        description = f"User {request.user.email} encountered error while viewing department {department_id}: {str(e)}"
        log_department_activity(
            activity_type='department_view',
            user=request.user,
            request=request,
            status_code='500',
            description=description,
            related_department_id=department_id
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while retrieving the department: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_department(request, department_id):
    """
    Update a department (Admin only)
    """
    start_time = time.time()
    
    try:
        # Check if user is admin
        if not is_admin(request.user):
            description = f"User {request.user.email} attempted to update department without admin privileges"
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='403',
                description=description,
                related_department_id=department_id,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Permission denied. Only administrators can update departments.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate department_id
        if not department_id:
            description = f"Admin {request.user.email} attempted to update department without ID"
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Department ID is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            description = f"Admin {request.user.email} attempted to update non-existent department ID: {department_id}"
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='404',
                description=description,
                related_department_id=department_id,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': f'Department with ID {department_id} does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            description = f"Admin {request.user.email} attempted to update department with invalid ID format: {department_id}"
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                related_department_id=department_id,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Invalid department ID format.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate request data
        if not request.data:
            description = f"Admin {request.user.email} attempted to update department {department_id} with empty data"
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                related_department_id=department_id,
                request_data=request.data
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'No data provided. Please provide department details to update.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use partial update for PATCH, full update for PUT
        partial = request.method == 'PATCH'
        serializer = DepartmentUpdateSerializer(department, data=request.data, partial=partial)
        
        if serializer.is_valid():
            # Store old values for logging
            old_name = department.name
            old_status = department.status
            
            updated_department = serializer.save()
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Prepare description with changes
            changes = []
            if 'name' in request.data and old_name != updated_department.name:
                changes.append(f"name changed from '{old_name}' to '{updated_department.name}'")
            if 'status' in request.data and old_status != updated_department.status:
                changes.append(f"status changed from '{old_status}' to '{updated_department.status}'")
            
            description = f"Admin {request.user.email} updated department '{updated_department.name}' (ID: {updated_department.id})"
            if changes:
                description += f": {', '.join(changes)}"
            
            # Log successful update
            log_department_activity(
                activity_type='department_update',
                user=request.user,
                request=request,
                status_code='200',
                description=description,
                related_department_id=updated_department.id,
                duration_ms=duration_ms,
                request_data=request.data,
                response_data={'id': updated_department.id, 'name': updated_department.name}
            )
            
            # Return full department details
            response_serializer = DepartmentSerializer(updated_department)
            
            return Response(
                {
                    'success': True,
                    'message': 'Department updated successfully.',
                    'data': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        # Log validation failure
        description = f"Admin {request.user.email} failed to update department {department_id}: validation errors"
        log_department_activity(
            activity_type='department_update',
            user=request.user,
            request=request,
            status_code='400',
            description=description,
            related_department_id=department_id,
            request_data=request.data,
            response_data={'errors': serializer.errors}
        )
        
        return Response(
            {
                'success': False,
                'message': 'Validation failed. Please check your input.',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except IntegrityError as e:
        # Log integrity error
        description = f"Admin {request.user.email} attempted to update department {department_id} with duplicate name"
        log_department_activity(
            activity_type='department_update',
            user=request.user,
            request=request,
            status_code='400',
            description=description,
            related_department_id=department_id,
            request_data=request.data
        )
        
        return Response(
            {
                'success': False,
                'message': 'A department with this name already exists.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        # Log unexpected error
        description = f"Admin {request.user.email} encountered error while updating department {department_id}: {str(e)}"
        log_department_activity(
            activity_type='department_update',
            user=request.user,
            request=request,
            status_code='500',
            description=description,
            related_department_id=department_id,
            request_data=request.data
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while updating the department: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_department(request, department_id):
    """
    Delete a department (Admin only)
    """
    start_time = time.time()
    
    try:
        # Check if user is admin
        if not is_admin(request.user):
            description = f"User {request.user.email} attempted to delete department without admin privileges"
            log_department_activity(
                activity_type='department_delete',
                user=request.user,
                request=request,
                status_code='403',
                description=description,
                related_department_id=department_id
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Permission denied. Only administrators can delete departments.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate department_id
        if not department_id:
            description = f"Admin {request.user.email} attempted to delete department without ID"
            log_department_activity(
                activity_type='department_delete',
                user=request.user,
                request=request,
                status_code='400',
                description=description
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Department ID is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            description = f"Admin {request.user.email} attempted to delete non-existent department ID: {department_id}"
            log_department_activity(
                activity_type='department_delete',
                user=request.user,
                request=request,
                status_code='404',
                description=description,
                related_department_id=department_id
            )
            
            return Response(
                {
                    'success': False,
                    'message': f'Department with ID {department_id} does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            description = f"Admin {request.user.email} attempted to delete department with invalid ID format: {department_id}"
            log_department_activity(
                activity_type='department_delete',
                user=request.user,
                request=request,
                status_code='400',
                description=description,
                related_department_id=department_id
            )
            
            return Response(
                {
                    'success': False,
                    'message': 'Invalid department ID format.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store department information before deletion
        department_name = department.name
        department_data = {
            'id': department.id,
            'name': department.name,
            'status': department.status,
            'description': department.description
        }
        
        # Delete the department
        department.delete()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful deletion
        description = f"Admin {request.user.email} deleted department '{department_name}' (ID: {department_id})"
        log_department_activity(
            activity_type='department_delete',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_department_id=department_id,
            duration_ms=duration_ms,
            response_data={'deleted_department': department_data}
        )
        
        return Response(
            {
                'success': True,
                'message': f'Department "{department_name}" has been deleted successfully.'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        # Log error
        description = f"Admin {request.user.email} encountered error while deleting department {department_id}: {str(e)}"
        log_department_activity(
            activity_type='department_delete',
            user=request.user,
            request=request,
            status_code='500',
            description=description,
            related_department_id=department_id
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while deleting the department: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_departments(request):
    """
    Get departments the logged-in user belongs to based on their role
    """
    start_time = time.time()
    
    try:
        user = CustomUser.objects.get(id=request.user.id)
    except CustomUser.DoesNotExist:
        description = f"User with ID {request.user.id} attempted to access departments but user does not exist"
        log_department_activity(
            activity_type='departments_list',
            user=request.user,
            request=request,
            status_code='404',
            description=description
        )
        
        return Response(
            {
                'success': False,
                'message': 'User not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        # Determine which departments to return based on user role
        if user.role == 'employee':
            # employee: get their single department (ForeignKey)
            if user.department:
                departments = Department.objects.filter(id=user.department.id)
            else:
                departments = Department.objects.none()
        
        elif user.role in ['admin', 'manager', 'analyst']:
            # Admin/HR: get all departments in the system
            departments = Department.objects.all()
        
        else:
            # Unknown role
            departments = Department.objects.none()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            if status_filter not in ['active', 'inactive']:
                description = f"User {user.email} used invalid status filter: {status_filter}"
                log_department_activity(
                    activity_type='departments_list',
                    user=user,
                    request=request,
                    status_code='400',
                    description=description,
                    request_data={'status_filter': status_filter}
                )
                
                return Response(
                    {
                        'success': False,
                        'message': 'Invalid status filter. Use "active" or "inactive".'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            departments = departments.filter(status=status_filter)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        serializer = DepartmentSerializer(departments, many=True)
        
        # Build response message and log
        if user.role == 'employee':
            message = 'Your assigned department retrieved successfully.'
            description = f"Employee {user.email} retrieved their assigned department"
        elif user.role in ['admin', 'manager', 'analyst']:
            message = 'All departments retrieved successfully.'
            description = f"{user.role.capitalize()} {user.email} retrieved all departments"
        else:
            message = 'Departments retrieved successfully.'
            description = f"User {user.email} with unknown role retrieved departments"
        
        # Log activity
        log_department_activity(
            activity_type='departments_list',
            user=user,
            request=request,
            status_code='200',
            description=description,
            duration_ms=duration_ms,
            request_data=dict(request.query_params)
        )
        
        return Response(
            {
                'success': True,
                'message': message,
                'count': departments.count(),
                'user_role': user.role,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        # Log error
        description = f"User {request.user.email} encountered error while retrieving their departments: {str(e)}"
        log_department_activity(
            activity_type='departments_list',
            user=request.user,
            request=request,
            status_code='500',
            description=description
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while retrieving your departments: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_employees(request, department_id):
    """
    Get all employees in a specific department
    """
    start_time = time.time()
    
    try:
        # Validate department_id
        if not department_id:
            return Response(
                {
                    'success': False,
                    'message': 'Department ID is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': f'Department with ID {department_id} does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all users in this department
        employees = CustomUser.objects.filter(
            department=department,
            role='employee'
        ).select_related('department')
        
        # Serialize employee data
        employee_data = []
        for employee in employees:
            employee_data.append({
                'id': employee.id,
                'full_name': employee.full_name,
                'work_mail_address': employee.work_mail_address,
                'email': employee.email,
                'phone_number': employee.phone_number,
                'role': employee.role,
                'status': employee.status,
                'availability_status': employee.availability_status,
                'created_at': employee.created_at,
                'department_details': {
                    'id': employee.department.id if employee.department else None,
                    'name': employee.department.name if employee.department else None
                }
            })
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log activity
        description = f"User {request.user.email} viewed employees in department '{department.name}'"
        log_department_activity(
            activity_type='department_employees_view',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_department_id=department.id,
            duration_ms=duration_ms
        )
        
        return Response(
            {
                'success': True,
                'message': f'Employees retrieved successfully for department {department.name}',
                'count': employees.count(),
                'department': {
                    'id': department.id,
                    'name': department.name,
                    'status': department.status
                },
                'data': employee_data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        log_department_activity(
            activity_type='department_employees_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing department employees: {str(e)}",
            related_department_id=department_id
        )
        
        return Response(
            {
                'success': False,
                'message': f'An error occurred while retrieving department employees: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )