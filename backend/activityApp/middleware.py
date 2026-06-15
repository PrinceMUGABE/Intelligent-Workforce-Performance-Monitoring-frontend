# activityApp/middleware.py

from .models import Activity
from .utils import ActivityTimer
import json


class ActivityTrackingMiddleware:
    """
    Middleware to automatically log API activities
    
    This middleware tracks all API requests and responses, logging them as activities.
    It captures request details, response status, and performance metrics.
    
    To enable, add to MIDDLEWARE in settings.py:
        'activityApp.middleware.ActivityTrackingMiddleware',
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Endpoints to exclude from automatic logging
        self.excluded_endpoints = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            # Add activity endpoints to avoid recursive logging
            '/api/activities/',
            '/api/activity/',
        ]
    
    def __call__(self, request):
        # Skip excluded endpoints
        if any(request.path.startswith(endpoint) for endpoint in self.excluded_endpoints):
            return self.get_response(request)
        
        # Start timer
        timer = ActivityTimer()
        timer.__enter__()
        
        # Process request
        response = self.get_response(request)
        
        # Stop timer
        timer.__exit__(None, None, None)
        
        # Log activity asynchronously (to avoid blocking the response)
        try:
            self._log_activity(request, response, timer.duration_ms)
        except Exception as e:
            # Don't let logging errors affect the response
            print(f"Error in activity tracking middleware: {str(e)}")
        
        return response
    
    def _log_activity(self, request, response, duration_ms):
        """Log the activity"""
        
        # Determine activity type based on endpoint and method
        activity_type = self._determine_activity_type(request)
        
        # Get user (if authenticated)
        user = request.user if request.user.is_authenticated else None
        
        # Get status code
        status_code = str(response.status_code)
        
        # Create description
        description = f"{request.method} {request.path}"
        
        # Extract request data (sanitized)
        request_data = self._extract_request_data(request)
        
        # Only log if it's an API request (starts with /api/)
        if request.path.startswith('/api/'):
            Activity.log_activity(
                activity_type=activity_type,
                user=user,
                status_code=status_code,
                description=description,
                request=request,
                duration_ms=duration_ms,
                request_data=request_data
            )
    
    def _determine_activity_type(self, request):
        """Determine activity type based on request path and method"""
        
        path = request.path.lower()
        method = request.method.upper()
        
        # Authentication endpoints
        if 'login' in path:
            return 'user_login'
        elif 'logout' in path:
            return 'user_logout'
        elif 'register' in path:
            return 'user_registration'
        elif 'password' in path and 'reset' in path:
            if method == 'POST':
                return 'password_reset_request'
            return 'password_reset_complete'
        elif 'password' in path and 'change' in path:
            return 'password_change'
        elif 'otp' in path:
            if 'request' in path:
                return 'otp_request'
            elif 'verify' in path:
                return 'otp_verification'
        
        # User management endpoints
        elif 'user' in path:
            if method == 'POST':
                return 'user_create'
            elif method in ['PUT', 'PATCH']:
                return 'user_update'
            elif method == 'DELETE':
                return 'user_delete'
            elif method == 'GET':
                if path.endswith('/users/') or 'list' in path:
                    return 'users_list'
                return 'user_view'
        
        # Department endpoints
        elif 'department' in path:
            if method == 'POST':
                return 'department_create'
            elif method in ['PUT', 'PATCH']:
                return 'department_update'
            elif method == 'DELETE':
                return 'department_delete'
            elif method == 'GET':
                if path.endswith('/departments/') or 'list' in path:
                    return 'departments_list'
                return 'department_view'
        
        # Contact form
        elif 'contact' in path:
            return 'contact_submission'
        
        # Default
        return 'api_request'
    
    def _extract_request_data(self, request):
        """Extract and sanitize request data"""
        data = {}
        
        # GET parameters
        if request.GET:
            data['query_params'] = dict(request.GET)
        
        # POST/PUT/PATCH data
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    data['body'] = json.loads(request.body.decode('utf-8'))
                elif request.POST:
                    data['body'] = dict(request.POST)
            except:
                pass
        
        return data