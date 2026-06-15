from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import traceback

from sympy import Q

from userApp.models import CustomUser
from departmentApp.models import Department
from .services import PerformanceCalculator
from .serializers import (
    UserPerformanceSerializer, 
    DepartmentPerformanceSerializer,
    OrganizationPerformanceSerializer,
    PerformanceTrendSerializer
)
from activityApp.models import Activity


# ==================== HELPER FUNCTIONS ====================
def _log_performance_activity(activity_type, user, description, related_user_id=None,
                             related_department_id=None, status_code='200', 
                             request=None, request_data=None, response_data=None):
    """Log performance-related activities"""
    try:
        Activity.log_activity(
            activity_type=activity_type,
            user=user,
            description=description,
            related_user_id=related_user_id,
            related_department_id=related_department_id,
            status_code=status_code,
            request=request,
            request_data=request_data,
            response_data=response_data
        )
    except Exception as e:
        print(f"Failed to log performance activity: {str(e)}")


def _check_permission(user, required_roles):
    """Check if user has required role"""
    return user.role in required_roles


# ==================== PERFORMANCE VIEWS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_performance(request):
    """
    Get performance metrics for the authenticated user
    Accessible by: All authenticated users (employees see their own)
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Get date range from query params
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            if days < 1:
                days = 30
            if days > 365:
                days = 365
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate performance
        performance_data = PerformanceCalculator.calculate_user_performance(
            user, 
            start_date=start_date,
            end_date=end_date
        )
        
        # Get trends
        trends = PerformanceCalculator.get_performance_trends(user, days=days)
        trend_serializer = PerformanceTrendSerializer(trends, many=True)
        
        # Serialize response
        serializer = UserPerformanceSerializer(performance_data)
        print(f" Retrieved performance data: {serializer.data}\n")
        response_data = {
            'success': True,
            'message': 'Performance data retrieved successfully',
            'data': serializer.data,
            'trends': trend_serializer.data,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_own',
            user=user,
            description=f'User {user.full_name} viewed their own performance metrics',
            related_user_id=user.id,
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_my_performance: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving your performance data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_performance(request, user_id):
    """
    Get performance metrics for a specific user
    Accessible by: Admin, Manager, Analyst
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Check permissions
        if not _check_permission(user, ['admin', 'manager', 'analyst']):
            return Response({
                'success': False,
                'message': 'You do not have permission to view other users\' performance'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get target user
        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': f'User with ID {user_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Managers can only view users in their department
        if user.role == 'manager' and not user.is_admin:
            if not target_user.department or target_user.department != user.department:
                return Response({
                    'success': False,
                    'message': 'You can only view performance of users in your department'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate performance
        performance_data = PerformanceCalculator.calculate_user_performance(
            target_user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get trends
        trends = PerformanceCalculator.get_performance_trends(target_user, days=days)
        trend_serializer = PerformanceTrendSerializer(trends, many=True)
        
        # Serialize response
        serializer = UserPerformanceSerializer(performance_data)
        response_data = {
            'success': True,
            'message': f'Performance data for {target_user.full_name} retrieved successfully',
            'data': serializer.data,
            'trends': trend_serializer.data,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_user',
            user=user,
            description=f'User {user.full_name} viewed performance of {target_user.full_name}',
            related_user_id=target_user.id,
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_user_performance: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving user performance data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_performance(request, department_id):
    """
    Get performance metrics for a department
    Accessible by: Admin, Manager, Analyst
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Check permissions
        if not _check_permission(user, ['admin', 'manager', 'analyst']):
            return Response({
                'success': False,
                'message': 'You do not have permission to view department performance'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get department
        try:
            from departmentApp.models import Department
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return Response({
                'success': False,
                'message': f'Department with ID {department_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Managers can only view their own department
        if user.role == 'manager' and not user.is_admin:
            if user.department != department:
                return Response({
                    'success': False,
                    'message': 'You can only view performance of your own department'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate department performance
        performance_data = PerformanceCalculator.get_department_performance(
            department,
            start_date=start_date,
            end_date=end_date
        )
        
        # Serialize response
        serializer = DepartmentPerformanceSerializer(performance_data)
        response_data = {
            'success': True,
            'message': f'Performance data for {department.name} retrieved successfully',
            'data': serializer.data,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_department',
            user=user,
            description=f'User {user.full_name} viewed performance of department {department.name}',
            related_department_id=department.id,
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_department_performance: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving department performance data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_performances(request):
    """
    Get performance metrics for all users (paginated)
    Accessible by: Admin, Manager, Analyst
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Check permissions
        if not _check_permission(user, ['admin', 'manager', 'analyst']):
            return Response({
                'success': False,
                'message': 'You do not have permission to view all performances'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get query parameters
        days = request.query_params.get('days', 30)
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 10))
        department_id = request.query_params.get('department_id')
        search = request.query_params.get('search', '')
        
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset - only employees
        users = CustomUser.objects.filter(
            role='employee',
            is_active=True,
            status='approved'
        )
        
        # Managers can only see their department
        if user.role == 'manager' and not user.is_admin:
            if user.department:
                users = users.filter(department=user.department)
            else:
                users = users.none()
        
        # Apply filters
        if department_id and department_id != 'all':
            try:
                users = users.filter(department_id=int(department_id))
            except ValueError:
                pass
        
        if search:
            users = users.filter(
                Q(full_name__icontains=search) |
                Q(work_mail_address__icontains=search) |
                Q(email__icontains=search)
            )
        
        # Pagination
        total_count = users.count()
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_users = users[start_idx:end_idx]
        
        # Calculate performance for each user
        performances = []
        for target_user in paginated_users:
            perf_data = PerformanceCalculator.calculate_user_performance(
                target_user,
                start_date=start_date,
                end_date=end_date
            )
            performances.append(perf_data)
        
        # Sort by completion rate (highest first)
        performances = sorted(performances, key=lambda x: x['task_completion_rate'], reverse=True)
        
        # Serialize
        serializer = UserPerformanceSerializer(performances, many=True)
        print(f"\n Retrieved users performances {serializer.data}\n")
        
        response_data = {
            'success': True,
            'message': 'Performance data retrieved successfully',
            'data': serializer.data,
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if limit > 0 else 0,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_all',
            user=user,
            description=f'User {user.full_name} viewed all employee performances',
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_all_performances: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving performance data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_performance(request):
    """
    Get organization-wide performance summary
    Accessible by: Admin, Analyst
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Check permissions
        if not _check_permission(user, ['admin', 'analyst']):
            return Response({
                'success': False,
                'message': 'You do not have permission to view organization performance'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate organization performance
        org_performance = PerformanceCalculator.get_organization_performance(
            start_date=start_date,
            end_date=end_date
        )
        
        # Serialize
        serializer = OrganizationPerformanceSerializer(org_performance)
        
        response_data = {
            'success': True,
            'message': 'Organization performance data retrieved successfully',
            'data': serializer.data,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_organization',
            user=user,
            description=f'User {user.full_name} viewed organization performance',
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_organization_performance: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving organization performance data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_department_summaries(request):
    """
    Get performance summaries for all departments
    Accessible by: Admin, Analyst
    """
    start_time = timezone.now()
    
    try:
        user = request.user
        
        # Check permissions
        if not _check_permission(user, ['admin', 'analyst']):
            return Response({
                'success': False,
                'message': 'You do not have permission to view department summaries'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get all active departments
        departments = Department.objects.filter(status='active')
        
        # Calculate performance for each department
        dept_performances = []
        for dept in departments:
            perf = PerformanceCalculator.get_department_performance(
                dept,
                start_date=start_date,
                end_date=end_date
            )
            dept_performances.append(perf)
        
        # Sort by completion rate
        dept_performances = sorted(
            dept_performances, 
            key=lambda x: x['avg_task_completion_rate'], 
            reverse=True
        )
        
        # Serialize
        serializer = DepartmentPerformanceSerializer(dept_performances, many=True)
        
        response_data = {
            'success': True,
            'message': 'Department performance summaries retrieved successfully',
            'data': serializer.data,
            'period': {
                'start': start_date,
                'end': end_date,
                'days': days
            }
        }
        
        # Log activity
        _log_performance_activity(
            activity_type='performance_view_departments',
            user=user,
            description=f'User {user.full_name} viewed all department performance summaries',
            status_code='200',
            request=request
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in get_department_summaries: {str(e)}\n{error_trace}")
        
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving department summaries'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)