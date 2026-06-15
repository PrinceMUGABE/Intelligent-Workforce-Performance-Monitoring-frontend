# userApp/day_off_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
import time
import logging
import traceback

from .models import CustomUser
from .serializers import UserDayOffSerializer, CustomUserSerializer
from activityApp.models import Activity

logger = logging.getLogger(__name__)


def log_user_activity(activity_type, user, request, status_code, description, 
                     related_user_id=None, duration_ms=None, request_data=None, 
                     response_data=None):
    """Helper function to log user-related activities"""
    Activity.log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request,
        related_user_id=related_user_id or (user.id if user else None),
        duration_ms=duration_ms,
        request_data=request_data,
        response_data=response_data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_day_off(request):
    """Get the current user's day off setting"""
    start_time = time.time()
    
    try:
        user = request.user
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_view',
            user=user,
            request=request,
            status_code='200',
            description=f"User {user.email} viewed their day off setting",
            duration_ms=duration_ms,
            response_data={'day_off': user.day_off}
        )
        
        return Response({
            'success': True,
            'day_off': user.day_off,
            'day_off_display': user.get_day_off_display() if user.day_off else None,
            'user_id': user.id,
            'full_name': user.full_name
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing day off: {str(e)}"
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_day_off(request, user_id):
    """Get another user's day off setting (admin/manager only)"""
    start_time = time.time()
    
    try:
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_admin or current_user.is_manager):
            log_user_activity(
                activity_type='dayoff_request_view',
                user=current_user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {current_user.email} attempted to view another user's day off",
                related_user_id=user_id
            )
            return Response({
                'success': False,
                'message': 'You are not authorized to view other users\' day off settings.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the target user
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_view',
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} viewed day off of user {target_user.email}",
            related_user_id=target_user.id,
            duration_ms=duration_ms,
            response_data={'day_off': target_user.day_off}
        )
        
        return Response({
            'success': True,
            'day_off': target_user.day_off,
            'day_off_display': target_user.get_day_off_display() if target_user.day_off else None,
            'user_id': target_user.id,
            'full_name': target_user.full_name,
            'role': target_user.role
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting user day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing user day off: {str(e)}",
            related_user_id=user_id
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_my_day_off(request):
    """Update the current user's day off setting"""
    start_time = time.time()
    
    try:
        user = request.user
        serializer = UserDayOffSerializer(data=request.data)
        
        if not serializer.is_valid():
            log_user_activity(
                activity_type='dayoff_request_update',
                user=user,
                request=request,
                status_code='400',
                description=f"Day off update failed: Invalid data",
                request_data=request.data,
                response_data={'errors': serializer.errors}
            )
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_day_off = user.day_off
        new_day_off = serializer.validated_data['day_off']
        
        # Update the day off
        user.day_off = new_day_off
        user.save()
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_update',
            user=user,
            request=request,
            status_code='200',
            description=f"User {user.email} updated their day off from {old_day_off} to {new_day_off}",
            duration_ms=duration_ms,
            request_data={'old_day_off': old_day_off, 'new_day_off': new_day_off},
            response_data={'day_off': new_day_off}
        )
        
        return Response({
            'success': True,
            'message': 'Day off updated successfully',
            'day_off': new_day_off,
            'day_off_display': user.get_day_off_display(),
            'old_day_off': old_day_off
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_update',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error updating day off: {str(e)}"
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_day_off(request, user_id):
    """Update another user's day off setting (admin/manager only)"""
    start_time = time.time()
    
    try:
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_admin or current_user.is_manager):
            log_user_activity(
                activity_type='dayoff_request_update',
                user=current_user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {current_user.email} attempted to update another user's day off",
                related_user_id=user_id
            )
            return Response({
                'success': False,
                'message': 'You are not authorized to update other users\' day off settings.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the target user
        target_user = get_object_or_404(CustomUser, id=user_id)
        
        serializer = UserDayOffSerializer(data=request.data)
        
        if not serializer.is_valid():
            log_user_activity(
                activity_type='dayoff_request_update',
                user=current_user,
                request=request,
                status_code='400',
                description=f"Day off update failed: Invalid data for user {target_user.email}",
                related_user_id=target_user.id,
                request_data=request.data,
                response_data={'errors': serializer.errors}
            )
            return Response({
                'success': False,
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_day_off = target_user.day_off
        new_day_off = serializer.validated_data['day_off']
        
        # Update the day off
        target_user.day_off = new_day_off
        target_user.save()
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_update',
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} updated day off of user {target_user.email} from {old_day_off} to {new_day_off}",
            related_user_id=target_user.id,
            duration_ms=duration_ms,
            request_data={'old_day_off': old_day_off, 'new_day_off': new_day_off},
            response_data={'day_off': new_day_off}
        )
        
        return Response({
            'success': True,
            'message': f'Day off updated successfully for {target_user.full_name}',
            'user_id': target_user.id,
            'full_name': target_user.full_name,
            'day_off': new_day_off,
            'day_off_display': target_user.get_day_off_display(),
            'old_day_off': old_day_off
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating user day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_update',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error updating user day off: {str(e)}",
            related_user_id=user_id
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_day_offs(request):
    """List all users with their day off settings (admin/manager only)"""
    start_time = time.time()
    
    try:
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_admin or current_user.is_manager):
            log_user_activity(
                activity_type='dayoff_requests_list',
                user=current_user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {current_user.email} attempted to view all day offs"
            )
            return Response({
                'success': False,
                'message': 'You are not authorized to view all day off settings.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Optional filtering by day
        day_filter = request.query_params.get('day', None)
        role_filter = request.query_params.get('role', None)
        
        users = CustomUser.objects.all().select_related('department')
        
        if day_filter and day_filter != 'all':
            if day_filter in ['monday', 'tuesday', 'wednesday', 'thursday', 
                             'friday', 'saturday', 'sunday', 'none']:
                users = users.filter(day_off=day_filter)
            else:
                return Response({
                    'success': False,
                    'message': f'Invalid day filter. Must be one of: monday, tuesday, wednesday, thursday, friday, saturday, sunday, none, all'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if role_filter:
            users = users.filter(role=role_filter)
        
        # Prepare response data
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'work_mail_address': user.work_mail_address,
                'role': user.role,
                'department': user.department.name if user.department else None,
                'day_off': user.day_off,
                'day_off_display': user.get_day_off_display() if user.day_off else None,
                'status': user.status,
                'availability_status': user.availability_status
            })
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_requests_list',
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} viewed all day off settings ({len(users_data)} users)",
            duration_ms=duration_ms,
            request_data=dict(request.query_params)
        )
        
        return Response({
            'success': True,
            'count': len(users_data),
            'users': users_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing day offs: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_requests_list',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error listing day offs: {str(e)}"
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_day_off_statistics(request):
    """Get statistics about day off distribution (admin/manager only)"""
    start_time = time.time()
    
    try:
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_admin or current_user.is_manager):
            log_user_activity(
                activity_type='dayoff_request_stats_view',
                user=current_user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {current_user.email} attempted to view day off statistics"
            )
            return Response({
                'success': False,
                'message': 'You are not authorized to view day off statistics.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all users
        all_users = CustomUser.objects.all()
        total_users = all_users.count()
        
        # Calculate statistics
        day_counts = {}
        for day_choice, day_display in CustomUser.DAY_CHOICES:
            count = all_users.filter(day_off=day_choice).count()
            day_counts[day_choice] = {
                'display': day_display,
                'count': count,
                'percentage': round((count / total_users * 100), 2) if total_users > 0 else 0
            }
        
        # Statistics by role
        role_stats = {}
        for role_choice, role_display in CustomUser.ROLE_CHOICES:
            role_users = all_users.filter(role=role_choice)
            role_count = role_users.count()
            
            if role_count > 0:
                role_day_counts = {}
                for day_choice, _ in CustomUser.DAY_CHOICES:
                    day_count = role_users.filter(day_off=day_choice).count()
                    role_day_counts[day_choice] = {
                        'count': day_count,
                        'percentage': round((day_count / role_count * 100), 2)
                    }
                
                role_stats[role_choice] = {
                    'display': role_display,
                    'total': role_count,
                    'day_distribution': role_day_counts
                }
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_stats_view',
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} viewed day off statistics",
            duration_ms=duration_ms
        )
        
        return Response({
            'success': True,
            'total_users': total_users,
            'day_distribution': day_counts,
            'role_statistics': role_stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting day off statistics: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_stats_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error getting day off statistics: {str(e)}"
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_day_off(request):
    """Clear the current user's day off setting (set to none)"""
    start_time = time.time()
    
    try:
        user = request.user
        old_day_off = user.day_off
        
        if old_day_off == 'none':
            return Response({
                'success': True,
                'message': 'Day off is already set to none',
                'day_off': 'none'
            }, status=status.HTTP_200_OK)
        
        user.day_off = 'none'
        user.save()
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_delete',
            user=user,
            request=request,
            status_code='200',
            description=f"User {user.email} cleared their day off (was: {old_day_off})",
            duration_ms=duration_ms,
            response_data={'old_day_off': old_day_off, 'new_day_off': 'none'}
        )
        
        return Response({
            'success': True,
            'message': 'Day off cleared successfully',
            'day_off': 'none',
            'old_day_off': old_day_off
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error clearing day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_delete',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error clearing day off: {str(e)}"
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_user_day_off(request, user_id):
    """Clear another user's day off setting (admin/manager only)"""
    start_time = time.time()
    
    try:
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_admin or current_user.is_manager):
            log_user_activity(
                activity_type='dayoff_request_delete',
                user=current_user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {current_user.email} attempted to clear another user's day off",
                related_user_id=user_id
            )
            return Response({
                'success': False,
                'message': 'You are not authorized to clear other users\' day off settings.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the target user
        target_user = get_object_or_404(CustomUser, id=user_id)
        old_day_off = target_user.day_off
        
        if old_day_off == 'none':
            return Response({
                'success': True,
                'message': f"{target_user.full_name}'s day off is already set to none",
                'day_off': 'none'
            }, status=status.HTTP_200_OK)
        
        target_user.day_off = 'none'
        target_user.save()
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='dayoff_request_delete',
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} cleared day off of user {target_user.email} (was: {old_day_off})",
            related_user_id=target_user.id,
            duration_ms=duration_ms,
            response_data={'old_day_off': old_day_off, 'new_day_off': 'none'}
        )
        
        return Response({
            'success': True,
            'message': f"Day off cleared successfully for {target_user.full_name}",
            'user_id': target_user.id,
            'full_name': target_user.full_name,
            'day_off': 'none',
            'old_day_off': old_day_off
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error clearing user day off: {str(e)}")
        logger.error(traceback.format_exc())
        
        log_user_activity(
            activity_type='dayoff_request_delete',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error clearing user day off: {str(e)}",
            related_user_id=user_id
        )
        
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)