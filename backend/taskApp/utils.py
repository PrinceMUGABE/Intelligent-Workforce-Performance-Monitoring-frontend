# taskApp/utils.py

import time
from activityApp.models import Activity

def log_task_activity(activity_type, user, task=None, request=None, 
                      description='', status_code='200', 
                      request_data=None, response_data=None):
    """
    Helper function to log task-related activities
    """
    start_time = time.time()
    
    try:
        # Sanitize request data to remove sensitive information
        sanitized_request_data = sanitize_request_data(request_data) if request_data else None
        sanitized_response_data = sanitize_response_data(response_data) if response_data else None
        
        # Calculate duration if we have request
        duration_ms = None
        if request:
            # In a real implementation, you might track start time differently
            duration_ms = int((time.time() - start_time) * 1000)
        
        # Create the activity log
        activity = Activity.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=status_code,
            description=description,
            request=request,
            related_task_id=task.id if task else None,
            duration_ms=duration_ms,
            request_data=sanitized_request_data,
            response_data=sanitized_response_data,
        )
        
        return activity
    
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        return None

def sanitize_request_data(data):
    """
    Remove sensitive information from request data
    """
    if not data:
        return None
    
    # Create a copy to avoid modifying original
    sanitized = data.copy() if hasattr(data, 'copy') else dict(data)
    
    # List of sensitive fields to remove or mask
    sensitive_fields = ['password', 'token', 'secret', 'key', 'authorization', 'bearer']
    
    def sanitize_dict(d):
        if isinstance(d, dict):
            for key, value in list(d.items()):
                # Check if key contains sensitive information
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    d[key] = '***REMOVED***'
                elif isinstance(value, (dict, list)):
                    sanitize_dict(value)
        elif isinstance(d, list):
            for item in d:
                sanitize_dict(item)
        return d
    
    return sanitize_dict(sanitized)

def sanitize_response_data(data):
    """
    Remove sensitive information from response data
    """
    if not data:
        return None
    
    # For response data, we typically want to keep structure but remove sensitive info
    sanitized = data.copy() if hasattr(data, 'copy') else dict(data)
    
    # Remove or mask sensitive response data
    sensitive_response_fields = ['token', 'access_token', 'refresh_token', 'password']
    
    def sanitize_dict(d):
        if isinstance(d, dict):
            for key, value in list(d.items()):
                if key in sensitive_response_fields:
                    d[key] = '***REMOVED***'
                elif isinstance(value, (dict, list)):
                    sanitize_dict(value)
        elif isinstance(d, list):
            for item in d:
                sanitize_dict(item)
        return d
    
    return sanitize_dict(sanitized)