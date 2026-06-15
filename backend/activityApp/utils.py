# activityApp/utils.py

from .models import Activity
import time
import json


def log_activity(activity_type, user=None, status_code='200', description='',
                 request=None, related_user_id=None, related_department_id=None,
                 duration_ms=None, request_data=None, response_data=None):
    """
    Convenience function to log an activity
    
    Args:
        activity_type (str): Type of activity from Activity.ACTIVITY_TYPE_CHOICES
        user (CustomUser): User who performed the activity
        status_code (str): HTTP status code
        description (str): Description of the activity
        request (HttpRequest): Django request object
        related_user_id (int): ID of related user (if applicable)
        related_department_id (int): ID of related department (if applicable)
        duration_ms (int): Duration of the operation in milliseconds
        request_data (dict): Request data (will be sanitized)
        response_data (dict): Response data (will be sanitized)
    
    Returns:
        Activity: Created activity instance
    
    Example:
        from activityApp.utils import log_activity
        
        log_activity(
            activity_type='user_login',
            user=request.user,
            status_code='200',
            description='User logged in successfully',
            request=request
        )
    """
    try:
        # Sanitize sensitive data
        sanitized_request_data = sanitize_data(request_data) if request_data else None
        sanitized_response_data = sanitize_data(response_data) if response_data else None
        
        return Activity.log_activity(
            activity_type=activity_type,
            user=user,
            status_code=str(status_code),
            description=description,
            request=request,
            related_user_id=related_user_id,
            related_department_id=related_department_id,
            duration_ms=duration_ms,
            request_data=sanitized_request_data,
            response_data=sanitized_response_data
        )
    except Exception as e:
        # Log the error but don't raise it to avoid breaking the main flow
        print(f"Error logging activity: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def sanitize_data(data):
    """
    Remove sensitive information from data before logging
    
    Args:
        data (dict): Data to sanitize
    
    Returns:
        dict: Sanitized data
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = [
        'password',
        'confirm_password',
        'current_password',
        'new_password',
        'otp',
        'token',
        'access_token',
        'refresh_token',
        'secret',
        'api_key',
        'authorization'
    ]
    
    sanitized = {}
    for key, value in data.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized


class ActivityTimer:
    """
    Context manager to measure activity duration
    
    Usage:
        with ActivityTimer() as timer:
            # Perform operation
            result = some_function()
        
        duration_ms = timer.duration_ms
    """
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration_ms = int((self.end_time - self.start_time) * 1000)
        return False


def get_client_ip(request):
    """
    Get client IP address from request
    
    Args:
        request (HttpRequest): Django request object
    
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device info
    
    Args:
        user_agent_string (str): User agent string
    
    Returns:
        dict: Parsed device information
    """
    try:
        from user_agents import parse
        user_agent = parse(user_agent_string)
        
        return {
            'device_type': 'Mobile' if user_agent.is_mobile else 'Tablet' if user_agent.is_tablet else 'Desktop' if user_agent.is_pc else 'Unknown',
            'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}" if user_agent.browser.version_string else user_agent.browser.family,
            'operating_system': f"{user_agent.os.family} {user_agent.os.version_string}" if user_agent.os.version_string else user_agent.os.family
        }
    except Exception as e:
        print(f"Error parsing user agent: {str(e)}")
        return {
            'device_type': 'Unknown',
            'browser': 'Unknown',
            'operating_system': 'Unknown'
        }


def log_authentication_activity(activity_type, user, status_code, description, request):
    """
    Helper function specifically for authentication activities
    
    Args:
        activity_type (str): Type of auth activity
        user (CustomUser): User object
        status_code (str): HTTP status code
        description (str): Description
        request (HttpRequest): Django request object
    """
    return log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request
    )


def log_user_management_activity(activity_type, user, target_user_id, status_code, description, request):
    """
    Helper function specifically for user management activities
    
    Args:
        activity_type (str): Type of user management activity
        user (CustomUser): User performing the action
        target_user_id (int): ID of the user being managed
        status_code (str): HTTP status code
        description (str): Description
        request (HttpRequest): Django request object
    """
    return log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request,
        related_user_id=target_user_id
    )


def log_department_activity(activity_type, user, department_id, status_code, description, request):
    """
    Helper function specifically for department activities
    
    Args:
        activity_type (str): Type of department activity
        user (CustomUser): User performing the action
        department_id (int): ID of the department
        status_code (str): HTTP status code
        description (str): Description
        request (HttpRequest): Django request object
    """
    return log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request,
        related_department_id=department_id
    )