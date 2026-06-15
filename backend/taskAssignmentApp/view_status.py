# taskAssignmentApp/view_status.py

from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import Serializer, CharField, IntegerField
import traceback
from django.core.exceptions import ValidationError, PermissionDenied

from .models import TaskAssignment
from .serializers import TaskAssignmentSerializer
from .status_service import TaskAssignmentStatusService
from .views import _log_to_terminal, _log_assignment_activity
from .permissions import IsAdminOrManager
from .utils import get_assignment_status_values


class UpdateStatusSerializer(Serializer):
    """Serializer for status update requests"""
    assignment_id = IntegerField(required=True)
    new_status = CharField(required=True)
    reason = CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_new_status(self, value):
        """Validate that the status is valid"""
        try:
            valid_statuses = get_assignment_status_values()
            if value not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            return value
        except Exception as e:
            _log_to_terminal(
                "UPDATE_STATUS_SERIALIZER - Validation error",
                {'error': str(e), 'value': value}
            )
            raise serializers.ValidationError(f"Status validation failed: {str(e)}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_assignment_status(request):
    """
    Update the status of a task assignment with role-based permissions
    
    Allowed transitions:
    - Employee: scheduled -> active, active -> completed
    - Manager/Admin: scheduled -> completed/reassigned/cancelled, 
                     active -> completed/reassigned/cancelled,
                     missed -> reassigned/cancelled
    - Completed/Cancelled assignments cannot be updated
    """
    start_time = timezone.now()
    assignment_id = None
    old_status = None
    
    try:
        _log_to_terminal(
            "UPDATE_ASSIGNMENT_STATUS - Request received",
            {
                'user_id': request.user.id,
                'user_role': request.user.role,
                'data': request.data
            }
        )
        
        user = request.user
        
        # Validate request data
        try:
            serializer = UpdateStatusSerializer(data=request.data)
            if not serializer.is_valid():
                _log_to_terminal(
                    "UPDATE_ASSIGNMENT_STATUS - Validation failed",
                    {'errors': serializer.errors}
                )
                return Response({
                    'success': False,
                    'message': 'Invalid request data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Serializer error",
                {'error': str(e), 'traceback': traceback.format_exc()}
            )
            return Response({
                'success': False,
                'message': f'Failed to validate request data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        try:
            data = serializer.validated_data
            assignment_id = data['assignment_id']
            new_status = data['new_status']
            reason = data.get('reason', '')
            
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Validated data",
                {
                    'assignment_id': assignment_id,
                    'new_status': new_status,
                    'reason': reason
                }
            )
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Data extraction error",
                {'error': str(e), 'traceback': traceback.format_exc()}
            )
            return Response({
                'success': False,
                'message': f'Failed to extract request data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the assignment
        try:
            assignment = TaskAssignment.objects.get(id=assignment_id)
            old_status = assignment.status
            
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Assignment found",
                {
                    'assignment_id': assignment_id,
                    'current_status': old_status,
                    'assigned_to': assignment.user_id,
                    'task_id': assignment.task_id
                }
            )
        except TaskAssignment.DoesNotExist:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Assignment not found",
                {'assignment_id': assignment_id}
            )
            return Response({
                'success': False,
                'message': f'Assignment with ID {assignment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Database query error",
                {'error': str(e), 'traceback': traceback.format_exc()}
            )
            return Response({
                'success': False,
                'message': f'Failed to retrieve assignment: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if assignment is in terminal state
        try:
            if assignment.status in ['completed', 'cancelled'] and new_status != assignment.status:
                _log_to_terminal(
                    "UPDATE_ASSIGNMENT_STATUS - Terminal state violation",
                    {
                        'assignment_id': assignment_id,
                        'current_status': assignment.status,
                        'attempted_status': new_status
                    }
                )
                return Response({
                    'success': False,
                    'message': f'Cannot update {assignment.status} assignments. This assignment is in a final state.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Terminal state check error",
                {'error': str(e), 'traceback': traceback.format_exc()}
            )
            return Response({
                'success': False,
                'message': f'Failed to validate assignment state: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update the status using the service
        try:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Attempting status update",
                {
                    'assignment_id': assignment_id,
                    'from_status': old_status,
                    'to_status': new_status,
                    'user_id': user.id,
                    'user_role': user.role
                }
            )
            
            updated_assignment = TaskAssignmentStatusService.update_status(
                assignment=assignment,
                new_status=new_status,
                user=user,
                reason=reason
            )
            
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Status updated successfully",
                {
                    'assignment_id': assignment_id,
                    'new_status': updated_assignment.status,
                    'updated_at': str(updated_assignment.updated_at)
                }
            )
            
        except PermissionDenied as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Permission denied",
                {
                    'error': str(e),
                    'user_id': user.id,
                    'user_role': user.role,
                    'assignment_id': assignment_id,
                    'current_status': old_status,
                    'attempted_status': new_status
                }
            )
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
            
        except ValidationError as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Validation error",
                {
                    'error': str(e),
                    'assignment_id': assignment_id,
                    'current_status': old_status,
                    'attempted_status': new_status,
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Service error",
                {
                    'error': str(e),
                    'assignment_id': assignment_id,
                    'current_status': old_status,
                    'attempted_status': new_status,
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Failed to update assignment status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Serialize the updated assignment
        try:
            result_serializer = TaskAssignmentSerializer(updated_assignment)
            serialized_data = result_serializer.data
            
            response_data = {
                'success': True,
                'message': f'Assignment status successfully updated from {old_status} to {new_status}',
                'assignment': serialized_data
            }
            
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Serialization successful",
                {'assignment_id': assignment_id}
            )
            
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Serialization error",
                {
                    'error': str(e),
                    'assignment_id': assignment_id,
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Assignment updated but failed to serialize response: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log the activity
        try:
            _log_assignment_activity(
                activity_type='task_assignment_status_update',
                user=user,
                description=f'Updated assignment status from {old_status} to {new_status}',
                related_user_id=assignment.user_id,
                related_task_id=assignment.task_id,
                related_assignment_id=assignment.id,
                related_department_id=assignment.department_id,
                request=request,
                request_data={
                    'assignment_id': assignment_id,
                    'new_status': new_status,
                    'reason': reason
                },
                response_data=response_data
            )
        except Exception as e:
            # Log activity failure but don't fail the request
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Activity logging failed",
                {
                    'error': str(e),
                    'assignment_id': assignment_id,
                    'traceback': traceback.format_exc()
                }
            )
        
        # Calculate and log duration
        try:
            duration = (timezone.now() - start_time).total_seconds() * 1000
            _log_to_terminal(
                f"UPDATE_ASSIGNMENT_STATUS - Completed successfully in {duration:.2f}ms",
                {
                    'assignment_id': assignment_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'duration_ms': duration
                }
            )
        except Exception as e:
            _log_to_terminal(
                "UPDATE_ASSIGNMENT_STATUS - Duration calculation error",
                {'error': str(e)}
            )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        _log_to_terminal(
            "UPDATE_ASSIGNMENT_STATUS - Unexpected critical error",
            {
                'error': str(e),
                'error_type': type(e).__name__,
                'assignment_id': assignment_id,
                'old_status': old_status,
                'user_id': getattr(request.user, 'id', None),
                'traceback': error_trace
            }
        )
        return Response({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}',
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_possible_status_transitions(request, assignment_id):
    """
    Get all possible status transitions for a given assignment based on user role
    """
    try:
        _log_to_terminal(
            "GET_POSSIBLE_TRANSITIONS - Request received",
            {
                'user_id': request.user.id,
                'user_role': request.user.role,
                'assignment_id': assignment_id
            }
        )
        
        user = request.user
        
        # Get the assignment
        try:
            assignment = get_object_or_404(TaskAssignment, id=assignment_id)
            
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Assignment found",
                {
                    'assignment_id': assignment_id,
                    'current_status': assignment.status,
                    'assigned_to': assignment.user_id
                }
            )
        except Exception as e:
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Assignment not found",
                {
                    'error': str(e),
                    'assignment_id': assignment_id,
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Assignment with ID {assignment_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions for employees
        try:
            if user.role == 'employee' and assignment.user_id != user.id:
                _log_to_terminal(
                    "GET_POSSIBLE_TRANSITIONS - Permission denied",
                    {
                        'user_id': user.id,
                        'assignment_user_id': assignment.user_id,
                        'assignment_id': assignment_id
                    }
                )
                return Response({
                    'success': False,
                    'message': 'You can only view status transitions for your own assignments'
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Permission check error",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Failed to verify permissions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get allowed transitions
        try:
            allowed_transitions = TaskAssignmentStatusService.ALLOWED_TRANSITIONS.get(
                user.role, {}
            )
            
            possible_transitions = allowed_transitions.get(assignment.status, [])
            
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Transitions retrieved",
                {
                    'assignment_id': assignment_id,
                    'current_status': assignment.status,
                    'user_role': user.role,
                    'possible_transitions': possible_transitions
                }
            )
        except Exception as e:
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Transitions retrieval error",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Failed to retrieve possible transitions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Build context
        try:
            context = {
                'current_status': assignment.status,
                'is_terminal': assignment.status in TaskAssignmentStatusService.TERMINAL_STATES,
                'can_start': getattr(assignment, 'can_start', False),
                'is_overdue': getattr(assignment, 'is_overdue', False),
                'time_until_start': assignment.time_until_start_minutes,
                'time_until_end': assignment.time_until_end_minutes,
            }
            
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Context built",
                {
                    'assignment_id': assignment_id,
                    'context': context
                }
            )
        except Exception as e:
            _log_to_terminal(
                "GET_POSSIBLE_TRANSITIONS - Context building error",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            # Use minimal context if there's an error
            context = {
                'current_status': assignment.status,
                'error': 'Failed to build complete context'
            }
        
        response_data = {
            'success': True,
            'possible_transitions': possible_transitions,
            'context': context
        }
        
        _log_to_terminal(
            "GET_POSSIBLE_TRANSITIONS - Completed successfully",
            {
                'assignment_id': assignment_id,
                'transitions_count': len(possible_transitions)
            }
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        _log_to_terminal(
            "GET_POSSIBLE_TRANSITIONS - Unexpected critical error",
            {
                'error': str(e),
                'error_type': type(e).__name__,
                'assignment_id': assignment_id,
                'user_id': getattr(request.user, 'id', None),
                'traceback': traceback.format_exc()
            }
        )
        return Response({
            'success': False,
            'message': f'An unexpected error occurred while retrieving transitions: {str(e)}',
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOrManager])
def run_missed_check(request):
    """
    Admin/Manager endpoint to manually trigger missed assignment check
    """
    try:
        _log_to_terminal(
            "RUN_MISSED_CHECK - Request received",
            {
                'user_id': request.user.id,
                'user_role': request.user.role
            }
        )
        
        # Verify user has admin or manager role
        try:
            if request.user.role not in ['admin', 'manager']:
                _log_to_terminal(
                    "RUN_MISSED_CHECK - Permission denied",
                    {
                        'user_id': request.user.id,
                        'user_role': request.user.role
                    }
                )
                return Response({
                    'success': False,
                    'message': 'Only admins and managers can run missed assignment checks'
                }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            _log_to_terminal(
                "RUN_MISSED_CHECK - Permission check error",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Failed to verify permissions: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Run the missed check
        try:
            _log_to_terminal(
                "RUN_MISSED_CHECK - Starting missed assignments check",
                {'timestamp': str(timezone.now())}
            )
            
            count = TaskAssignmentStatusService.check_for_missed_assignments()
            
            _log_to_terminal(
                "RUN_MISSED_CHECK - Check completed",
                {
                    'missed_count': count,
                    'timestamp': str(timezone.now())
                }
            )
            
            return Response({
                'success': True,
                'message': f'Successfully marked {count} overdue assignment(s) as missed',
                'count': count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            _log_to_terminal(
                "RUN_MISSED_CHECK - Service error",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            return Response({
                'success': False,
                'message': f'Failed to check for missed assignments: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        _log_to_terminal(
            "RUN_MISSED_CHECK - Unexpected critical error",
            {
                'error': str(e),
                'error_type': type(e).__name__,
                'user_id': getattr(request.user, 'id', None),
                'traceback': traceback.format_exc()
            }
        )
        return Response({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}',
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)