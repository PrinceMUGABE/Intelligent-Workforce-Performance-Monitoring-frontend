# activityApp/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Activity, ActivitySummary
from .serializers import (
    ActivitySerializer,
    ActivityDetailSerializer,
    ActivityStatsSerializer,
    ActivityFilterSerializer
)
import traceback


def is_admin_or_manager(user):
    """Helper function to check if user is admin or manager"""
    return user.is_authenticated and hasattr(user, 'role') and user.role in ['admin', 'manager']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_activities(request):
    """
    Get all activities with filtering and pagination
    Admin/Manager: Can view all activities
    Other users: Can only view their own activities
    """
    try:
        user = request.user
        
        # Base queryset
        if is_admin_or_manager(user):
            activities = Activity.objects.all()
        else:
            # Regular users can only see their own activities
            activities = Activity.objects.filter(user=user)
        
        # Apply filters
        activity_type = request.query_params.get('activity_type')
        if activity_type:
            activities = activities.filter(activity_type=activity_type)
        
        user_id = request.query_params.get('user_id')
        if user_id and is_admin_or_manager(user):
            activities = activities.filter(user_id=user_id)
        
        status_code = request.query_params.get('status_code')
        if status_code:
            activities = activities.filter(status_code=status_code)
        
        device_type = request.query_params.get('device_type')
        if device_type:
            activities = activities.filter(device_type__icontains=device_type)
        
        # Date range filters
        date_from = request.query_params.get('date_from')
        if date_from:
            activities = activities.filter(created_at__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            activities = activities.filter(created_at__lte=date_to)
        
        # Search across description and endpoint
        search = request.query_params.get('search')
        if search:
            activities = activities.filter(
                Q(description__icontains=search) |
                Q(endpoint__icontains=search) |
                Q(user__full_name__icontains=search)
            )
        
        # Ordering
        order_by = request.query_params.get('order_by', '-created_at')
        activities = activities.order_by(order_by)
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = activities.count()
        activities_page = activities[start:end]
        
        serializer = ActivitySerializer(activities_page, many=True)
        
        return Response({
            'success': True,
            'message': 'Activities retrieved successfully.',
            'data': serializer.data,
            'pagination': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error retrieving activities: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'An error occurred while retrieving activities: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_by_id(request, activity_id):
    """Get a single activity by ID"""
    try:
        user = request.user
        
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Activity with ID {activity_id} does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if not is_admin_or_manager(user) and activity.user != user:
            return Response({
                'success': False,
                'message': 'You do not have permission to view this activity.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ActivityDetailSerializer(activity)
        
        return Response({
            'success': True,
            'message': 'Activity retrieved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error retrieving activity: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'An error occurred while retrieving the activity: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_activities(request):
    """Get activities for the logged-in user"""
    try:
        user = request.user
        
        activities = Activity.objects.filter(user=user)
        
        # Apply filters (same as get_all_activities but without user_id filter)
        activity_type = request.query_params.get('activity_type')
        if activity_type:
            activities = activities.filter(activity_type=activity_type)
        
        status_code = request.query_params.get('status_code')
        if status_code:
            activities = activities.filter(status_code=status_code)
        
        # Date range
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            date_from = timezone.now() - timedelta(days=days)
            activities = activities.filter(created_at__gte=date_from)
        except ValueError:
            pass
        
        # Ordering
        activities = activities.order_by('-created_at')
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = activities.count()
        activities_page = activities[start:end]
        
        serializer = ActivitySerializer(activities_page, many=True)
        
        return Response({
            'success': True,
            'message': 'Your activities retrieved successfully.',
            'data': serializer.data,
            'pagination': {
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error retrieving user activities: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'An error occurred while retrieving your activities: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_stats(request):
    """
    Get activity statistics
    Admin/Manager: System-wide stats
    Other users: Personal stats
    """
    try:
        user = request.user
        
        # Base queryset
        if is_admin_or_manager(user):
            activities = Activity.objects.all()
        else:
            activities = Activity.objects.filter(user=user)
        
        # Apply date range filter
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        activities = activities.filter(created_at__gte=date_from)
        
        # Calculate statistics
        total_activities = activities.count()
        successful_activities = activities.filter(status_code__startswith='2').count()
        failed_activities = total_activities - successful_activities
        success_rate = (successful_activities / total_activities * 100) if total_activities > 0 else 0
        
        # Activities by type
        activities_by_type = dict(
            activities.values('activity_type')
            .annotate(count=Count('id'))
            .values_list('activity_type', 'count')
        )
        
        # Activities by status code
        activities_by_status = dict(
            activities.values('status_code')
            .annotate(count=Count('id'))
            .values_list('status_code', 'count')
        )
        
        # Activities by device type
        activities_by_device = dict(
            activities.exclude(device_type__isnull=True)
            .values('device_type')
            .annotate(count=Count('id'))
            .values_list('device_type', 'count')
        )
        
        # Activities by date (last 7 days)
        from django.db.models.functions import TruncDate
        activities_by_date = list(
            activities.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
            .values('date', 'count')
        )
        
        # Top users (admin/manager only)
        top_users = []
        if is_admin_or_manager(user):
            top_users_data = (
                activities.exclude(user__isnull=True)
                .values('user__id', 'user__full_name', 'user__work_mail_address')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            
            top_users = [
                {
                    'user_id': item['user__id'],
                    'full_name': item['user__full_name'],
                    'work_mail': item['user__work_mail_address'],
                    'activity_count': item['count']
                }
                for item in top_users_data
            ]
        
        stats_data = {
            'total_activities': total_activities,
            'successful_activities': successful_activities,
            'failed_activities': failed_activities,
            'success_rate': round(success_rate, 2),
            'activities_by_type': activities_by_type,
            'activities_by_status': activities_by_status,
            'activities_by_device': activities_by_device,
            'activities_by_date': activities_by_date,
            'top_users': top_users,
        }
        
        serializer = ActivityStatsSerializer(data=stats_data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'success': True,
            'message': 'Activity statistics retrieved successfully.',
            'data': serializer.validated_data,
            'period': f'Last {days} days'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error retrieving activity stats: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'An error occurred while retrieving activity statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity_summary(request, user_id):
    """Get activity summary for a specific user (Admin/Manager only)"""
    try:
        user = request.user
        
        if not is_admin_or_manager(user):
            return Response({
                'success': False,
                'message': 'You do not have permission to view other users\' activities.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if target user exists
        from userApp.models import CustomUser
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': f'User with ID {user_id} does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get activities for the user
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        activities = Activity.objects.filter(
            user=target_user,
            created_at__gte=date_from
        )
        
        total = activities.count()
        successful = activities.filter(status_code__startswith='2').count()
        failed = total - successful
        
        # Recent activities
        recent_activities = activities.order_by('-created_at')[:10]
        activities_serializer = ActivitySerializer(recent_activities, many=True)
        
        # Activity breakdown by type
        by_type = dict(
            activities.values('activity_type')
            .annotate(count=Count('id'))
            .values_list('activity_type', 'count')
        )
        
        return Response({
            'success': True,
            'message': 'User activity summary retrieved successfully.',
            'data': {
                'user': {
                    'id': target_user.id,
                    'full_name': target_user.full_name,
                    'work_mail_address': target_user.work_mail_address,
                    'role': target_user.role
                },
                'summary': {
                    'total_activities': total,
                    'successful_activities': successful,
                    'failed_activities': failed,
                    'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
                    'activities_by_type': by_type
                },
                'recent_activities': activities_serializer.data,
                'period': f'Last {days} days'
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error retrieving user activity summary: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'An error occurred while retrieving user activity summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_old_activities(request):
    """
    Delete all existing activities permanently (Admin only)
    This will delete ALL activities in the database.
    New activities created after this deletion will be kept.
    
    Note: Confirmation is handled on the frontend side.
    """
    try:
        user = request.user
        
        # Check if user is admin
        if not hasattr(user, 'is_admin') or not user.is_admin:
            # Alternative check for role-based admin
            if not hasattr(user, 'role') or user.role != 'admin':
                return Response({
                    'success': False,
                    'message': 'Only administrators can delete activity logs.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get count before deletion
        count_before = Activity.objects.count()
        
        print("\n" + "=" * 80)
        print(f"🗑️  ACTIVITY DELETION IN PROGRESS")
        print("=" * 80)
        print(f"Total activities BEFORE deletion: {count_before}")
        print(f"User performing deletion: {user.work_mail_address if hasattr(user, 'work_mail_address') else user.email if hasattr(user, 'email') else 'Unknown'}")
        print(f"User role: {user.role if hasattr(user, 'role') else 'N/A'}")
        print(f"Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        if count_before == 0:
            print("ℹ️  No activities to delete. Database is already clean.")
            print("=" * 80 + "\n")
            return Response({
                'success': True,
                'message': 'No activities to delete. Database is already clean.',
                'deleted_count': 0
            }, status=status.HTTP_200_OK)
        
        # Delete ALL activities
        print(f"Deleting {count_before} activities...")
        Activity.objects.all().delete()
        
        # Check count after deletion (should be 0)
        count_after_deletion = Activity.objects.count()
        print(f"✓ Deletion complete!")
        print(f"Total activities AFTER deletion: {count_after_deletion}")
        print("-" * 80)
        
        # Log this deletion activity (creates a new record)
        print("Creating deletion log entry...")
        Activity.log_activity(
            activity_type='api_request',
            user=user,
            status_code='200',
            description=f'Permanently deleted all {count_before} existing activities from the database',
            request=request
        )
        
        # Final count (should be 1 - the log entry)
        final_count = Activity.objects.count()
        print(f"✓ Deletion log entry created!")
        print(f"Final activity count: {final_count} (the deletion log entry)")
        print("=" * 80)
        print(f"✅ DELETION SUMMARY:")
        print(f"   • Activities before deletion: {count_before}")
        print(f"   • Activities deleted: {count_before}")
        print(f"   • Activities after deletion: {count_after_deletion}")
        print(f"   • Current total (including log): {final_count}")
        print("=" * 80 + "\n")
        
        return Response({
            'success': True,
            'message': f'Successfully deleted all {count_before} activities. New activities will be tracked going forward.',
            'deleted_count': count_before,
            'activities_before_deletion': count_before,
            'activities_after_deletion': count_after_deletion,
            'current_total': final_count,
            'note': f'{final_count} activity remaining (the deletion log entry)'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR DURING ACTIVITY DELETION")
        print("=" * 80)
        print(f"Error message: {str(e)}")
        print("-" * 80)
        print("Stack trace:")
        print(traceback.format_exc())
        print("=" * 80 + "\n")
        
        return Response({
            'success': False,
            'message': f'An error occurred while deleting activities: {str(e)}',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)