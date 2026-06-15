import traceback
import json
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.db import IntegrityError, DatabaseError
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

from .models import TaskAssignment, TaskAssignmentTemplate, TaskOverload
from .serializers import (
    BulkAssignmentSerializer, DepartmentBulkAssignmentSerializer, 
    TaskAssignmentSerializer, TaskAssignmentModifySerializer,
    TaskAssignmentTemplateSerializer, TaskOverloadSerializer, 
    UserListBulkAssignmentSerializer
)
from .services import TaskAssignmentService, TaskNotificationService
from userApp.models import CustomUser
from taskApp.models import Task
from departmentApp.models import Department
from activityApp.models import Activity
from django.db import models

# ==================== HELPER FUNCTIONS ====================

def _log_to_terminal(message, data=None, level="INFO"):
    """Helper function to log messages to terminal with formatting"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"[{timestamp}] [{level}] {message}")
    if data is not None:
        print(f"\nDATA:")
        if isinstance(data, dict):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)
    print(f"{'='*80}\n")


def _log_assignment_activity(activity_type, user, description, related_user_id=None, 
                           related_task_id=None, related_assignment_id=None, 
                           related_department_id=None, status_code='200', 
                           request=None, request_data=None, response_data=None):
    """Helper function to log assignment activities with error handling"""
    try:
        # Convert any non-serializable objects in response_data
        if response_data:
            response_data = _make_json_serializable(response_data)
        
        if request_data:
            request_data = _make_json_serializable(request_data)
            
        return Activity.log_activity(
            activity_type=activity_type,
            user=user,
            description=description,
            related_user_id=related_user_id,
            related_task_id=related_task_id,
            related_assignment_id=related_assignment_id,
            related_department_id=related_department_id,
            status_code=status_code,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
    except Exception as e:
        _log_to_terminal(
            f"Failed to log activity: {str(e)}",
            {
                'activity_type': activity_type,
                'description': description,
                'error': str(e)
            },
            "ERROR"
        )
        return None


def _make_json_serializable(data):
    """Convert non-serializable objects to serializable format"""
    if data is None:
        return None
    
    if isinstance(data, dict):
        return {k: _make_json_serializable(v) for k, v in data.items()}
    
    if isinstance(data, (list, tuple)):
        return [_make_json_serializable(item) for item in data]
    
    # Handle date and datetime objects
    if hasattr(data, 'isoformat'):
        return data.isoformat()
    
    # Handle model instances
    if hasattr(data, 'pk') and hasattr(data, '__class__'):
        return {
            'id': getattr(data, 'id', None),
            'pk': data.pk,
            'model': data.__class__.__name__
        }
    
    # Handle querysets
    if hasattr(data, '__iter__') and hasattr(data, 'model'):
        return [_make_json_serializable(item) for item in data]
    
    return data


def _check_user_permission(request_user, target_user, action):
    """Check if user has permission to perform action on target_user"""
    try:
        if request_user.is_admin or request_user.is_manager:
            return True
        
        if request_user.is_analyst:
            return request_user.department == target_user.department
        
        return request_user == target_user
    except Exception as e:
        _log_to_terminal(
            f"Error checking user permission: {str(e)}",
            {
                'request_user_id': getattr(request_user, 'id', None),
                'target_user_id': getattr(target_user, 'id', None),
                'action': action,
                'error': str(e)
            },
            "ERROR"
        )
        return False


def _validate_date(date_str, format='%Y-%m-%d'):
    """Validate and parse date string"""
    try:
        if not date_str:
            return None, None
        parsed_date = datetime.strptime(date_str, format)
        return parsed_date, None
    except ValueError as e:
        error_msg = f"Invalid date format. Expected {format}, got: {date_str}"
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error parsing date: {str(e)}"
        return None, error_msg


def _get_object_or_none(model, **kwargs):
    """Safely get an object or return None"""
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
    except Exception as e:
        _log_to_terminal(
            f"Error fetching {model.__name__}: {str(e)}",
            {'filters': kwargs},
            "ERROR"
        )
        return None


# ==================== EMPLOYEE VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_assignments(request):
    """Get assignments for the authenticated employee"""
    start_time = timezone.now()
    request_data = {
        'query_params': dict(request.query_params),
        'user_id': request.user.id,
        'user_email': request.user.email
    }
    _log_to_terminal("GET_MY_ASSIGNMENTS - Request received", request_data)
    
    try:
        user = request.user
        
        # Validate user exists
        if not user or not user.is_authenticated:
            error_msg = "User not authenticated or invalid"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Query parameters
        date_str = request.query_params.get('date')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        department_id = request.query_params.get('department_id')
        
        try:
            # Base queryset - get all assignments for user
            assignments = TaskAssignment.objects.filter(user=user)
            
            # Apply date filters
            if date_str:
                parsed_date, error = _validate_date(date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date=parsed_date.date())
            
            if start_date_str:
                parsed_start, error = _validate_date(start_date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date__gte=parsed_start.date())
            
            if end_date_str:
                parsed_end, error = _validate_date(end_date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date__lte=parsed_end.date())
            
            # Apply status filter
            if status_filter:
                valid_statuses = ['scheduled', 'active', 'completed', 'missed', 'cancelled', 'reassigned']
                if status_filter not in valid_statuses:
                    return Response({
                        'success': False,
                        'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(status=status_filter)
            
            # Apply department filter
            if department_id:
                try:
                    department_id = int(department_id)
                    assignments = assignments.filter(department_id=department_id)
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid department ID format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Order by start_time descending (most recent first)
            assignments = assignments.order_by('-start_time')
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            
            total_count = assignments.count()
            paginated_assignments = assignments[start_idx:end_idx]
            
        except DatabaseError as e:
            _log_to_terminal("GET_MY_ASSIGNMENTS - Database error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Database error occurred while fetching assignments'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Serialize data
        try:
            serializer = TaskAssignmentSerializer(paginated_assignments, many=True)
            response_data = {
                'success': True,
                'assignments': serializer.data,
                'total_count': total_count,
                'page': page,
                'limit': limit,
                'total_pages': (total_count + limit - 1) // limit if limit > 0 else 0
            }
        except Exception as e:
            _log_to_terminal("GET_MY_ASSIGNMENTS - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing assignment data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignments_list',
            user=user,
            description='Viewed assignments list',
            related_user_id=user.id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"GET_MY_ASSIGNMENTS - Completed successfully in {duration:.2f}ms",
            {'count': total_count, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "GET_MY_ASSIGNMENTS - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_assignment(request):
    """Get the current active assignment for the employee"""
    start_time = timezone.now()
    request_data = {
        'user_id': request.user.id,
        'user_email': request.user.email
    }
    _log_to_terminal("GET_CURRENT_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        if not user or not user.is_authenticated:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            current_assignment = TaskAssignmentService.get_current_assignment(user)
        except Exception as e:
            _log_to_terminal("GET_CURRENT_ASSIGNMENT - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error retrieving current assignment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = {
            'success': True,
            'message': 'No current assignment' if not current_assignment else 'Current assignment retrieved',
            'assignment': None
        }
        
        if current_assignment:
            try:
                serializer = TaskAssignmentSerializer(current_assignment)
                response_data['assignment'] = serializer.data
                
                _log_assignment_activity(
                    activity_type='task_assignment_view',
                    user=user,
                    description=f'Viewed current assignment: {current_assignment.task.name}',
                    related_user_id=user.id,
                    related_task_id=current_assignment.task.id,
                    related_assignment_id=current_assignment.id,
                    request=request
                )
            except Exception as e:
                _log_to_terminal("GET_CURRENT_ASSIGNMENT - Serialization error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error processing assignment data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            _log_assignment_activity(
                activity_type='task_assignment_view',
                user=user,
                description='Viewed current assignment (none found)',
                related_user_id=user.id,
                request=request
            )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"GET_CURRENT_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'has_assignment': bool(current_assignment), 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "GET_CURRENT_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_assignment(request):
    """Get the next scheduled assignment for the employee"""
    start_time = timezone.now()
    request_data = {
        'user_id': request.user.id,
        'user_email': request.user.email
    }
    _log_to_terminal("GET_NEXT_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        if not user or not user.is_authenticated:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            next_assignment = TaskAssignmentService.get_next_assignment(user)
        except Exception as e:
            _log_to_terminal("GET_NEXT_ASSIGNMENT - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error retrieving next assignment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = {
            'success': True,
            'message': 'No upcoming assignment' if not next_assignment else 'Next assignment retrieved',
            'assignment': None
        }
        
        if next_assignment:
            try:
                serializer = TaskAssignmentSerializer(next_assignment)
                response_data['assignment'] = serializer.data
                
                _log_assignment_activity(
                    activity_type='task_assignment_view',
                    user=user,
                    description=f'Viewed next assignment: {next_assignment.task.name}',
                    related_user_id=user.id,
                    related_task_id=next_assignment.task.id,
                    related_assignment_id=next_assignment.id,
                    request=request
                )
            except Exception as e:
                _log_to_terminal("GET_NEXT_ASSIGNMENT - Serialization error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error processing assignment data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            _log_assignment_activity(
                activity_type='task_assignment_view',
                user=user,
                description='Viewed next assignment (none found)',
                related_user_id=user.id,
                request=request
            )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"GET_NEXT_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'has_assignment': bool(next_assignment), 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "GET_NEXT_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_assignment(request, assignment_id):
    """Start a task assignment"""
    start_time = timezone.now()
    request_data = {
        'assignment_id': assignment_id,
        'user_id': request.user.id,
        'user_email': request.user.email
    }
    _log_to_terminal("START_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        if not user or not user.is_authenticated:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            assignment_id = int(assignment_id)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid assignment ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = TaskAssignment.objects.get(id=assignment_id, user=user)
        except TaskAssignment.DoesNotExist:
            _log_to_terminal(
                "START_ASSIGNMENT - Assignment not found",
                {'assignment_id': assignment_id, 'user_id': user.id}
            )
            return Response({
                'success': False,
                'message': 'Assignment not found or you do not have permission to start it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if not assignment.can_start:
                return Response({
                    'success': False,
                    'message': 'Assignment cannot be started at this time',
                    'details': {
                        'status': assignment.status,
                        'start_time': assignment.start_time,
                        'end_time': assignment.end_time,
                        'current_time': timezone.now()
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            assignment.start_assignment()
            
        except Exception as e:
            _log_to_terminal("START_ASSIGNMENT - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error starting assignment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            serializer = TaskAssignmentSerializer(assignment)
            response_data = {
                'success': True,
                'message': 'Assignment started successfully',
                'assignment': serializer.data
            }
        except Exception as e:
            _log_to_terminal("START_ASSIGNMENT - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        _log_assignment_activity(
            activity_type='task_assignment_start',
            user=user,
            description=f'Started assignment: {assignment.task.name}',
            related_user_id=user.id,
            related_task_id=assignment.task.id,
            related_assignment_id=assignment.id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"START_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'assignment_id': assignment_id, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "START_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while starting the assignment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_assignment(request, assignment_id):
    """Complete a task assignment"""
    start_time = timezone.now()
    request_data = {
        'assignment_id': assignment_id,
        'user_id': request.user.id,
        'user_email': request.user.email
    }
    _log_to_terminal("COMPLETE_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        if not user or not user.is_authenticated:
            return Response({
                'success': False,
                'message': 'User not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            assignment_id = int(assignment_id)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid assignment ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = TaskAssignment.objects.get(id=assignment_id, user=user)
        except TaskAssignment.DoesNotExist:
            _log_to_terminal(
                "COMPLETE_ASSIGNMENT - Assignment not found",
                {'assignment_id': assignment_id, 'user_id': user.id}
            )
            return Response({
                'success': False,
                'message': 'Assignment not found or you do not have permission to complete it'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if assignment.status != 'active':
            return Response({
                'success': False,
                'message': f'Cannot complete assignment with status: {assignment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment.complete_assignment()
            
            # Get next assignment
            next_assignment = TaskAssignmentService.get_next_assignment(user)
            
        except Exception as e:
            _log_to_terminal("COMPLETE_ASSIGNMENT - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error completing assignment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            serializer = TaskAssignmentSerializer(assignment)
            next_serializer = TaskAssignmentSerializer(next_assignment) if next_assignment else None
            
            response_data = {
                'success': True,
                'message': 'Assignment completed successfully',
                'assignment': serializer.data,
                'next_assignment': next_serializer.data if next_serializer else None
            }
        except Exception as e:
            _log_to_terminal("COMPLETE_ASSIGNMENT - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        _log_assignment_activity(
            activity_type='task_assignment_complete',
            user=user,
            description=f'Completed assignment: {assignment.task.name}',
            related_user_id=user.id,
            related_task_id=assignment.task.id,
            related_assignment_id=assignment.id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"COMPLETE_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'assignment_id': assignment_id, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "COMPLETE_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while completing the assignment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ADMIN/MANAGER VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_assignments(request):
    """Get all assignments (admin/manager/analyst only)"""
    start_time = timezone.now()
    request_data = {
        'query_params': dict(request.query_params),
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("GET_ALL_ASSIGNMENTS - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager or user.is_analyst):
            _log_to_terminal(
                "GET_ALL_ASSIGNMENTS - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'You do not have permission to view all assignments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Query parameters
        date_str = request.query_params.get('date')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        user_id = request.query_params.get('user_id')
        department_id = request.query_params.get('department_id')
        status_filter = request.query_params.get('status')
        
        try:
            # Base queryset
            assignments = TaskAssignment.objects.all()
            
            # Apply date filters
            if date_str:
                parsed_date, error = _validate_date(date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date=parsed_date.date())
            
            if start_date_str:
                parsed_start, error = _validate_date(start_date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date__gte=parsed_start.date())
            
            if end_date_str:
                parsed_end, error = _validate_date(end_date_str)
                if error:
                    return Response({
                        'success': False,
                        'message': error
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(assignment_date__lte=parsed_end.date())
            
            # For analysts, filter to their department only
            if user.is_analyst and not (user.is_admin or user.is_manager):
                if not user.department:
                    return Response({
                        'success': False,
                        'message': 'You are not assigned to any department'
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(department=user.department)
            
            # Apply other filters
            if user_id:
                try:
                    user_id = int(user_id)
                    assignments = assignments.filter(user_id=user_id)
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid user ID format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if department_id:
                try:
                    department_id = int(department_id)
                    assignments = assignments.filter(department_id=department_id)
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid department ID format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            if status_filter:
                valid_statuses = ['scheduled', 'active', 'completed', 'missed', 'cancelled', 'reassigned']
                if status_filter not in valid_statuses:
                    return Response({
                        'success': False,
                        'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                assignments = assignments.filter(status=status_filter)
            
            # Order by most recent first
            assignments = assignments.order_by('-created_at', 'start_time')
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            
            total_count = assignments.count()
            paginated_assignments = assignments[start_idx:end_idx]
            
        except DatabaseError as e:
            _log_to_terminal("GET_ALL_ASSIGNMENTS - Database error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Database error occurred while fetching assignments'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            serializer = TaskAssignmentSerializer(paginated_assignments, many=True)
            response_data = {
                'success': True,
                'assignments': serializer.data,
                'total_count': total_count,
                'page': page,
                'limit': limit,
                'total_pages': (total_count + limit - 1) // limit if limit > 0 else 0
            }
        except Exception as e:
            _log_to_terminal("GET_ALL_ASSIGNMENTS - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing assignment data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignments_list',
            user=user,
            description='Viewed all assignments',
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"GET_ALL_ASSIGNMENTS - Completed in {duration:.2f}ms",
            {'count': total_count, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "GET_ALL_ASSIGNMENTS - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while fetching assignments'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_assignment(request):
    """Create a new task assignment (admin/manager only)"""
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("CREATE_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager or user.is_analyst):
            _log_to_terminal(
                "CREATE_ASSIGNMENT - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'You do not have permission to create assignments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate required fields
        required_fields = ['user_id', 'task_id', 'start_time', 'end_time']
        missing_fields = []
        for field in required_fields:
            if field not in request.data:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            _log_to_terminal("CREATE_ASSIGNMENT - Missing fields", {'missing': missing_fields})
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Parse assignment_date (optional, will default to start_time.date())
            assignment_date = None
            if 'assignment_date' in request.data and request.data['assignment_date']:
                try:
                    assignment_date = datetime.strptime(request.data['assignment_date'], '%Y-%m-%d').date()
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid assignment_date format. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # ============== IMPROVED DATETIME PARSING ==============
            def parse_datetime(dt_str):
                """Parse datetime from various formats and make timezone-aware"""
                if not dt_str:
                    return None
                
                # Remove any surrounding whitespace
                dt_str = dt_str.strip()
                
                try:
                    # Case 1: ISO format with Z suffix (UTC)
                    if 'Z' in dt_str:
                        dt_str = dt_str.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(dt_str)
                    
                    # Case 2: ISO format without Z but with timezone
                    elif '+' in dt_str or '-' in dt_str and 'T' in dt_str:
                        dt = datetime.fromisoformat(dt_str)
                    
                    # Case 3: Local datetime without timezone (add Z for UTC)
                    else:
                        # Add seconds if missing
                        if 'T' in dt_str:
                            parts = dt_str.split('T')
                            date_part = parts[0]
                            time_part = parts[1]
                            
                            # Check if seconds are missing
                            if ':' in time_part and len(time_part.split(':')) == 2:
                                time_part = f"{time_part}:00"
                            
                            dt_str = f"{date_part}T{time_part}"
                        
                        # Parse as naive datetime
                        dt = datetime.fromisoformat(dt_str)
                        
                        # Make timezone-aware (assume UTC)
                        dt = timezone.make_aware(dt, timezone=timezone.utc)
                    
                    return dt
                    
                except (ValueError, AttributeError) as e:
                    _log_to_terminal("CREATE_ASSIGNMENT - Datetime parse error", 
                                   {'error': str(e), 'value': dt_str}, "ERROR")
                    raise ValueError(f"Invalid datetime format: {dt_str}")
            
            # Parse start and end times
            try:
                start_time_val = parse_datetime(request.data['start_time'])
                end_time_val = parse_datetime(request.data['end_time'])
            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate time range
            if start_time_val >= end_time_val:
                return Response({
                    'success': False,
                    'message': 'Start time must be before end time'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate that end time is not in the past (allow for future dates)
            now = timezone.now()
            if end_time_val < now:
                return Response({
                    'success': False,
                    'message': f'End time ({end_time_val.strftime("%Y-%m-%d %H:%M")}) cannot be in the past'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set assignment_date to start_time.date() if not provided
            if not assignment_date:
                assignment_date = start_time_val.date()
            
            # Get related objects
            try:
                assigned_user = CustomUser.objects.get(id=request.data['user_id'])
            except CustomUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'User with ID {request.data["user_id"]} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            try:
                task = Task.objects.get(id=request.data['task_id'])
            except Task.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Task with ID {request.data["task_id"]} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is employee
            if assigned_user.role != 'employee':
                return Response({
                    'success': False,
                    'message': 'Assignments can only be created for employees'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user has department
            if not assigned_user.department:
                return Response({
                    'success': False,
                    'message': 'Cannot assign task to employee without a department'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check permission for analysts
            if user.is_analyst and not (user.is_admin or user.is_manager):
                if not assigned_user.department or assigned_user.department != user.department:
                    return Response({
                        'success': False,
                        'message': 'You can only assign tasks to users in your department'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate priority
            priority = request.data.get('priority', 'medium')
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if priority not in valid_priorities:
                return Response({
                    'success': False,
                    'message': f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle department_id
            department_id = request.data.get('department_id')
            if department_id:
                try:
                    department_id = int(department_id)
                    # Verify department exists
                    department = Department.objects.get(id=department_id)
                    # Verify department matches user's department
                    if assigned_user.department.id != department_id:
                        return Response({
                            'success': False,
                            'message': f'Selected department does not match employee\'s department ({assigned_user.department.name})'
                        }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({
                        'success': False,
                        'message': 'Invalid department ID format'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Department.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': f'Department with ID {department_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                department_id = assigned_user.department.id
            
            # Check for conflicting assignments (overlapping times)
            conflicting = TaskAssignment.objects.filter(
                user=assigned_user,
                status__in=['scheduled', 'active']
            ).filter(
                models.Q(start_time__lt=end_time_val, end_time__gt=start_time_val)
            )
            
            if conflicting.exists():
                conflict = conflicting.first()
                return Response({
                    'success': False,
                    'message': f'Time conflict with existing assignment: {conflict.task.name} ({conflict.start_time.strftime("%Y-%m-%d %H:%M")} - {conflict.end_time.strftime("%Y-%m-%d %H:%M")})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get next sequence order (only relevant if same day)
            sequence_order = 1
            if start_time_val.date() == end_time_val.date():
                last_assignment = TaskAssignment.objects.filter(
                    user=assigned_user,
                    assignment_date=start_time_val.date()
                ).order_by('-sequence_order').first()
                sequence_order = (last_assignment.sequence_order + 1) if last_assignment else 1
            
            # Create assignment
            try:
                assignment = TaskAssignment.objects.create(
                    user=assigned_user,
                    task=task,
                    department_id=department_id,
                    assignment_date=assignment_date,
                    start_time=start_time_val,
                    end_time=end_time_val,
                    priority=priority,
                    sequence_order=sequence_order,
                    assigned_by=user,
                    notes=request.data.get('notes', ''),
                    status='scheduled'
                )
                
                _log_to_terminal("CREATE_ASSIGNMENT - Assignment created", 
                               {'assignment_id': assignment.id, 'user': assigned_user.full_name, 'task': task.name}, 
                               level="INFO")
                
            except ValidationError as e:
                _log_to_terminal("CREATE_ASSIGNMENT - Validation error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                _log_to_terminal("CREATE_ASSIGNMENT - Integrity error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Assignment with this sequence order already exists for this date'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                _log_to_terminal("CREATE_ASSIGNMENT - Database error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': f'Error creating assignment: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except (CustomUser.DoesNotExist, Task.DoesNotExist, Department.DoesNotExist) as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== SERIALIZATION ==============
        try:
            serializer = TaskAssignmentSerializer(assignment)
            response_data = {
                'success': True,
                'message': 'Assignment created successfully',
                'assignment': serializer.data
            }
            
            _log_to_terminal("CREATE_ASSIGNMENT - Serialization successful", 
                           {'assignment_id': assignment.id}, 
                           level="INFO")
            
        except Exception as e:
            _log_to_terminal("CREATE_ASSIGNMENT - Serialization error", 
                           {'error': str(e), 'traceback': traceback.format_exc()}, 
                           "ERROR")
            
            # Try to serialize without calculated fields as fallback
            try:
                # Create a simple dict with basic fields
                basic_data = {
                    'id': assignment.id,
                    'user': assignment.user.id,
                    'task': assignment.task.id,
                    'department': assignment.department.id if assignment.department else None,
                    'assignment_date': str(assignment.assignment_date),
                    'start_time': assignment.start_time.isoformat(),
                    'end_time': assignment.end_time.isoformat(),
                    'status': assignment.status,
                    'priority': assignment.priority,
                    'notes': assignment.notes
                }
                
                response_data = {
                    'success': True,
                    'message': 'Assignment created successfully',
                    'assignment': basic_data
                }
                
                _log_to_terminal("CREATE_ASSIGNMENT - Fallback serialization used", 
                               {'assignment_id': assignment.id}, 
                               level="WARNING")
                
            except Exception as fallback_error:
                _log_to_terminal("CREATE_ASSIGNMENT - Fallback serialization failed", 
                               {'error': str(fallback_error)}, 
                               "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error processing response data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignment_create',
            user=user,
            description=f'Created assignment: {task.name} for {assigned_user.full_name} ({start_time_val.strftime("%Y-%m-%d %H:%M")} - {end_time_val.strftime("%Y-%m-%d %H:%M")})',
            related_user_id=assigned_user.id,
            related_task_id=task.id,
            related_assignment_id=assignment.id,
            related_department_id=department_id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"CREATE_ASSIGNMENT - Completed in {duration:.2f}ms",
            {
                'assignment_id': assignment.id,
                'user_id': assigned_user.id,
                'task_id': task.id,
                'duration_ms': duration
            },
            level="INFO"
        )
        _log_to_terminal("=" * 100, level="SEPARATOR")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        duration = (timezone.now() - start_time).total_seconds() * 1000
        
        _log_to_terminal(
            "CREATE_ASSIGNMENT - Unexpected error",
            {
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': error_trace,
                'request_data': request_data,
                'duration_ms': f"{duration:.2f}"
            },
            "CRITICAL"
        )
        _log_to_terminal("=" * 100, level="SEPARATOR")
        
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while creating the assignment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def modify_assignment(request):
    """Modify a task assignment (admin/manager/analyst only)"""
    start_time = timezone.now()
    request_data = {
        'method': request.method,
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("MODIFY_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager or user.is_analyst):
            _log_to_terminal(
                "MODIFY_ASSIGNMENT - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'You do not have permission to modify assignments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate serializer
        serializer = TaskAssignmentModifySerializer(data=request.data)
        if not serializer.is_valid():
            _log_to_terminal(
                "MODIFY_ASSIGNMENT - Validation failed",
                {'errors': serializer.errors}
            )
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify assignment exists
            assignment_id = serializer.validated_data['assignment_id']
            assignment = TaskAssignment.objects.get(id=assignment_id)
            
            # Check permission for analysts
            if user.is_analyst and not (user.is_admin or user.is_manager):
                if not assignment.department or assignment.department != user.department:
                    return Response({
                        'success': False,
                        'message': 'You can only modify assignments in your department'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Modify assignment using service
            modified_assignment = TaskAssignmentService.modify_assignment(
                assignment_id=assignment_id,
                modified_by=user,
                new_task_id=serializer.validated_data.get('new_task_id'),
                new_start_time=serializer.validated_data.get('new_start_time'),
                new_end_time=serializer.validated_data.get('new_end_time'),
                new_notes=serializer.validated_data.get('notes'),
                reason=serializer.validated_data.get('reason', 'No reason provided')
            )
            
        except TaskAssignment.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Assignment with ID {assignment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            _log_to_terminal("MODIFY_ASSIGNMENT - Permission error", {'error': str(e)})
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            _log_to_terminal("MODIFY_ASSIGNMENT - Validation error", {'error': str(e)})
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            _log_to_terminal("MODIFY_ASSIGNMENT - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error modifying assignment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            result_serializer = TaskAssignmentSerializer(modified_assignment)
            response_data = {
                'success': True,
                'message': 'Assignment modified successfully',
                'assignment': result_serializer.data
            }
        except Exception as e:
            _log_to_terminal("MODIFY_ASSIGNMENT - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignment_update',
            user=user,
            description=f'Modified assignment for {modified_assignment.user.full_name}',
            related_user_id=modified_assignment.user.id,
            related_task_id=modified_assignment.task.id,
            related_assignment_id=modified_assignment.id,
            related_department_id=modified_assignment.department.id if modified_assignment.department else None,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"MODIFY_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'assignment_id': assignment_id, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "MODIFY_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while modifying the assignment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_assignment(request, assignment_id):
    """Delete a task assignment (admin/manager only)"""
    start_time = timezone.now()
    request_data = {
        'assignment_id': assignment_id,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("DELETE_ASSIGNMENT - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager):
            _log_to_terminal(
                "DELETE_ASSIGNMENT - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'Only admins and managers can delete assignments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            assignment_id = int(assignment_id)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid assignment ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment = TaskAssignment.objects.get(id=assignment_id)
        except TaskAssignment.DoesNotExist:
            _log_to_terminal(
                "DELETE_ASSIGNMENT - Assignment not found",
                {'assignment_id': assignment_id}
            )
            return Response({
                'success': False,
                'message': f'Assignment with ID {assignment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if assignment can be deleted
        if assignment.status == 'active':
            return Response({
                'success': False,
                'message': 'Cannot delete an active assignment'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store info for logging
        assignment_info = {
            'user': assignment.user.full_name,
            'user_id': assignment.user.id,
            'task': assignment.task.name,
            'task_id': assignment.task.id,
            'date': str(assignment.assignment_date),
            'status': assignment.status
        }
        
        try:
            assignment.delete()
        except DatabaseError as e:
            _log_to_terminal("DELETE_ASSIGNMENT - Delete error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error deleting assignment from database'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = {
            'success': True,
            'message': 'Assignment deleted successfully',
            'deleted_assignment': assignment_info
        }
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignment_delete',
            user=user,
            description=f'Deleted assignment: {assignment_info["task"]} for {assignment_info["user"]}',
            related_user_id=assignment_info['user_id'],
            related_task_id=assignment_info['task_id'],
            related_assignment_id=assignment_id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"DELETE_ASSIGNMENT - Completed in {duration:.2f}ms",
            {'assignment_id': assignment_id, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "DELETE_ASSIGNMENT - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while deleting the assignment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_department_assignments(request):
    """Create assignments for a department based on templates (admin/manager only)"""
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("CREATE_DEPARTMENT_ASSIGNMENTS - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager):
            _log_to_terminal(
                "CREATE_DEPARTMENT_ASSIGNMENTS - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'Only admins and managers can create department assignments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate required fields
        date_str = request.data.get('date')
        department_id = request.data.get('department_id')
        
        if not date_str:
            return Response({
                'success': False,
                'message': 'date is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not department_id:
            return Response({
                'success': False,
                'message': 'department_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date
        try:
            assignment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get department
        try:
            department_id = int(department_id)
            department = Department.objects.get(id=department_id)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid department ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Department.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Department with ID {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if department is active
        if department.status != 'active':
            return Response({
                'success': False,
                'message': f'Department {department.name} is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if department has templates
        try:
            templates = TaskAssignmentTemplate.objects.filter(
                department=department,
                is_active=True
            )
            if not templates.exists():
                return Response({
                    'success': False,
                    'message': f'No active templates found for department {department.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            _log_to_terminal("CREATE_DEPARTMENT_ASSIGNMENTS - Template error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error checking assignment templates'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create assignments using service
        try:
            assignments = TaskAssignmentService.create_daily_assignments_for_department(
                date=assignment_date,
                department=department,
                assigned_by=user
            )
        except Exception as e:
            _log_to_terminal("CREATE_DEPARTMENT_ASSIGNMENTS - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error creating assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        response_data = {
            'success': True,
            'message': f'Successfully created {len(assignments)} assignments',
            'date': str(assignment_date),
            'department': department.name,
            'department_id': department.id,
            'count': len(assignments)
        }
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignment_bulk_create',
            user=user,
            description=f'Created {len(assignments)} assignments for department {department.name} on {assignment_date}',
            related_department_id=department.id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"CREATE_DEPARTMENT_ASSIGNMENTS - Completed in {duration:.2f}ms",
            {
                'department_id': department.id,
                'date': str(assignment_date),
                'count': len(assignments),
                'duration_ms': duration
            }
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "CREATE_DEPARTMENT_ASSIGNMENTS - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while creating department assignments'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== TASK ASSIGNMENT TEMPLATE VIEWS ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_assignment_templates(request):
    """Get all or create task assignment template (admin/manager only)"""
    start_time = timezone.now()
    request_data = {
        'method': request.method,
        'body': request.data if request.method == 'POST' else None,
        'query_params': dict(request.query_params) if request.method == 'GET' else None,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("MANAGE_ASSIGNMENT_TEMPLATES - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager):
            _log_to_terminal(
                "MANAGE_ASSIGNMENT_TEMPLATES - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'Only admins and managers can manage assignment templates'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            try:
                templates = TaskAssignmentTemplate.objects.all()
                
                # For analysts, filter to their department
                if user.is_analyst and not (user.is_admin or user.is_manager):
                    if user.department:
                        templates = templates.filter(department=user.department)
                
                serializer = TaskAssignmentTemplateSerializer(templates, many=True)
                
                response_data = {
                    'success': True,
                    'templates': serializer.data,
                    'count': templates.count()
                }
                
                # Log activity
                _log_assignment_activity(
                    activity_type='task_assignments_list',
                    user=user,
                    description='Viewed assignment templates list',
                    request=request,
                    request_data=request_data,
                    response_data=response_data
                )
                
                duration = (timezone.now() - start_time).total_seconds() * 1000
                _log_to_terminal(
                    f"MANAGE_ASSIGNMENT_TEMPLATES - GET completed in {duration:.2f}ms",
                    {'count': templates.count(), 'duration_ms': duration}
                )
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except DatabaseError as e:
                _log_to_terminal("MANAGE_ASSIGNMENT_TEMPLATES - Database error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error fetching templates from database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif request.method == 'POST':
            try:
                serializer = TaskAssignmentTemplateSerializer(data=request.data)
                
                if not serializer.is_valid():
                    _log_to_terminal(
                        "MANAGE_ASSIGNMENT_TEMPLATES - Validation failed",
                        {'errors': serializer.errors}
                    )
                    return Response({
                        'success': False,
                        'message': 'Invalid template data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verify department exists
                department_id = request.data.get('department')
                if department_id:
                    try:
                        department = Department.objects.get(id=department_id)
                        if department.status != 'active':
                            return Response({
                                'success': False,
                                'message': f'Cannot create template for inactive department: {department.name}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    except Department.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': f'Department with ID {department_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # Verify task exists
                task_id = request.data.get('task')
                if task_id:
                    try:
                        task = Task.objects.get(id=task_id)
                    except Task.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': f'Task with ID {task_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # Check for duplicate template
                existing = TaskAssignmentTemplate.objects.filter(
                    department_id=department_id,
                    task_id=task_id,
                    start_time=request.data.get('start_time')
                ).exists()
                
                if existing:
                    return Response({
                        'success': False,
                        'message': 'A template with these settings already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                template = serializer.save(created_by=user)
                
            except (Department.DoesNotExist, Task.DoesNotExist) as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_404_NOT_FOUND)
            except IntegrityError as e:
                _log_to_terminal("MANAGE_ASSIGNMENT_TEMPLATES - Integrity error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'A template with these settings already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            except DatabaseError as e:
                _log_to_terminal("MANAGE_ASSIGNMENT_TEMPLATES - Database error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error saving template to database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            try:
                response_serializer = TaskAssignmentTemplateSerializer(template)
                response_data = {
                    'success': True,
                    'message': 'Assignment template created successfully',
                    'template': response_serializer.data
                }
            except Exception as e:
                _log_to_terminal("MANAGE_ASSIGNMENT_TEMPLATES - Serialization error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error processing response data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Log activity
            _log_assignment_activity(
                activity_type='task_assignment_create',
                user=user,
                description=f'Created assignment template: {template.name}',
                related_department_id=template.department.id if template.department else None,
                related_task_id=template.task.id,
                request=request,
                request_data=request_data,
                response_data=response_data
            )
            
            duration = (timezone.now() - start_time).total_seconds() * 1000
            _log_to_terminal(
                f"MANAGE_ASSIGNMENT_TEMPLATES - POST completed in {duration:.2f}ms",
                {'template_id': template.id, 'duration_ms': duration}
            )
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "MANAGE_ASSIGNMENT_TEMPLATES - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while managing templates'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== TASK OVERLOAD VIEWS ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_task_overloads(request):
    """Get all or create task overload (admin/manager/analyst)"""
    start_time = timezone.now()
    request_data = {
        'method': request.method,
        'body': request.data if request.method == 'POST' else None,
        'query_params': dict(request.query_params) if request.method == 'GET' else None,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("MANAGE_TASK_OVERLOADS - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager or user.is_analyst):
            _log_to_terminal(
                "MANAGE_TASK_OVERLOADS - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'You do not have permission to manage task overloads'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            try:
                # Get all unresolved overloads
                overloads = TaskOverload.objects.filter(is_resolved=False)
                
                # For analysts, filter to their department
                if user.is_analyst and not (user.is_admin or user.is_manager):
                    if not user.department:
                        return Response({
                            'success': False,
                            'message': 'You are not assigned to any department'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    overloads = overloads.filter(department=user.department)
                
                serializer = TaskOverloadSerializer(overloads, many=True)
                
                response_data = {
                    'success': True,
                    'overloads': serializer.data,
                    'count': overloads.count()
                }
                
                # Log activity
                _log_assignment_activity(
                    activity_type='task_assignments_list',
                    user=user,
                    description='Viewed task overloads list',
                    request=request,
                    request_data=request_data,
                    response_data=response_data
                )
                
                duration = (timezone.now() - start_time).total_seconds() * 1000
                _log_to_terminal(
                    f"MANAGE_TASK_OVERLOADS - GET completed in {duration:.2f}ms",
                    {'count': overloads.count(), 'duration_ms': duration}
                )
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except DatabaseError as e:
                _log_to_terminal("MANAGE_TASK_OVERLOADS - Database error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error fetching overloads from database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif request.method == 'POST':
            try:
                # Normalize request data - map task to task_id if needed
                normalized_data = dict(request.data)
                
                # Handle field name mapping
                if 'task' in normalized_data and 'task_id' not in normalized_data:
                    normalized_data['task_id'] = normalized_data['task']
                
                # Handle department filtering for analysts
                if user.is_analyst and not (user.is_admin or user.is_manager):
                    if not user.department:
                        return Response({
                            'success': False,
                            'message': 'You are not assigned to any department'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    if 'department' in normalized_data or 'department_id' in normalized_data:
                        dept_id = normalized_data.get('department') or normalized_data.get('department_id')
                        try:
                            dept_id = int(dept_id)
                            if dept_id != user.department.id:
                                return Response({
                                    'success': False,
                                    'message': 'You can only create overloads for your department'
                                }, status=status.HTTP_403_FORBIDDEN)
                        except (ValueError, TypeError):
                            return Response({
                                'success': False,
                                'message': 'Invalid department ID format'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        normalized_data['department_id'] = user.department.id
                
                # Verify department exists
                dept_id = normalized_data.get('department_id') or normalized_data.get('department')
                if dept_id:
                    try:
                        dept_id = int(dept_id)
                        department = Department.objects.get(id=dept_id)
                        if department.status != 'active':
                            return Response({
                                'success': False,
                                'message': f'Cannot create overload for inactive department: {department.name}'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    except ValueError:
                        return Response({
                            'success': False,
                            'message': 'Invalid department ID format'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    except Department.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': f'Department with ID {dept_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                # Verify task exists
                task_id = normalized_data.get('task_id') or normalized_data.get('task')
                if task_id:
                    try:
                        task_id = int(task_id)
                        task = Task.objects.get(id=task_id)
                    except ValueError:
                        return Response({
                            'success': False,
                            'message': 'Invalid task ID format'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    except Task.DoesNotExist:
                        return Response({
                            'success': False,
                            'message': f'Task with ID {task_id} not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                
                serializer = TaskOverloadSerializer(data=normalized_data)
                
                if not serializer.is_valid():
                    _log_to_terminal(
                        "MANAGE_TASK_OVERLOADS - Validation failed",
                        {'errors': serializer.errors}
                    )
                    return Response({
                        'success': False,
                        'message': 'Invalid overload data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                overload = serializer.save(created_by=user)
                
            except (Department.DoesNotExist, Task.DoesNotExist) as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_404_NOT_FOUND)
            except IntegrityError as e:
                _log_to_terminal("MANAGE_TASK_OVERLOADS - Integrity error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'A similar overload already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            except DatabaseError as e:
                _log_to_terminal("MANAGE_TASK_OVERLOADS - Database error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error saving overload to database'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            try:
                response_serializer = TaskOverloadSerializer(overload)
                response_data = {
                    'success': True,
                    'message': 'Task overload created successfully',
                    'overload': response_serializer.data
                }
            except Exception as e:
                _log_to_terminal("MANAGE_TASK_OVERLOADS - Serialization error", {'error': str(e)}, "ERROR")
                return Response({
                    'success': False,
                    'message': 'Error processing response data'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Log activity
            _log_assignment_activity(
                activity_type='task_assignment_create',
                user=user,
                description=f'Created task overload for {task.name}',
                related_department_id=overload.department.id if overload.department else None,
                related_task_id=overload.task.id,
                request=request,
                request_data=request_data,
                response_data=response_data
            )
            
            duration = (timezone.now() - start_time).total_seconds() * 1000
            _log_to_terminal(
                f"MANAGE_TASK_OVERLOADS - POST completed in {duration:.2f}ms",
                {'overload_id': overload.id, 'duration_ms': duration}
            )
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "MANAGE_TASK_OVERLOADS - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while managing task overloads'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_task_overload(request, overload_id):
    """Mark task overload as resolved (admin/manager/analyst)"""
    start_time = timezone.now()
    request_data = {
        'overload_id': overload_id,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    _log_to_terminal("RESOLVE_TASK_OVERLOAD - Request received", request_data)
    
    try:
        user = request.user
        
        # Check permissions
        if not (user.is_admin or user.is_manager or user.is_analyst):
            _log_to_terminal(
                "RESOLVE_TASK_OVERLOAD - Permission denied",
                {'user_id': user.id, 'user_role': getattr(user, 'role', None)}
            )
            return Response({
                'success': False,
                'message': 'You do not have permission to resolve task overloads'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            overload_id = int(overload_id)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid overload ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            overload = TaskOverload.objects.get(id=overload_id)
        except TaskOverload.DoesNotExist:
            _log_to_terminal(
                "RESOLVE_TASK_OVERLOAD - Overload not found",
                {'overload_id': overload_id}
            )
            return Response({
                'success': False,
                'message': f'Task overload with ID {overload_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permission for analysts
        if user.is_analyst and not (user.is_admin or user.is_manager):
            if not overload.department or overload.department != user.department:
                return Response({
                    'success': False,
                    'message': 'You can only resolve overloads in your department'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if already resolved
        if overload.is_resolved:
            serializer = TaskOverloadSerializer(overload)
            response_data = {
                'success': True,
                'message': 'Task overload is already resolved',
                'overload': serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        try:
            # Mark as resolved
            overload.is_resolved = True
            overload.resolved_at = timezone.now()
            overload.save(update_fields=['is_resolved', 'resolved_at'])
            
            serializer = TaskOverloadSerializer(overload)
            
            response_data = {
                'success': True,
                'message': 'Task overload resolved successfully',
                'overload': serializer.data
            }
        except DatabaseError as e:
            _log_to_terminal("RESOLVE_TASK_OVERLOAD - Save error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error saving resolved overload'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        _log_assignment_activity(
            activity_type='task_assignment_update',
            user=user,
            description=f'Resolved task overload for {overload.task.name}',
            related_department_id=overload.department.id if overload.department else None,
            related_task_id=overload.task.id,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"RESOLVE_TASK_OVERLOAD - Completed in {duration:.2f}ms",
            {'overload_id': overload_id, 'duration_ms': duration}
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "RESOLVE_TASK_OVERLOAD - Unexpected error",
            {'error': str(e), 'traceback': error_trace},
            "ERROR"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while resolving the task overload'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== BULK ASSIGNMENT ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_assign_task(request):
    """
    Bulk assign a task to multiple users
    Supports: department, specific users, all employees, all users
    """
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    
    _log_to_terminal("BULK_ASSIGN_TASK - REQUEST RECEIVED", request_data, level="INFO")
    
    try:
        # ============== PERMISSION CHECK ==============
        user = request.user
        
        if not user or not user.is_authenticated:
            error_msg = "User not authenticated"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (user.is_admin or user.is_manager):
            error_msg = "Only admins and managers can perform bulk task assignments"
            _log_to_terminal("BULK_ASSIGN_TASK - Permission denied", 
                           {'user_id': user.id, 'user_role': getattr(user, 'role', None)}, 
                           level="WARNING")
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ============== SERIALIZER VALIDATION ==============
        serializer = BulkAssignmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            validation_errors = serializer.errors
            _log_to_terminal("BULK_ASSIGN_TASK - Validation failed", 
                           {'errors': validation_errors}, 
                           level="WARNING")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        validated_data = serializer.validated_data
        
        # ============== DATE/TIME VALIDATION ==============
        start_time_val = validated_data['start_time']
        end_time_val = validated_data['end_time']
        
        if start_time_val >= end_time_val:
            error_msg = 'Start time must be before end time'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_time_val < timezone.now():
            error_msg = 'End time cannot be in the past'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== TASK VALIDATION ==============
        task_id = validated_data['task_id']
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            error_msg = f"Task with ID {task_id} not found"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ============== BULK ASSIGNMENT EXECUTION ==============
        try:
            result = TaskAssignmentService.create_bulk_assignments(
                task_id=task_id,
                start_time=start_time_val,
                end_time=end_time_val,
                assigned_by=user,
                priority=validated_data.get('priority', 'medium'),
                assignment_date=validated_data.get('assignment_date'),
                notes=validated_data.get('notes'),
                department_id=validated_data.get('department_id'),
                user_ids=validated_data.get('user_ids'),
                assign_to_all_employees=validated_data.get('assign_to_all_employees', False),
                assign_to_all_users=validated_data.get('assign_to_all_users', False)
            )
            
            _log_to_terminal("BULK_ASSIGN_TASK - Bulk assignment completed", 
                           {
                               'created_count': result['created_count'],
                               'skipped_count': result['skipped_count'],
                               'failed_count': result['failed_count']
                           }, 
                           level="INFO")
            
        except ValueError as e:
            error_msg = str(e)
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        except Department.DoesNotExist:
            error_msg = f"Department with ID {validated_data.get('department_id')} not found"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            error_msg = "One or more selected users do not exist"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            error_msg = f"Service error: {str(e)}"
            _log_to_terminal("BULK_ASSIGN_TASK - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error creating bulk assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== RESPONSE SERIALIZATION ==============
        try:
            assignment_serializer = TaskAssignmentSerializer(result['created'], many=True)
            response_data = {
                'success': True,
                'message': f'Successfully created {result["created_count"]} assignments',
                'task': {
                    'id': result['task'].id,
                    'name': result['task'].name
                },
                'created_count': result['created_count'],
                'skipped_count': result['skipped_count'],
                'failed_count': result['failed_count'],
                'total_targeted': result['total_targeted'],
                'created_assignments': assignment_serializer.data,
                'skipped_assignments': result['skipped'],
                'failed_assignments': result['failed']
            }
        except Exception as e:
            _log_to_terminal("BULK_ASSIGN_TASK - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== LOG ACTIVITY ==============
        try:
            _log_assignment_activity(
                activity_type='task_assignment_bulk_create',
                user=user,
                description=f'Bulk assigned task "{result["task"].name}" to {result["created_count"]} users',
                related_task_id=result['task'].id,
                request=request,
                request_data=_make_json_serializable(request_data),
                response_data=_make_json_serializable(response_data)
            )
        except Exception as e:
            _log_to_terminal("BULK_ASSIGN_TASK - Activity logging failed", 
                           {'error': str(e)}, 
                           level="WARNING")
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"BULK_ASSIGN_TASK - COMPLETED SUCCESSFULLY in {duration:.2f}ms",
            {
                'task_id': result['task'].id,
                'task_name': result['task'].name,
                'created': result['created_count']
            }, 
            level="INFO"
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "BULK_ASSIGN_TASK - UNEXPECTED ERROR",
            {'error': str(e), 'traceback': error_trace},
            level="CRITICAL"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while bulk assigning tasks. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_task_to_department(request):
    """
    Assign a task to all employees in a specific department
    """
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    
    # Log incoming request
    _log_to_terminal("=" * 100, level="SEPARATOR")
    _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - REQUEST RECEIVED", request_data, level="INFO")
    
    try:
        # ============== PERMISSION CHECK ==============
        try:
            user = request.user
            
            if not user or not user.is_authenticated:
                error_msg = "User not authenticated"
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Authentication failed", 
                               {'error': error_msg}, 
                               level="ERROR")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not (user.is_admin or user.is_manager):
                error_msg = "Only admins and managers can assign tasks to departments"
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Permission denied", 
                               {'user_id': user.id, 'user_role': getattr(user, 'role', None)}, 
                               level="WARNING")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_403_FORBIDDEN)
                
        except AttributeError as e:
            error_msg = f"User permission attributes error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Permission check error", 
                           {'error': error_msg, 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': 'Error checking user permissions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== SERIALIZER VALIDATION ==============
        try:
            # Pre-process datetime fields to ensure they have seconds
            modified_data = request.data.copy()
            
            # Fix start_time format
            if 'start_time' in modified_data:
                start_time_str = modified_data['start_time']
                if isinstance(start_time_str, str) and 'T' in start_time_str:
                    # Check if seconds are missing
                    time_part = start_time_str.split('T')[1]
                    if ':' in time_part and len(time_part.split(':')) == 2:
                        # Add seconds and Z
                        modified_data['start_time'] = f"{start_time_str}:00Z"
                    elif not time_part.endswith('Z'):
                        modified_data['start_time'] = f"{start_time_str}Z"
            
            # Fix end_time format
            if 'end_time' in modified_data:
                end_time_str = modified_data['end_time']
                if isinstance(end_time_str, str) and 'T' in end_time_str:
                    time_part = end_time_str.split('T')[1]
                    if ':' in time_part and len(time_part.split(':')) == 2:
                        modified_data['end_time'] = f"{end_time_str}:00Z"
                    elif not time_part.endswith('Z'):
                        modified_data['end_time'] = f"{end_time_str}Z"
            
            serializer = DepartmentBulkAssignmentSerializer(data=modified_data)
            
            if not serializer.is_valid():
                validation_errors = serializer.errors
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Validation failed", 
                               {'errors': validation_errors, 'request_data': request.data}, 
                               level="WARNING")
                return Response({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
            validated = serializer.validated_data
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Validation successful", 
                           {'validated_data': validated}, 
                           level="INFO")
            
        except Exception as e:
            error_msg = f"Serializer validation error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Serializer error", 
                           {'error': error_msg, 'traceback': traceback.format_exc(), 'request_data': request.data}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': 'Error validating request data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== DEPARTMENT VALIDATION ==============
        try:
            department_id = validated['department_id']
            try:
                department = Department.objects.get(id=department_id)
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department found", 
                               {'department_id': department_id, 'department_name': department.name, 'department_status': department.status}, 
                               level="INFO")
                
                # Check if department is active
                if department.status != 'active':
                    error_msg = f"Department '{department.name}' is not active"
                    _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department inactive", 
                                   {'department_id': department_id, 'department_name': department.name, 'status': department.status}, 
                                   level="WARNING")
                    return Response({
                        'success': False,
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Department.DoesNotExist:
                error_msg = f"Department with ID {department_id} not found"
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department not found", 
                               {'department_id': department_id}, 
                               level="ERROR")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
                
        except KeyError as e:
            error_msg = f"Missing department_id field"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Missing department_id", 
                           {'error': str(e), 'validated_data': validated}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': 'Department ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== TASK VALIDATION ==============
        try:
            task_id = validated['task_id']
            try:
                task = Task.objects.get(id=task_id)
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Task found", 
                               {'task_id': task_id, 'task_name': task.name, 'task_status': task.status}, 
                               level="INFO")
                
                # Check if task is active
                if task.status != 'active':
                    error_msg = f"Task '{task.name}' is not active"
                    _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Task inactive", 
                                   {'task_id': task_id, 'task_name': task.name, 'status': task.status}, 
                                   level="WARNING")
                    return Response({
                        'success': False,
                        'message': error_msg
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Task.DoesNotExist:
                error_msg = f"Task with ID {task_id} not found"
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Task not found", 
                               {'task_id': task_id}, 
                               level="ERROR")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_404_NOT_FOUND)
                
        except KeyError as e:
            error_msg = f"Missing task_id field"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Missing task_id", 
                           {'error': str(e), 'validated_data': validated}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': 'Task ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== DATE/TIME VALIDATION ==============
        try:
            start_time_val = validated['start_time']
            end_time_val = validated['end_time']
            
            # Ensure we're working with timezone-aware datetimes
            if timezone.is_naive(start_time_val):
                start_time_val = timezone.make_aware(start_time_val)
            if timezone.is_naive(end_time_val):
                end_time_val = timezone.make_aware(end_time_val)
            
            # Validate time range
            if start_time_val >= end_time_val:
                error_msg = 'Start time must be before end time'
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Time validation failed", 
                               {'start_time': str(start_time_val), 'end_time': str(end_time_val)}, 
                               level="WARNING")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if end_time_val < timezone.now():
                error_msg = 'End time cannot be in the past'
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Time validation failed", 
                               {'end_time': str(end_time_val), 'current_time': str(timezone.now())}, 
                               level="WARNING")
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except KeyError as e:
            error_msg = f"Missing date/time field: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Missing date/time field", 
                           {'error': error_msg}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = f"Date/time validation error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Date/time validation error", 
                           {'error': error_msg, 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': f'Invalid date/time format. Please use ISO format (YYYY-MM-DDTHH:MM:SSZ)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== CHECK DEPARTMENT EMPLOYEES ==============
        try:
            # Check if department has any active employees
            active_employees = CustomUser.objects.filter(
                department=department,
                role='employee',
                is_active=True,
                status='approved'
            )
            
            total_employees = active_employees.count()
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department employees count", 
                           {'department_id': department.id, 'department_name': department.name, 'total_employees': total_employees}, 
                           level="INFO")
            
            if total_employees == 0:
                error_msg = f"No active employees found in department '{department.name}'"
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - No employees available", 
                               {'department_id': department.id, 'department_name': department.name}, 
                               level="WARNING")
                
                return Response({
                    'success': False,
                    'message': error_msg,
                    'department': {
                        'id': department.id,
                        'name': department.name
                    },
                    'created_count': 0,
                    'skipped_count': 0,
                    'failed_count': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Apply exclusions
            exclude_user_ids = validated.get('exclude_user_ids', [])
            if exclude_user_ids:
                active_employees = active_employees.exclude(id__in=exclude_user_ids)
                remaining_count = active_employees.count()
                
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - After exclusions", 
                               {'excluded_count': len(exclude_user_ids), 'remaining_count': remaining_count}, 
                               level="INFO")
                
                if remaining_count == 0:
                    error_msg = f"No employees available in department '{department.name}' after excluding {len(exclude_user_ids)} user(s)"
                    _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - No employees after exclusions", 
                                   {'department_id': department.id, 'department_name': department.name, 'excluded': exclude_user_ids}, 
                                   level="WARNING")
                    
                    return Response({
                        'success': False,
                        'message': error_msg,
                        'department': {
                            'id': department.id,
                            'name': department.name
                        },
                        'created_count': 0,
                        'skipped_count': 0,
                        'failed_count': 0
                    }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Employee check error", 
                           {'error': str(e), 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            # Continue anyway, let the service handle it
        
        # ============== DEPARTMENT ASSIGNMENT EXECUTION ==============
        try:
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Starting department assignment", 
                           {
                               'task_id': task_id,
                               'task_name': task.name,
                               'department_id': department_id,
                               'department_name': department.name,
                               'start_time': str(start_time_val),
                               'end_time': str(end_time_val),
                               'assigned_by': user.email,
                               'priority': validated.get('priority', 'medium'),
                               'exclude_user_ids': exclude_user_ids
                           }, 
                           level="INFO")
            
            result = TaskAssignmentService.create_department_assignments(
                task_id=task_id,
                department_id=department_id,
                start_time=start_time_val,
                end_time=end_time_val,
                assigned_by=user,
                priority=validated.get('priority', 'medium'),
                assignment_date=validated.get('assignment_date'),
                notes=validated.get('notes'),
                exclude_user_ids=exclude_user_ids
            )
            
            # Check if the result indicates no users were found
            if not result.get('success', False):
                error_msg = result.get('message', 'Unknown error')
                
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Assignment failed", 
                               {'message': error_msg, 'result': result}, 
                               level="WARNING")
                
                return Response({
                    'success': False,
                    'message': error_msg,
                    'department': {
                        'id': department.id,
                        'name': department.name
                    },
                    'created_count': result.get('created_count', 0),
                    'skipped_count': result.get('skipped_count', 0),
                    'failed_count': result.get('failed_count', 0)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department assignment completed", 
                           {
                               'created_count': result['created_count'],
                               'skipped_count': result['skipped_count'],
                               'failed_count': result['failed_count'],
                               'total_targeted': result['total_targeted']
                           }, 
                           level="INFO")
            
            # Log skipped assignments if any
            if result['skipped_count'] > 0:
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Skipped assignments", 
                               result['skipped'], 
                               level="WARNING")
            
            # Log failed assignments if any
            if result['failed_count'] > 0:
                _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Failed assignments", 
                               result['failed'], 
                               level="ERROR")
            
        except ValueError as e:
            error_msg = str(e)
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Value error", 
                           {'error': error_msg, 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            
            # Check if this is the "no users" error
            if "No users found" in error_msg:
                return Response({
                    'success': False,
                    'message': f"No active employees available in department '{department.name}'",
                    'department': {
                        'id': department.id,
                        'name': department.name
                    },
                    'created_count': 0,
                    'skipped_count': 0,
                    'failed_count': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Department.DoesNotExist:
            error_msg = "Department not found"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Department not found", 
                           {'department_id': department_id}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            error_msg = f"Service error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Service error", 
                           {'error': error_msg, 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': f'Error creating department assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== RESPONSE SERIALIZATION ==============
        try:
            assignment_serializer = TaskAssignmentSerializer(result['created'], many=True)
            response_data = {
                'success': True,
                'message': f'Successfully assigned task to {result["created_count"]} employees in department',
                'department': {
                    'id': department.id,
                    'name': department.name
                },
                'task': {
                    'id': task.id,
                    'name': task.name
                },
                'created_count': result['created_count'],
                'skipped_count': result['skipped_count'],
                'failed_count': result['failed_count'],
                'total_targeted': result['total_targeted'],
                'created_assignments': assignment_serializer.data,
                'skipped_assignments': result['skipped'],
                'failed_assignments': result['failed']
            }
            
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Response prepared", 
                           {
                               'success': True,
                               'message': response_data['message'],
                               'created_count': response_data['created_count'],
                               'skipped_count': response_data['skipped_count'],
                               'failed_count': response_data['failed_count']
                           }, 
                           level="INFO")
            
        except Exception as e:
            error_msg = f"Response serialization error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Serialization error", 
                           {'error': error_msg, 'traceback': traceback.format_exc()}, 
                           level="ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== LOG ACTIVITY ==============
        try:
            _log_assignment_activity(
                activity_type='task_assignment_bulk_create',
                user=user,
                description=f'Assigned task "{task.name}" to department {department.name} ({result["created_count"]} employees)',
                related_task_id=task.id,
                related_department_id=department.id,
                request=request,
                request_data=_make_json_serializable(request_data),
                response_data=_make_json_serializable(response_data)
            )
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Activity logged", level="INFO")
            
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - Activity logging failed", 
                           {'error': str(e)}, 
                           level="WARNING")
        
        # ============== CALCULATE DURATION AND RETURN ==============
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - COMPLETED SUCCESSFULLY", 
                       {
                           'department_id': department.id,
                           'department_name': department.name,
                           'task_id': task.id,
                           'task_name': task.name,
                           'created': result['created_count'],
                           'duration_ms': f"{duration:.2f}",
                           'response_status': '201 CREATED'
                       }, 
                       level="INFO")
        _log_to_terminal("=" * 100, level="SEPARATOR")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        duration = (timezone.now() - start_time).total_seconds() * 1000
        
        _log_to_terminal("ASSIGN_TASK_TO_DEPARTMENT - UNEXPECTED ERROR", 
                       {
                           'error': str(e),
                           'error_type': type(e).__name__,
                           'traceback': error_trace,
                           'request_data': request_data,
                           'duration_ms': f"{duration:.2f}"
                       }, 
                       level="CRITICAL")
        _log_to_terminal("=" * 100, level="SEPARATOR")
        
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while assigning task to department. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_task_to_users(request):
    """
    Assign a task to a specific list of users
    """
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    
    _log_to_terminal("ASSIGN_TASK_TO_USERS - REQUEST RECEIVED", request_data, level="INFO")
    
    try:
        # ============== PERMISSION CHECK ==============
        user = request.user
        
        if not user or not user.is_authenticated:
            error_msg = "User not authenticated"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (user.is_admin or user.is_manager):
            error_msg = "Only admins and managers can assign tasks to specific users"
            _log_to_terminal("ASSIGN_TASK_TO_USERS - Permission denied", 
                           {'user_id': user.id, 'user_role': getattr(user, 'role', None)}, 
                           level="WARNING")
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ============== SERIALIZER VALIDATION ==============
        serializer = UserListBulkAssignmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            validation_errors = serializer.errors
            _log_to_terminal("ASSIGN_TASK_TO_USERS - Validation failed", 
                           {'errors': validation_errors}, 
                           level="WARNING")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        validated = serializer.validated_data
        
        # ============== USER LIST VALIDATION ==============
        user_ids = validated['user_ids']
        
        if not user_ids or len(user_ids) == 0:
            error_msg = "At least one user must be selected"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify all users exist
        users = CustomUser.objects.filter(id__in=user_ids)
        found_user_ids = set(users.values_list('id', flat=True))
        missing_user_ids = set(user_ids) - found_user_ids
        
        if missing_user_ids:
            error_msg = f"Users not found: {list(missing_user_ids)}"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ============== TASK VALIDATION ==============
        task_id = validated['task_id']
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            error_msg = f"Task with ID {task_id} not found"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ============== DATE/TIME VALIDATION ==============
        start_time_val = validated['start_time']
        end_time_val = validated['end_time']
        
        if start_time_val >= end_time_val:
            error_msg = 'Start time must be before end time'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_time_val < timezone.now():
            error_msg = 'End time cannot be in the past'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== USER LIST ASSIGNMENT EXECUTION ==============
        try:
            result = TaskAssignmentService.create_user_list_assignments(
                task_id=task_id,
                user_ids=user_ids,
                start_time=start_time_val,
                end_time=end_time_val,
                assigned_by=user,
                priority=validated.get('priority', 'medium'),
                assignment_date=validated.get('assignment_date'),
                notes=validated.get('notes')
            )
            
        except ValueError as e:
            error_msg = str(e)
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = f"Service error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_USERS - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error creating user list assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== RESPONSE SERIALIZATION ==============
        try:
            assignment_serializer = TaskAssignmentSerializer(result['created'], many=True)
            response_data = {
                'success': True,
                'message': f'Successfully assigned task to {result["created_count"]} users',
                'task': {
                    'id': task.id,
                    'name': task.name
                },
                'created_count': result['created_count'],
                'skipped_count': result['skipped_count'],
                'failed_count': result['failed_count'],
                'total_targeted': result['total_targeted'],
                'created_assignments': assignment_serializer.data,
                'skipped_assignments': result['skipped'],
                'failed_assignments': result['failed']
            }
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_USERS - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== LOG ACTIVITY ==============
        try:
            _log_assignment_activity(
                activity_type='task_assignment_bulk_create',
                user=user,
                description=f'Assigned task "{task.name}" to {result["created_count"]} specific users',
                related_task_id=task.id,
                request=request,
                request_data=_make_json_serializable(request_data),
                response_data=_make_json_serializable(response_data)
            )
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_USERS - Activity logging failed", 
                           {'error': str(e)}, 
                           level="WARNING")
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"ASSIGN_TASK_TO_USERS - COMPLETED SUCCESSFULLY in {duration:.2f}ms",
            {
                'task_id': task.id,
                'user_count': len(user_ids),
                'created': result['created_count']
            }, 
            level="INFO"
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "ASSIGN_TASK_TO_USERS - UNEXPECTED ERROR",
            {'error': str(e), 'traceback': error_trace},
            level="CRITICAL"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while assigning task to users.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_task_to_role(request):
    """
    Assign a task to all users with a specific role (admin, manager, analyst, employee)
    Only users with departments will get assignments
    """
    start_time = timezone.now()
    request_data = {
        'body': request.data,
        'user_id': request.user.id,
        'user_email': request.user.email,
        'user_role': getattr(request.user, 'role', None)
    }
    
    _log_to_terminal("ASSIGN_TASK_TO_ROLE - REQUEST RECEIVED", request_data, level="INFO")
    
    try:
        # ============== PERMISSION CHECK ==============
        user = request.user
        
        if not user or not user.is_authenticated:
            error_msg = "User not authenticated"
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (user.is_admin or user.is_manager):
            error_msg = "Only admins and managers can assign tasks to roles"
            _log_to_terminal("ASSIGN_TASK_TO_ROLE - Permission denied", 
                           {'user_id': user.id, 'user_role': getattr(user, 'role', None)}, 
                           level="WARNING")
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ============== REQUEST VALIDATION ==============
        # Validate required fields
        required_fields = ['task_id', 'role', 'start_time', 'end_time']
        missing_fields = []
        for field in required_fields:
            if field not in request.data:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== ROLE VALIDATION ==============
        role = request.data.get('role')
        valid_roles = ['admin', 'manager', 'analyst', 'employee']
        
        if role not in valid_roles:
            error_msg = f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== TASK VALIDATION ==============
        task_id = request.data.get('task_id')
        try:
            task_id = int(task_id)
            task = Task.objects.get(id=task_id)
        except ValueError:
            error_msg = 'Invalid task ID format'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            error_msg = f'Task with ID {task_id} not found'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ============== DATE/TIME VALIDATION ==============
        try:
            # Parse start_time - handle ISO format
            start_time_str = request.data['start_time']
            if 'Z' in start_time_str:
                start_time_val = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            else:
                start_time_val = datetime.fromisoformat(start_time_str)
            
            # Parse end_time - handle ISO format
            end_time_str = request.data['end_time']
            if 'Z' in end_time_str:
                end_time_val = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            else:
                end_time_val = datetime.fromisoformat(end_time_str)
            
            # Validate time range
            if start_time_val >= end_time_val:
                error_msg = 'Start time must be before end time'
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if end_time_val < timezone.now():
                error_msg = 'End time cannot be in the past'
                return Response({
                    'success': False,
                    'message': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (ValueError, AttributeError) as e:
            error_msg = 'Invalid date/time format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== ASSIGNMENT DATE ==============
        assignment_date = request.data.get('assignment_date')
        if assignment_date:
            try:
                assignment_date = datetime.strptime(assignment_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': 'Invalid assignment_date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            assignment_date = start_time_val.date()
        
        # ============== PRIORITY VALIDATION ==============
        priority = request.data.get('priority', 'medium')
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if priority not in valid_priorities:
            error_msg = f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== EXCLUDE USER IDS ==============
        exclude_user_ids = request.data.get('exclude_user_ids', [])
        if exclude_user_ids and not isinstance(exclude_user_ids, list):
            return Response({
                'success': False,
                'message': 'exclude_user_ids must be a list'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ============== ROLE-BASED ASSIGNMENT EXECUTION ==============
        try:
            result = TaskAssignmentService.create_role_based_assignments(
                task_id=task_id,
                role=role,
                start_time=start_time_val,
                end_time=end_time_val,
                assigned_by=user,
                priority=priority,
                assignment_date=assignment_date,
                notes=request.data.get('notes'),
                exclude_user_ids=exclude_user_ids
            )
            
            _log_to_terminal("ASSIGN_TASK_TO_ROLE - Role-based assignment completed", 
                           {
                               'role': role,
                               'created_count': result['created_count'],
                               'skipped_count': result['skipped_count'],
                               'failed_count': result['failed_count']
                           }, 
                           level="INFO")
            
        except ValueError as e:
            error_msg = str(e)
            return Response({
                'success': False,
                'message': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_msg = f"Service error: {str(e)}"
            _log_to_terminal("ASSIGN_TASK_TO_ROLE - Service error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': f'Error creating role-based assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== RESPONSE SERIALIZATION ==============
        try:
            assignment_serializer = TaskAssignmentSerializer(result['created'], many=True)
            response_data = {
                'success': True,
                'message': f'Successfully assigned task to {result["created_count"]} users with role "{role}"',
                'task': {
                    'id': task.id,
                    'name': task.name
                },
                'role': role,
                'created_count': result['created_count'],
                'skipped_count': result['skipped_count'],
                'failed_count': result['failed_count'],
                'total_targeted': result['total_targeted'],
                'created_assignments': assignment_serializer.data,
                'skipped_assignments': result['skipped'],
                'failed_assignments': result['failed']
            }
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_ROLE - Serialization error", {'error': str(e)}, "ERROR")
            return Response({
                'success': False,
                'message': 'Error processing response data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ============== LOG ACTIVITY ==============
        try:
            _log_assignment_activity(
                activity_type='task_assignment_bulk_create',
                user=user,
                description=f'Assigned task "{task.name}" to {result["created_count"]} users with role "{role}"',
                related_task_id=task.id,
                request=request,
                request_data=_make_json_serializable(request_data),
                response_data=_make_json_serializable(response_data)
            )
        except Exception as e:
            _log_to_terminal("ASSIGN_TASK_TO_ROLE - Activity logging failed", 
                           {'error': str(e)}, 
                           level="WARNING")
        
        duration = (timezone.now() - start_time).total_seconds() * 1000
        _log_to_terminal(
            f"ASSIGN_TASK_TO_ROLE - COMPLETED SUCCESSFULLY in {duration:.2f}ms",
            {
                'task_id': task.id,
                'role': role,
                'created': result['created_count']
            }, 
            level="INFO"
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "ASSIGN_TASK_TO_ROLE - UNEXPECTED ERROR",
            {'error': str(e), 'traceback': error_trace},
            level="CRITICAL"
        )
        return Response({
            'success': False,
            'message': 'An unexpected error occurred while assigning task to role.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    