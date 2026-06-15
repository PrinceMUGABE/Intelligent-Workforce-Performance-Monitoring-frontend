# taskApp/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Task
from .serializers import TaskSerializer
from activityApp.models import Activity
from .utils import log_task_activity  # Import the helper function


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    """
    Create a new task
    """
    try:
        serializer = TaskSerializer(data=request.data)
        
        if serializer.is_valid():
            # Set created_by to current user if not provided
            task = serializer.save(created_by=request.user)
            
            # Log the activity
            log_task_activity(
                activity_type='task_create',
                user=request.user,
                task=task,
                request=request,
                description=f'Task "{task.name}" created successfully',
                status_code='201',
                request_data=request.data,
                response_data=serializer.data
            )
            
            print(f"Task created successfully: {serializer.data['name']}")
            return Response({
                'success': True,
                'message': 'Task created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            # Log failed creation attempt
            log_task_activity(
                activity_type='task_create',
                user=request.user,
                request=request,
                description=f'Task creation failed: {serializer.errors}',
                status_code='400',
                request_data=request.data,
                response_data={'errors': serializer.errors}
            )
            
            print(f"Task creation validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error creating task: {str(e)}',
            status_code='500',
            request_data=request.data,
            response_data={'error': str(e)}
        )
        
        print(f"Error creating task: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while creating the task',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_tasks(request):
    """
    Retrieve all tasks without filters
    """
    try:
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        
        # Log the activity
        log_task_activity(
            activity_type='tasks_list',
            user=request.user,
            request=request,
            description=f'Viewed all tasks ({tasks.count()} tasks)',
            status_code='200',
            response_data={'count': tasks.count()}
        )
        
        print(f"Retrieved {tasks.count()} tasks")
        return Response({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'count': tasks.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error retrieving all tasks: {str(e)}',
            status_code='500'
        )
        
        print(f"Error retrieving tasks: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving tasks',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_by_id(request, task_id):
    """
    Retrieve a specific task by ID
    """
    try:
        if not task_id:
            # Log missing task ID
            log_task_activity(
                activity_type='task_view',
                user=request.user,
                request=request,
                description='Task ID not provided',
                status_code='400'
            )
            
            print("Task ID not provided")
            return Response({
                'success': False,
                'message': 'Task ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            # Log task not found
            log_task_activity(
                activity_type='task_view',
                user=request.user,
                request=request,
                description=f'Task with ID {task_id} not found',
                status_code='404'
            )
            
            print(f"Task with ID {task_id} not found")
            return Response({
                'success': False,
                'message': f'Task with ID {task_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(task)
        
        # Log successful task view
        log_task_activity(
            activity_type='task_view',
            user=request.user,
            task=task,
            request=request,
            description=f'Viewed task "{task.name}" (ID: {task.id})',
            status_code='200',
            response_data={'task_id': task.id, 'task_name': task.name}
        )
        
        print(f"Task retrieved successfully: {task.name}")
        return Response({
            'success': True,
            'message': 'Task retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        # Log invalid task ID format
        log_task_activity(
            activity_type='task_view',
            user=request.user,
            request=request,
            description=f'Invalid task ID format: {task_id}',
            status_code='400'
        )
        
        print(f"Invalid task ID format: {task_id}")
        return Response({
            'success': False,
            'message': 'Invalid task ID format'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error retrieving task by ID {task_id}: {str(e)}',
            status_code='500'
        )
        
        print(f"Error retrieving task by ID: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving the task',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_by_name(request, task_name):
    """
    Retrieve tasks by name (exact match)
    """
    try:
        if not task_name or not task_name.strip():
            # Log missing task name
            log_task_activity(
                activity_type='task_view_by_name',
                user=request.user,
                request=request,
                description='Task name not provided',
                status_code='400'
            )
            
            print("Task name not provided")
            return Response({
                'success': False,
                'message': 'Task name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        clean_task_name = task_name.strip()
        tasks = Task.objects.filter(name__iexact=clean_task_name)
        
        if not tasks.exists():
            # Log task not found
            log_task_activity(
                activity_type='task_view_by_name',
                user=request.user,
                request=request,
                description=f'No tasks found with name: {clean_task_name}',
                status_code='404'
            )
            
            print(f"No tasks found with name: {clean_task_name}")
            return Response({
                'success': False,
                'message': f'No tasks found with name: {clean_task_name}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(tasks, many=True)
        
        # Log successful search
        log_task_activity(
            activity_type='task_view_by_name',
            user=request.user,
            request=request,
            description=f'Found {tasks.count()} task(s) with name: {clean_task_name}',
            status_code='200',
            response_data={'count': tasks.count(), 'task_name': clean_task_name}
        )
        
        print(f"Found {tasks.count()} task(s) with name: {clean_task_name}")
        return Response({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'count': tasks.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error retrieving task by name {task_name}: {str(e)}',
            status_code='500'
        )
        
        print(f"Error retrieving task by name: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while retrieving tasks by name',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    """
    Update a task by ID
    """
    try:
        if not task_id:
            # Log missing task ID
            log_task_activity(
                activity_type='task_update',
                user=request.user,
                request=request,
                description='Task ID not provided for update',
                status_code='400'
            )
            
            print("Task ID not provided")
            return Response({
                'success': False,
                'message': 'Task ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            # Log task not found
            log_task_activity(
                activity_type='task_update',
                user=request.user,
                request=request,
                description=f'Task with ID {task_id} not found for update',
                status_code='404'
            )
            
            print(f"Task with ID {task_id} not found")
            return Response({
                'success': False,
                'message': f'Task with ID {task_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Store old data for comparison
        old_status = task.status
        old_name = task.name
        
        # Use partial=True for PATCH requests to allow partial updates
        partial = request.method == 'PATCH'
        serializer = TaskSerializer(task, data=request.data, partial=partial)
        
        if serializer.is_valid():
            updated_task = serializer.save()
            
            # Check if status was changed
            status_changed = old_status != updated_task.status
            description = f'Task "{updated_task.name}" updated successfully'
            
            if status_changed:
                description = f'Task "{updated_task.name}" updated - status changed from {old_status} to {updated_task.status}'
                # Log status change specifically
                log_task_activity(
                    activity_type='task_status_change',
                    user=request.user,
                    task=updated_task,
                    request=request,
                    description=f'Task status changed from {old_status} to {updated_task.status}',
                    status_code='200',
                    request_data=request.data,
                    response_data={'old_status': old_status, 'new_status': updated_task.status}
                )
            
            # Log the update activity
            log_task_activity(
                activity_type='task_update',
                user=request.user,
                task=updated_task,
                request=request,
                description=description,
                status_code='200',
                request_data=request.data,
                response_data=serializer.data
            )
            
            print(f"Task updated successfully: {updated_task.name}")
            return Response({
                'success': True,
                'message': 'Task updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            # Log failed update attempt
            log_task_activity(
                activity_type='task_update',
                user=request.user,
                task=task,
                request=request,
                description=f'Task update validation failed: {serializer.errors}',
                status_code='400',
                request_data=request.data,
                response_data={'errors': serializer.errors}
            )
            
            print(f"Task update validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ValueError:
        # Log invalid task ID format
        log_task_activity(
            activity_type='task_update',
            user=request.user,
            request=request,
            description=f'Invalid task ID format: {task_id}',
            status_code='400'
        )
        
        print(f"Invalid task ID format: {task_id}")
        return Response({
            'success': False,
            'message': 'Invalid task ID format'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error updating task {task_id}: {str(e)}',
            status_code='500',
            request_data=request.data
        )
        
        print(f"Error updating task: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while updating the task',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task(request, task_id):
    """
    Delete a task by ID
    """
    try:
        if not task_id:
            # Log missing task ID
            log_task_activity(
                activity_type='task_delete',
                user=request.user,
                request=request,
                description='Task ID not provided for deletion',
                status_code='400'
            )
            
            print("Task ID not provided")
            return Response({
                'success': False,
                'message': 'Task ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            # Log task not found
            log_task_activity(
                activity_type='task_delete',
                user=request.user,
                request=request,
                description=f'Task with ID {task_id} not found for deletion',
                status_code='404'
            )
            
            print(f"Task with ID {task_id} not found")
            return Response({
                'success': False,
                'message': f'Task with ID {task_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        task_name = task.name
        task_id_val = task.id
        
        # Store task data before deletion for logging
        task_data = {
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'created_by': task.created_by.id if task.created_by else None
        }
        
        task.delete()
        
        # Log successful deletion
        log_task_activity(
            activity_type='task_delete',
            user=request.user,
            request=request,
            description=f'Task "{task_name}" (ID: {task_id_val}) deleted successfully',
            status_code='200',
            response_data={'deleted_task': task_data}
        )
        
        print(f"Task deleted successfully: {task_name}")
        return Response({
            'success': True,
            'message': f'Task "{task_name}" deleted successfully',
            'deleted_task': task_data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        # Log invalid task ID format
        log_task_activity(
            activity_type='task_delete',
            user=request.user,
            request=request,
            description=f'Invalid task ID format: {task_id}',
            status_code='400'
        )
        
        print(f"Invalid task ID format: {task_id}")
        return Response({
            'success': False,
            'message': 'Invalid task ID format'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        # Log error
        log_task_activity(
            activity_type='api_error',
            user=request.user,
            request=request,
            description=f'Error deleting task {task_id}: {str(e)}',
            status_code='500'
        )
        
        print(f"Error deleting task: {str(e)}")
        return Response({
            'success': False,
            'message': 'An error occurred while deleting the task',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)