# reportApp/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .permissions import (
    CanGenerateUserReports,
    CanGenerateDepartmentReports,
    CanGenerateTaskReports,
    CanGenerateTaskAssignmentReports,
    CanGenerateDayOffReports,
    CanGenerateActivityReports,
    CanGeneratePerformanceReports,
    CanGenerateOrganizationReports,
)
from .serializers import (
    ReportFilterSerializer,
    UserReportResponseSerializer,
    DepartmentReportResponseSerializer,
    TaskReportResponseSerializer,
    TaskAssignmentReportResponseSerializer,
    DayOffReportResponseSerializer,
    ActivityReportResponseSerializer,
    PerformanceReportResponseSerializer,
    OrganizationReportResponseSerializer,
)
from .utils import (
    UserReportGenerator,
    DepartmentReportGenerator,
    TaskReportGenerator,
    TaskAssignmentReportGenerator,
    DayOffReportGenerator,
    ActivityReportGenerator,
    PerformanceReportGenerator,
    OrganizationReportGenerator,
)

from userApp.models import CustomUser
from departmentApp.models import Department
from taskApp.models import Task
from taskAssignmentApp.models import TaskAssignment
from requestApp.models import DayOffChangeRequest
from activityApp.models import Activity

logger = logging.getLogger(__name__)


def generate_organization_performance_report(request, filters):
    """
    Generate organization-wide performance report showing all users' performance
    Only accessible by admin, manager, and analyst roles
    """
    try:
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build user queryset based on role
        if request.user.role == 'admin' or request.user.role == 'analyst':
            users_queryset = CustomUser.objects.filter(status='approved')
        elif request.user.role == 'manager':
            # Manager sees only their department
            if request.user.department:
                users_queryset = CustomUser.objects.filter(
                    department=request.user.department,
                    status='approved'
                )
            else:
                users_queryset = CustomUser.objects.filter(status='approved')
        else:
            return Response({
                'error': 'Permission denied',
                'message': 'You do not have permission to view organization performance'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate performance data for all users
        all_users_performance = []
        
        for user in users_queryset:
            user_perf_data = PerformanceReportGenerator.generate_performance_report(
                user.id, validated_filters, request.user
            )
            
            if user_perf_data and user_perf_data.get('performance_data'):
                perf = user_perf_data['performance_data']
                all_users_performance.append({
                    'user_id': user.id,
                    'user_name': user.full_name,
                    'department': user.department.name if user.department else 'N/A',
                    'role': user.role,
                    'total_assignments': perf['assignment_metrics']['total_assignments'],
                    'completed': perf['assignment_metrics']['completed'],
                    'missed': perf['assignment_metrics']['missed'],
                    'active': perf['assignment_metrics']['active'],
                    'completion_rate': perf['performance_rates']['completion_rate'],
                    'miss_rate': perf['performance_rates']['miss_rate'],
                    'average_completion_time': perf.get('average_completion_time_minutes', 0),
                })
        
        # Calculate aggregate statistics
        total_assignments = sum(u['total_assignments'] for u in all_users_performance)
        total_completed = sum(u['completed'] for u in all_users_performance)
        total_missed = sum(u['missed'] for u in all_users_performance)
        
        # Prepare summary
        summary = {
            'total_count': len(all_users_performance),
            'filters_applied': {
                'start_date': validated_filters.get('start_date').isoformat() if validated_filters.get('start_date') else None,
                'end_date': validated_filters.get('end_date').isoformat() if validated_filters.get('end_date') else None,
            },
            'date_range': {
                'start_date': validated_filters.get('start_date').isoformat() if validated_filters.get('start_date') else None,
                'end_date': validated_filters.get('end_date').isoformat() if validated_filters.get('end_date') else None,
            },
            'generated_at': timezone.now().isoformat(),
            'generated_by': request.user.full_name if request.user else 'System',
            'report_type': 'Organization Performance Report',
        }
        
        statistics = {
            'total_users': len(all_users_performance),
            'total_assignments': total_assignments,
            'total_completed': total_completed,
            'total_missed': total_missed,
            'overall_completion_rate': round((total_completed / total_assignments * 100), 2) if total_assignments > 0 else 0,
            'overall_miss_rate': round((total_missed / total_assignments * 100), 2) if total_assignments > 0 else 0,
            'average_assignments_per_user': round(total_assignments / len(all_users_performance), 2) if len(all_users_performance) > 0 else 0,
        }
        
        # Sort by completion rate
        all_users_performance.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_organization',
            user=request.user,
            status_code='200',
            description=f'Generated organization performance report for {len(all_users_performance)} users',
            request=request,
            response_data={'user_count': len(all_users_performance)}
        )
        
        return Response({
            'summary': summary,
            'performance_data': all_users_performance,
            'statistics': statistics,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating organization performance report: {str(e)}")
        
        Activity.log_activity(
            activity_type='performance_view_organization',
            user=request.user,
            status_code='500',
            description=f'Failed to generate organization performance report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate organization performance report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateUserReports])
def generate_user_report(request):
    """
    Generate user report
    
    GET parameters / POST body:
    - start_date (optional): Filter users created from this date
    - end_date (optional): Filter users created until this date
    - department_id (optional): Filter by department
    - status (optional): Filter by user status
    - role (optional): Filter by user role
    - availability_status (optional): Filter by availability status
    
    Returns:
    - summary: Report metadata and summary
    - users: List of user data
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset based on user role
        if request.user.role == 'admin':
            # Admin can see all users
            queryset = CustomUser.objects.all()
        elif request.user.role == 'manager':
            # Manager can see users in their department(s)
            if request.user.department:
                queryset = CustomUser.objects.filter(department=request.user.department)
            else:
                queryset = CustomUser.objects.all()
        elif request.user.role == 'analyst':
            # Analyst can see all users
            queryset = CustomUser.objects.all()
        else:
            return Response({
                'error': 'Permission denied',
                'message': 'You do not have permission to generate user reports'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Apply filters
        if validated_filters.get('start_date'):
            start_datetime = timezone.make_aware(
                datetime.combine(validated_filters['start_date'], datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        
        if validated_filters.get('end_date'):
            end_datetime = timezone.make_aware(
                datetime.combine(validated_filters['end_date'], datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        if validated_filters.get('department_id'):
            queryset = queryset.filter(department_id=validated_filters['department_id'])
        
        if validated_filters.get('status'):
            queryset = queryset.filter(status=validated_filters['status'])
        
        if filters.get('role'):
            queryset = queryset.filter(role=filters['role'])
        
        if filters.get('availability_status'):
            queryset = queryset.filter(availability_status=filters['availability_status'])
        
        # Select related for optimization
        queryset = queryset.select_related('department', 'created_by')
        
        # Generate report
        report_data = UserReportGenerator.generate_user_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='users_list',
            user=request.user,
            status_code='200',
            description=f'Generated user report with {len(report_data["users"])} users',
            request=request,
            response_data={'count': len(report_data['users'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating user report: {str(e)}")
        
        Activity.log_activity(
            activity_type='users_list',
            user=request.user,
            status_code='500',
            description=f'Failed to generate user report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate user report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateDepartmentReports])
def generate_department_report(request):
    """
    Generate department report
    
    GET parameters / POST body:
    - start_date (optional): Filter departments created from this date
    - end_date (optional): Filter departments created until this date
    - status (optional): Filter by department status
    
    Returns:
    - summary: Report metadata and summary
    - departments: List of department data
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset
        queryset = Department.objects.all()
        
        # Apply filters
        if validated_filters.get('start_date'):
            start_datetime = timezone.make_aware(
                datetime.combine(validated_filters['start_date'], datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        
        if validated_filters.get('end_date'):
            end_datetime = timezone.make_aware(
                datetime.combine(validated_filters['end_date'], datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        if validated_filters.get('status'):
            queryset = queryset.filter(status=validated_filters['status'])
        
        # Select related for optimization
        queryset = queryset.select_related('created_by')
        
        # Generate report
        report_data = DepartmentReportGenerator.generate_department_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='departments_list',
            user=request.user,
            status_code='200',
            description=f'Generated department report with {len(report_data["departments"])} departments',
            request=request,
            response_data={'count': len(report_data['departments'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating department report: {str(e)}")
        
        Activity.log_activity(
            activity_type='departments_list',
            user=request.user,
            status_code='500',
            description=f'Failed to generate department report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate department report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateTaskReports])
def generate_task_report(request):
    """
    Generate task report
    
    GET parameters / POST body:
    - start_date (optional): Filter tasks created from this date
    - end_date (optional): Filter tasks created until this date
    - status (optional): Filter by task status
    
    Returns:
    - summary: Report metadata and summary
    - tasks: List of task data with assignment statistics
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset
        queryset = Task.objects.all()
        
        # Apply filters
        if validated_filters.get('start_date'):
            start_datetime = timezone.make_aware(
                datetime.combine(validated_filters['start_date'], datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        
        if validated_filters.get('end_date'):
            end_datetime = timezone.make_aware(
                datetime.combine(validated_filters['end_date'], datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        if validated_filters.get('status'):
            queryset = queryset.filter(status=validated_filters['status'])
        
        # Select related for optimization
        queryset = queryset.select_related('created_by')
        
        # Generate report
        report_data = TaskReportGenerator.generate_task_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='tasks_list',
            user=request.user,
            status_code='200',
            description=f'Generated task report with {len(report_data["tasks"])} tasks',
            request=request,
            response_data={'count': len(report_data['tasks'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating task report: {str(e)}")
        
        Activity.log_activity(
            activity_type='tasks_list',
            user=request.user,
            status_code='500',
            description=f'Failed to generate task report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate task report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateTaskAssignmentReports])
def generate_task_assignment_report(request):
    """
    Generate task assignment report
    
    GET parameters / POST body:
    - start_date (optional): Filter assignments from this date
    - end_date (optional): Filter assignments until this date
    - user_id (optional): Filter by user
    - department_id (optional): Filter by department
    - status (optional): Filter by assignment status
    - priority (optional): Filter by priority
    
    Returns:
    - summary: Report metadata and summary
    - assignments: List of task assignment data
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset based on user role
        if request.user.role in ['admin', 'manager', 'analyst']:
            queryset = TaskAssignment.objects.all()
            
            # Managers see assignments in their department
            if request.user.role == 'manager' and request.user.department:
                queryset = queryset.filter(department=request.user.department)
        else:
            # Employees only see their own assignments
            queryset = TaskAssignment.objects.filter(user=request.user)
        
        # Apply filters
        if validated_filters.get('start_date'):
            queryset = queryset.filter(assignment_date__gte=validated_filters['start_date'])
        
        if validated_filters.get('end_date'):
            queryset = queryset.filter(assignment_date__lte=validated_filters['end_date'])
        
        if validated_filters.get('user_id'):
            # Only allow if user has permission
            if request.user.role in ['admin', 'manager', 'analyst']:
                queryset = queryset.filter(user_id=validated_filters['user_id'])
        
        if validated_filters.get('department_id'):
            queryset = queryset.filter(department_id=validated_filters['department_id'])
        
        if validated_filters.get('status'):
            queryset = queryset.filter(status=validated_filters['status'])
        
        if filters.get('priority'):
            queryset = queryset.filter(priority=filters['priority'])
        
        # Select related for optimization
        queryset = queryset.select_related('user', 'task', 'department', 'assigned_by')
        
        # Generate report
        report_data = TaskAssignmentReportGenerator.generate_assignment_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='task_assignments_list',
            user=request.user,
            status_code='200',
            description=f'Generated task assignment report with {len(report_data["assignments"])} assignments',
            request=request,
            response_data={'count': len(report_data['assignments'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating task assignment report: {str(e)}")
        
        Activity.log_activity(
            activity_type='task_assignments_list',
            user=request.user,
            status_code='500',
            description=f'Failed to generate task assignment report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate task assignment report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateDayOffReports])
def generate_dayoff_report(request):
    """
    Generate day-off request report
    
    GET parameters / POST body:
    - start_date (optional): Filter requests from this date
    - end_date (optional): Filter requests until this date
    - user_id (optional): Filter by user
    - status (optional): Filter by request status
    
    Returns:
    - summary: Report metadata and summary
    - day_off_requests: List of day-off request data
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset based on user role
        if request.user.role in ['admin', 'manager', 'analyst']:
            queryset = DayOffChangeRequest.objects.all()
            
            # Managers see requests from their department
            if request.user.role == 'manager' and request.user.department:
                queryset = queryset.filter(user__department=request.user.department)
        else:
            # Employees only see their own requests
            queryset = DayOffChangeRequest.objects.filter(user=request.user)
        
        # Apply filters
        if validated_filters.get('start_date'):
            start_datetime = timezone.make_aware(
                datetime.combine(validated_filters['start_date'], datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        
        if validated_filters.get('end_date'):
            end_datetime = timezone.make_aware(
                datetime.combine(validated_filters['end_date'], datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        if validated_filters.get('user_id'):
            # Only allow if user has permission
            if request.user.role in ['admin', 'manager', 'analyst']:
                queryset = queryset.filter(user_id=validated_filters['user_id'])
        
        if validated_filters.get('status'):
            queryset = queryset.filter(status=validated_filters['status'])
        
        # Select related for optimization
        queryset = queryset.select_related('user', 'approved_by')
        
        # Generate report
        report_data = DayOffReportGenerator.generate_dayoff_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='dayoff_requests_list',
            user=request.user,
            status_code='200',
            description=f'Generated day-off request report with {len(report_data["day_off_requests"])} requests',
            request=request,
            response_data={'count': len(report_data['day_off_requests'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating day-off report: {str(e)}")
        
        Activity.log_activity(
            activity_type='dayoff_requests_list',
            user=request.user,
            status_code='500',
            description=f'Failed to generate day-off report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate day-off report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateActivityReports])
def generate_activity_report(request):
    """
    Generate activity report
    
    GET parameters / POST body:
    - start_date (optional): Filter activities from this date
    - end_date (optional): Filter activities until this date
    - user_id (optional): Filter by user
    - activity_type (optional): Filter by activity type
    - status_code (optional): Filter by status code
    
    Returns:
    - summary: Report metadata and summary
    - activities: List of activity data
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Build queryset
        queryset = Activity.objects.all()
        
        # Apply filters BEFORE ordering and slicing
        if validated_filters.get('start_date'):
            start_datetime = timezone.make_aware(
                datetime.combine(validated_filters['start_date'], datetime.min.time())
            )
            queryset = queryset.filter(created_at__gte=start_datetime)
        
        if validated_filters.get('end_date'):
            end_datetime = timezone.make_aware(
                datetime.combine(validated_filters['end_date'], datetime.max.time())
            )
            queryset = queryset.filter(created_at__lte=end_datetime)
        
        if validated_filters.get('user_id'):
            queryset = queryset.filter(user_id=validated_filters['user_id'])
        
        if filters.get('activity_type'):
            queryset = queryset.filter(activity_type=filters['activity_type'])
        
        if filters.get('status_code'):
            queryset = queryset.filter(status_code=filters['status_code'])
        
        # Select related for optimization
        queryset = queryset.select_related('user')
        
        # Order by most recent first BEFORE slicing
        queryset = queryset.order_by('-created_at')
        
        # Limit to last 1000 activities for performance (AFTER ordering) and convert to list
        queryset = list(queryset[:1000])
        
        # Generate report
        report_data = ActivityReportGenerator.generate_activity_report(
            queryset, validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='api_request',
            user=request.user,
            status_code='200',
            description=f'Generated activity report with {len(report_data["activities"])} activities',
            request=request,
            response_data={'count': len(report_data['activities'])}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating activity report: {str(e)}")
        
        Activity.log_activity(
            activity_type='api_request',
            user=request.user,
            status_code='500',
            description=f'Failed to generate activity report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate activity report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGeneratePerformanceReports])
def generate_performance_report(request, user_id=None):
    """
    Generate performance report for a specific user or organization
    
    GET parameters / POST body:
    - user_id (optional): User ID to generate report for. If not provided:
        - Employees: defaults to their own ID
        - Admin/Manager/Analyst: generates org-wide performance report
    - start_date (optional): Filter from this date
    - end_date (optional): Filter until this date
    
    Returns:
    - summary: Report metadata and summary
    - performance_data: User performance metrics or org-wide metrics
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
            target_user_id = filters.get('user_id') or user_id
        else:
            filters = request.query_params.dict()
            target_user_id = filters.get('user_id') or user_id
        
        # Handle missing user_id based on role
        if not target_user_id:
            if request.user.role == 'employee':
                # Employees default to their own performance
                target_user_id = request.user.id
            else:
                # Admin/Manager/Analyst: generate organization-wide performance report
                return generate_organization_performance_report(request, filters)
        
        # Convert to int if it's a string
        target_user_id = int(target_user_id)
        
        # Check if user exists
        try:
            target_user = CustomUser.objects.get(id=target_user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found',
                'message': f'User with ID {target_user_id} does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if request.user.role == 'employee':
            # Employees can only view their own performance
            if int(target_user_id) != request.user.id:
                return Response({
                    'error': 'Permission denied',
                    'message': 'You can only view your own performance report'
                }, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'manager':
            # Managers can view performance of users in their department
            if request.user.department and target_user.department:
                if request.user.department.id != target_user.department.id:
                    return Response({
                        'error': 'Permission denied',
                        'message': 'You can only view performance of users in your department'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Generate report
        report_data = PerformanceReportGenerator.generate_performance_report(
            target_user_id, validated_filters, request.user
        )
        
        if not report_data:
            return Response({
                'error': 'Failed to generate report',
                'message': 'Could not generate performance report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_user',
            user=request.user,
            status_code='200',
            description=f'Generated performance report for {target_user.full_name}',
            request=request,
            related_user_id=target_user_id,
            response_data={'user_id': target_user_id}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        
        Activity.log_activity(
            activity_type='performance_view_user',
            user=request.user,
            status_code='500',
            description=f'Failed to generate performance report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate performance report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanGenerateOrganizationReports])
def generate_organization_report(request):
    """
    Generate organization-wide report
    
    GET parameters / POST body:
    - start_date (optional): Filter from this date
    - end_date (optional): Filter until this date
    
    Returns:
    - summary: Report metadata and summary
    - organization_data: Organization-wide metrics
    - statistics: Aggregated statistics
    """
    try:
        # Get filters from request
        if request.method == 'POST':
            filters = request.data
        else:
            filters = request.query_params.dict()
        
        # Validate filters
        serializer = ReportFilterSerializer(data=filters)
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid filters',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_filters = serializer.validated_data
        
        # Generate report
        report_data = OrganizationReportGenerator.generate_organization_report(
            validated_filters, request.user
        )
        
        # Log activity
        Activity.log_activity(
            activity_type='performance_view_organization',
            user=request.user,
            status_code='200',
            description='Generated organization-wide report',
            request=request,
            response_data={'filters': {
                'start_date': validated_filters.get('start_date').isoformat() if validated_filters.get('start_date') else None,
                'end_date': validated_filters.get('end_date').isoformat() if validated_filters.get('end_date') else None,
            }}
        )
        
        return Response(report_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error generating organization report: {str(e)}")
        
        Activity.log_activity(
            activity_type='performance_view_organization',
            user=request.user,
            status_code='500',
            description=f'Failed to generate organization report: {str(e)}',
            request=request
        )
        
        return Response({
            'error': 'Failed to generate organization report',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_reports(request):
    """
    Get list of available reports based on user role
    
    Returns:
    - available_reports: List of reports user can generate
    """
    try:
        user_role = request.user.role
        
        reports = {
            'admin': [
                'user_report',
                'department_report',
                'task_report',
                'task_assignment_report',
                'dayoff_report',
                'activity_report',
                'performance_report',
                'organization_report',
            ],
            'manager': [
                'user_report',
                'department_report',
                'task_report',
                'task_assignment_report',
                'dayoff_report',
                'performance_report',
            ],
            'analyst': [
                'user_report',
                'department_report',
                'task_report',
                'task_assignment_report',
                'dayoff_report',
                'activity_report',
                'performance_report',
                'organization_report',
            ],
            'employee': [
                'task_assignment_report',  # Own assignments only
                'dayoff_report',  # Own requests only
                'performance_report',  # Own performance only
            ],
        }
        
        available_reports = reports.get(user_role, [])
        
        return Response({
            'user_role': user_role,
            'available_reports': available_reports,
            'report_descriptions': {
                'user_report': 'Generate reports about users in the system',
                'department_report': 'Generate reports about departments',
                'task_report': 'Generate reports about tasks and their assignments',
                'task_assignment_report': 'Generate reports about task assignments',
                'dayoff_report': 'Generate reports about day-off change requests',
                'activity_report': 'Generate reports about system activities',
                'performance_report': 'Generate performance reports for users',
                'organization_report': 'Generate organization-wide reports',
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting available reports: {str(e)}")
        return Response({
            'error': 'Failed to get available reports',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)