from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
import traceback
import json

from .models import DayOffChangeRequest
from .serializers import (
    DayOffChangeRequestCreateSerializer,
    DayOffChangeRequestDetailSerializer,
    DayOffChangeRequestListSerializer,
    DayOffChangeRequestUpdateSerializer,
    DayOffChangeRequestActionSerializer
)
from userApp.models import CustomUser
from activityApp.models import Activity


def print_data_to_terminal(data, title="DATA"):
    """Helper function to print data to terminal in a readable format"""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)
    
    # No need to remove profile_picture since it doesn't exist anymore
    print(json.dumps(data, indent=2, default=str) if isinstance(data, (dict, list)) else data)
    
    print("="*80 + "\n")
    

def remove_profile_pictures(data):
    """Recursively remove profile_picture fields from data"""
    if isinstance(data, dict):
        return {
            key: remove_profile_pictures(value) 
            for key, value in data.items() 
            if key != 'profile_picture'
        }
    elif isinstance(data, list):
        return [remove_profile_pictures(item) for item in data]
    else:
        return data


def log_activity(activity_type, user, description, request=None, 
                 related_user_id=None, related_request_id=None, 
                 status_code='200', request_data=None, response_data=None):
    """Helper function to log activities"""
    try:
        # Prepare activity data - use the correct field name from Activity model
        activity_data = {
            'activity_type': activity_type,
            'user': user,
            'status_code': str(status_code),
            'description': description,
            'related_user_id': related_user_id,
            'related_dayoff_request_id': related_request_id,  # This matches your Activity model
            'request_data': request_data,
            'response_data': response_data
        }
        
        if request:
            # Extract request info
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            activity_data['ip_address'] = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
            activity_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            activity_data['request_method'] = request.method
            activity_data['endpoint'] = request.path
        
        Activity.objects.create(**activity_data)
        
    except Exception as e:
        print(f"Failed to log activity: {str(e)}")
        print(traceback.format_exc())
        
        
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_requests(request):
    """
    Get all day-off change requests (with filtering)
    
    Query parameters:
    - status: Filter by status (pending, approved, rejected, cancelled)
    - user_id: Filter by user ID
    """
    try:
        user = request.user
        
        # Base queryset - all users can see all requests (as per requirements)
        queryset = DayOffChangeRequest.objects.all()
        
        # Apply filters
        request_status = request.GET.get('status', None)
        if request_status:
            queryset = queryset.filter(status=request_status)
        
        user_id = request.GET.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Order by created_at descending
        queryset = queryset.order_by('-created_at')
        
        # Serialize
        serializer = DayOffChangeRequestListSerializer(queryset, many=True)
        
        response_data = {
            'count': queryset.count(),
            'requests': serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignments_list',  # Reusing existing activity type
            user=user,
            description=f"Viewed all day-off change requests (filtered by: status={request_status}, user_id={user_id})",
            request=request,
            response_data={'count': queryset.count()}
        )
        
        # Print to terminal
        print_data_to_terminal(
            response_data, 
            f"GET ALL DAY-OFF REQUESTS - User: {user.full_name} ({user.role})"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_all_requests: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while retrieving requests.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_request_by_id(request, request_id):
    """
    Get a specific day-off change request by ID
    """
    try:
        user = request.user
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # All authenticated users can view any request (as per requirements)
        
        # Serialize and return
        serializer = DayOffChangeRequestDetailSerializer(day_off_request)
        
        response_data = {
            'request': serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignment_view',  # Reusing existing activity type
            user=user,
            description=f"Viewed day-off change request #{request_id}",
            request=request,
            related_user_id=day_off_request.user_id,
            related_request_id=request_id
        )
        
        # Print to terminal
        print_data_to_terminal(
            response_data,
            f"GET REQUEST BY ID ({request_id}) - User: {user.full_name} ({user.role})"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_request_by_id: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while retrieving the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_requests(request):
    """
    Get all day-off change requests for the currently logged-in user
    """
    try:
        user = request.user
        
        # Get user's requests
        queryset = DayOffChangeRequest.objects.filter(user=user).order_by('-created_at')
        
        # Apply filters
        request_status = request.GET.get('status', None)
        if request_status:
            queryset = queryset.filter(status=request_status)
        
        serializer = DayOffChangeRequestListSerializer(queryset, many=True)
        
        response_data = {
            'count': queryset.count(),
            'requests': serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignments_list',
            user=user,
            description=f"Viewed own day-off change requests",
            request=request,
            response_data={'count': queryset.count()}
        )
        
        # Print to terminal
        print_data_to_terminal(
            response_data,
            f"GET MY REQUESTS - User: {user.full_name} ({user.role})"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_my_requests: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while retrieving your requests.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_requests_by_user(request, user_id):
    """
    Get all day-off change requests for a specific user
    """
    try:
        current_user = request.user
        
        # Get the target user
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {
                    'error': 'User not found.',
                    'detail': f'No user found with ID {user_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # All authenticated users can view any user's requests (as per requirements)
        
        # Get requests
        queryset = DayOffChangeRequest.objects.filter(user=target_user).order_by('-created_at')
        
        # Apply filters
        request_status = request.GET.get('status', None)
        if request_status:
            queryset = queryset.filter(status=request_status)
        
        serializer = DayOffChangeRequestListSerializer(queryset, many=True)
        
        response_data = {
            'user': {
                'id': target_user.id,
                'full_name': target_user.full_name,
                'email': target_user.email,
                'role': target_user.role
            },
            'count': queryset.count(),
            'requests': serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignments_list',
            user=current_user,
            description=f"Viewed day-off change requests for user {target_user.full_name}",
            request=request,
            related_user_id=target_user.id,
            response_data={'count': queryset.count()}
        )
        
        # Print to terminal
        print_data_to_terminal(
            response_data,
            f"GET REQUESTS FOR USER ({target_user.full_name}) - Requested by: {current_user.full_name}"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_requests_by_user: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while retrieving user requests.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_day_off_request(request):
    """
    Create a new day-off change request
    
    Required fields:
    - reason: Text explaining the reason for change
    - requested_day_off: Requested new day off
    - effective_from: Date when change should take effect
    """
    try:
        user = request.user
        
        # Check if user can make requests (employees only - managers/admins don't need to request)
        if user.role in ['admin', 'manager', 'analyst']:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only employees can create day-off change requests. Managers and admins can directly update their day off.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create serializer with user context
        serializer = DayOffChangeRequestCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Save the request
            day_off_request = serializer.save()
            
            # Return detailed response
            detail_serializer = DayOffChangeRequestDetailSerializer(day_off_request)
            
            response_data = {
                'message': 'Day-off change request created successfully.',
                'request': detail_serializer.data
            }
            
            # Log activity
            log_activity(
                activity_type='task_assignment_create',  # Reusing existing activity type
                user=user,
                description=f"Created day-off change request (current: {day_off_request.current_day_off}, requested: {day_off_request.requested_day_off})",
                request=request,
                related_user_id=user.id,
                related_request_id=day_off_request.id,
                request_data=request.data,
                response_data=response_data,
                status_code='201'
            )
            
            # Print to terminal
            print_data_to_terminal(
                response_data,
                f"CREATE DAY-OFF REQUEST - User: {user.full_name} ({user.role})"
            )
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        print(f"Validation errors: {serializer.errors}")
        return Response(
            {
                'error': 'Invalid request data.',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except ValidationError as ve:
        error_message = str(ve)
        print(f"ValidationError in create_day_off_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'Validation error occurred.',
                'detail': error_message
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in create_day_off_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An unexpected error occurred while creating the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PATCH', 'PUT'])
@permission_classes([IsAuthenticated])
def update_request(request, request_id):
    """
    Update a day-off change request (only pending requests can be updated by the owner)
    
    Request body:
    - reason: Updated reason
    - requested_day_off: Updated requested day off
    - effective_from: Updated effective date
    """
    try:
        user = request.user
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only the request owner can update
        if user != day_off_request.user:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only the request owner can update the request.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can only update pending requests
        if day_off_request.status != 'pending':
            return Response(
                {
                    'error': 'Cannot update request.',
                    'detail': f'Only pending requests can be updated. Current status: {day_off_request.status}.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the request
        serializer = DayOffChangeRequestUpdateSerializer(
            day_off_request,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Return detailed response
            detail_serializer = DayOffChangeRequestDetailSerializer(day_off_request)
            
            response_data = {
                'message': 'Request updated successfully.',
                'request': detail_serializer.data
            }
            
            # Log activity
            log_activity(
                activity_type='task_assignment_update',
                user=user,
                description=f"Updated day-off change request #{request_id}",
                request=request,
                related_user_id=user.id,
                related_request_id=request_id,
                request_data=request.data,
                response_data=response_data
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        print(f"Validation errors: {serializer.errors}")
        return Response(
            {
                'error': 'Invalid request data.',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in update_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while updating the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_request(request, request_id):
    """
    Approve a day-off change request
    
    Only managers and admins can approve requests
    """
    try:
        user = request.user
        
        # Check if user has permission to approve
        if user.role not in ['admin', 'manager']:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only managers and admins can approve requests.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate serializer
        serializer = DayOffChangeRequestActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data.',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = serializer.validated_data.get('notes', '')
        
        # Approve the request
        try:
            day_off_request.approve(user, notes)
        except ValidationError as ve:
            print(f"ValidationError in approve_request: {str(ve)}")
            return Response(
                {
                    'error': 'Approval failed.',
                    'detail': str(ve)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return updated request
        detail_serializer = DayOffChangeRequestDetailSerializer(day_off_request)
        
        response_data = {
            'message': 'Request approved successfully. Employee day off has been updated.',
            'request': detail_serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignment_complete',  # Reusing existing activity type
            user=user,
            description=f"Approved day-off change request #{request_id} for {day_off_request.user.full_name} (to {day_off_request.requested_day_off})",
            request=request,
            related_user_id=day_off_request.user_id,
            related_request_id=request_id,
            request_data=request.data,
            response_data=response_data
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in approve_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while approving the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_request(request, request_id):
    """
    Reject a day-off change request
    
    Only managers and admins can reject requests
    """
    try:
        user = request.user
        
        # Check if user has permission to reject
        if user.role not in ['admin', 'manager']:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only managers and admins can reject requests.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate serializer
        serializer = DayOffChangeRequestActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data.',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = serializer.validated_data.get('notes', 'Rejected by manager/admin')
        
        # Reject the request
        try:
            day_off_request.reject(user, notes)
        except ValidationError as ve:
            print(f"ValidationError in reject_request: {str(ve)}")
            return Response(
                {
                    'error': 'Rejection failed.',
                    'detail': str(ve)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return updated request
        detail_serializer = DayOffChangeRequestDetailSerializer(day_off_request)
        
        response_data = {
            'message': 'Request rejected successfully.',
            'request': detail_serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignment_cancelled',  # Reusing existing activity type
            user=user,
            description=f"Rejected day-off change request #{request_id} for {day_off_request.user.full_name}",
            request=request,
            related_user_id=day_off_request.user_id,
            related_request_id=request_id,
            request_data=request.data,
            response_data=response_data
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in reject_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while rejecting the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_request(request, request_id):
    """
    Cancel a day-off change request
    
    Only the request owner can cancel their own pending requests
    """
    try:
        user = request.user
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only the request owner can cancel
        if user != day_off_request.user:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only the request owner can cancel this request.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate serializer
        serializer = DayOffChangeRequestActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data.',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = serializer.validated_data.get('reason', 'Cancelled by employee')
        
        # Cancel the request
        try:
            day_off_request.cancel(user, reason)
        except ValidationError as ve:
            print(f"ValidationError in cancel_request: {str(ve)}")
            return Response(
                {
                    'error': 'Cancellation failed.',
                    'detail': str(ve)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return updated request
        detail_serializer = DayOffChangeRequestDetailSerializer(day_off_request)
        
        response_data = {
            'message': 'Request cancelled successfully.',
            'request': detail_serializer.data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignment_cancelled',
            user=user,
            description=f"Cancelled own day-off change request #{request_id}",
            request=request,
            related_user_id=user.id,
            related_request_id=request_id,
            request_data=request.data,
            response_data=response_data
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in cancel_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while cancelling the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_request(request, request_id):
    """
    Delete a day-off change request
    
    - Employees can delete their own pending or cancelled requests
    - Managers and admins can delete any pending or cancelled requests
    """
    try:
        user = request.user
        
        # Get the request
        try:
            day_off_request = DayOffChangeRequest.objects.get(id=request_id)
        except DayOffChangeRequest.DoesNotExist:
            return Response(
                {
                    'error': 'Request not found.',
                    'detail': f'No day-off change request found with ID {request_id}.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        can_delete = (
            user.role in ['admin', 'manager'] or  # Admin/manager can delete any
            user == day_off_request.user  # Owner can delete their own
        )
        
        if not can_delete:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'You do not have permission to delete this request.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot delete approved/rejected requests
        if day_off_request.status not in ['pending', 'cancelled']:
            return Response(
                {
                    'error': 'Cannot delete request.',
                    'detail': f'Only pending or cancelled requests can be deleted. Current status: {day_off_request.status}.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store request data before deletion for logging
        request_data = {
            'id': day_off_request.id,
            'user': day_off_request.user.full_name,
            'current_day_off': day_off_request.current_day_off,
            'requested_day_off': day_off_request.requested_day_off,
            'status': day_off_request.status,
            'reason': day_off_request.reason
        }
        
        # Delete the request
        day_off_request.delete()
        
        response_data = {
            'message': 'Request deleted successfully.',
            'deleted_request': request_data
        }
        
        # Log activity
        log_activity(
            activity_type='task_assignment_delete',
            user=user,
            description=f"Deleted day-off change request #{request_id} (status: {request_data['status']})",
            request=request,
            related_user_id=request_data['user'] if isinstance(request_data['user'], int) else None,
            related_request_id=request_id,
            response_data=response_data
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in delete_request: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while deleting the request.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_requests_stats(request):
    """
    Get statistics about day-off change requests
    
    Only managers and admins can access stats
    """
    try:
        user = request.user
        
        # Check if user has permission
        if user.role not in ['admin', 'manager', 'analyst']:
            return Response(
                {
                    'error': 'Permission denied.',
                    'detail': 'Only admins, managers, and analysts can view request statistics.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate statistics
        total_requests = DayOffChangeRequest.objects.count()
        pending_requests = DayOffChangeRequest.objects.filter(status='pending').count()
        approved_requests = DayOffChangeRequest.objects.filter(status='approved').count()
        rejected_requests = DayOffChangeRequest.objects.filter(status='rejected').count()
        cancelled_requests = DayOffChangeRequest.objects.filter(status='cancelled').count()
        
        # Requests by day off type
        requests_by_day_off = {}
        for day_off, _ in DayOffChangeRequest.DAY_CHOICES:
            count = DayOffChangeRequest.objects.filter(requested_day_off=day_off).count()
            if count > 0:
                requests_by_day_off[day_off] = count
        
        response_data = {
            'total': total_requests,
            'pending': pending_requests,
            'approved': approved_requests,
            'rejected': rejected_requests,
            'cancelled': cancelled_requests,
            'by_day_off': requests_by_day_off
        }
        
        # Log activity
        log_activity(
            activity_type='performance_view_all',
            user=user,
            description=f"Viewed day-off request statistics",
            request=request,
            response_data=response_data
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error in get_requests_stats: {error_message}")
        print(traceback.format_exc())
        return Response(
            {
                'error': 'An error occurred while retrieving statistics.',
                'detail': error_message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )