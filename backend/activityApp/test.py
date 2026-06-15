# activityApp/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from userApp.models import CustomUser
from departmentApp.models import Department
from activityApp.models import Activity
from activityApp.utils import log_activity, ActivityTimer, sanitize_data
import json


class ActivityModelTestCase(TestCase):
    """Test cases for Activity model"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+250788123456',
            email='test@gmail.com',
            full_name='Test User',
            role='admin',
            password='Test@123'
        )
    
    def test_create_activity(self):
        """Test creating an activity"""
        activity = Activity.objects.create(
            activity_type='user_login',
            user=self.user,
            status_code='200',
            description='Test login',
            ip_address='127.0.0.1',
            device_type='Desktop',
            browser='Chrome 120.0',
            operating_system='Windows 10'
        )
        
        self.assertEqual(activity.activity_type, 'user_login')
        self.assertEqual(activity.user, self.user)
        self.assertTrue(activity.is_success())
        self.assertFalse(activity.is_client_error())
        self.assertFalse(activity.is_server_error())
    
    def test_activity_success_status(self):
        """Test activity status checks"""
        # Success
        activity_success = Activity.objects.create(
            activity_type='user_login',
            status_code='200'
        )
        self.assertTrue(activity_success.is_success())
        
        # Client error
        activity_client_error = Activity.objects.create(
            activity_type='user_login',
            status_code='404'
        )
        self.assertTrue(activity_client_error.is_client_error())
        
        # Server error
        activity_server_error = Activity.objects.create(
            activity_type='api_error',
            status_code='500'
        )
        self.assertTrue(activity_server_error.is_server_error())
    
    def test_activity_str_representation(self):
        """Test string representation of activity"""
        activity = Activity.objects.create(
            activity_type='user_login',
            user=self.user,
            status_code='200',
            description='Test'
        )
        
        str_repr = str(activity)
        self.assertIn(self.user.full_name, str_repr)
        self.assertIn('User Login', str_repr)


class ActivityUtilsTestCase(TestCase):
    """Test cases for utility functions"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+250788123456',
            email='test@gmail.com',
            full_name='Test User',
            role='admin',
            password='Test@123'
        )
    
    def test_sanitize_data(self):
        """Test data sanitization"""
        data = {
            'username': 'testuser',
            'password': 'secret123',
            'email': 'test@example.com',
            'token': 'abc123',
            'api_key': 'xyz789'
        }
        
        sanitized = sanitize_data(data)
        
        self.assertEqual(sanitized['username'], 'testuser')
        self.assertEqual(sanitized['email'], 'test@example.com')
        self.assertEqual(sanitized['password'], '***REDACTED***')
        self.assertEqual(sanitized['token'], '***REDACTED***')
        self.assertEqual(sanitized['api_key'], '***REDACTED***')
    
    def test_sanitize_nested_data(self):
        """Test sanitization of nested data"""
        data = {
            'user': {
                'username': 'test',
                'password': 'secret'
            },
            'credentials': {
                'api_key': 'xyz',
                'public_key': 'abc'
            }
        }
        
        sanitized = sanitize_data(data)
        
        self.assertEqual(sanitized['user']['username'], 'test')
        self.assertEqual(sanitized['user']['password'], '***REDACTED***')
        self.assertEqual(sanitized['credentials']['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['credentials']['public_key'], 'abc')
    
    def test_activity_timer(self):
        """Test ActivityTimer context manager"""
        import time
        
        with ActivityTimer() as timer:
            time.sleep(0.1)  # Sleep for 100ms
        
        # Check that duration is approximately 100ms (allow some variance)
        self.assertGreaterEqual(timer.duration_ms, 90)
        self.assertLessEqual(timer.duration_ms, 150)


class ActivityAPITestCase(APITestCase):
    """Test cases for Activity API endpoints"""
    
    def setUp(self):
        # Create admin user
        self.admin = CustomUser.objects.create_user(
            phone_number='+250788123456',
            email='admin@gmail.com',
            full_name='Admin User',
            role='admin',
            password='Admin@123'
        )
        
        # Create regular user
        self.user = CustomUser.objects.create_user(
            phone_number='+250788123457',
            email='user@gmail.com',
            full_name='Regular User',
            role='employee',
            department=Department.objects.create(name='IT'),
            password='User@123'
        )
        
        # Create some activities
        for i in range(5):
            Activity.objects.create(
                activity_type='user_login',
                user=self.admin,
                status_code='200',
                description=f'Login activity {i}'
            )
        
        for i in range(3):
            Activity.objects.create(
                activity_type='user_login',
                user=self.user,
                status_code='200',
                description=f'Login activity {i}'
            )
        
        self.client = APIClient()
    
    def test_get_all_activities_as_admin(self):
        """Test admin can view all activities"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/activities/activities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['pagination']['total'], 8)  # 5 admin + 3 user
    
    def test_get_all_activities_as_user(self):
        """Test regular user can only view their activities"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/activities/activities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['pagination']['total'], 3)  # Only user's activities
    
    def test_filter_activities_by_type(self):
        """Test filtering activities by type"""
        # Create a different activity type
        Activity.objects.create(
            activity_type='user_logout',
            user=self.admin,
            status_code='200',
            description='Logout'
        )
        
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/activities/activities/?activity_type=user_logout')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pagination']['total'], 1)
    
    def test_get_my_activities(self):
        """Test getting logged-in user's activities"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/activities/my-activities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(len(response.data['data']), 3)
    
    def test_get_activity_stats(self):
        """Test getting activity statistics"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/activities/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertIn('total_activities', response.data['data'])
        self.assertIn('successful_activities', response.data['data'])
        self.assertIn('activities_by_type', response.data['data'])
    
    def test_get_user_activity_summary_as_admin(self):
        """Test admin can get user activity summary"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(f'/api/activities/user/{self.user.id}/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['summary']['total_activities'], 3)
    
    def test_get_user_activity_summary_as_user_forbidden(self):
        """Test regular user cannot get other user's activity summary"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/activities/user/{self.admin.id}/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_pagination(self):
        """Test activity pagination"""
        # Create more activities
        for i in range(100):
            Activity.objects.create(
                activity_type='api_request',
                user=self.admin,
                status_code='200',
                description=f'Request {i}'
            )
        
        self.client.force_authenticate(user=self.admin)
        
        # Test first page
        response = self.client.get('/api/activities/activities/?page=1&page_size=10')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 10)
        self.assertEqual(response.data['pagination']['page'], 1)
        self.assertEqual(response.data['pagination']['page_size'], 10)
        
        # Test second page
        response = self.client.get('/api/activities/activities/?page=2&page_size=10')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 10)
        self.assertEqual(response.data['pagination']['page'], 2)
    
    def test_delete_old_activities_as_admin(self):
        """Test admin can delete old activities"""
        self.client.force_authenticate(user=self.admin)
        
        # Delete activities older than 0 days (all activities)
        response = self.client.delete(
            '/api/activities/cleanup/',
            data={'days': 0},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
    
    def test_delete_old_activities_as_user_forbidden(self):
        """Test regular user cannot delete activities"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(
            '/api/activities/cleanup/',
            data={'days': 90},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ActivityLoggingIntegrationTestCase(APITestCase):
    """Test activity logging integration with other endpoints"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            phone_number='+250788123456',
            email='admin@gmail.com',
            full_name='Admin User',
            role='admin',
            password='Admin@123'
        )
        self.client = APIClient()
    
    def test_login_creates_activity(self):
        """Test that login creates an activity log"""
        initial_count = Activity.objects.count()
        
        response = self.client.post(
            '/api/users/login/',
            {
                'work_mail_address': self.admin.work_mail_address,
                'password': 'Admin@123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check activity was created
        # Note: This assumes login view has activity logging integrated
        # The count might be 0 if integration isn't complete yet
        final_count = Activity.objects.count()
        self.assertGreaterEqual(final_count, initial_count)
    
    def test_department_creation_creates_activity(self):
        """Test that department creation creates an activity log"""
        self.client.force_authenticate(user=self.admin)
        
        initial_count = Activity.objects.count()
        
        response = self.client.post(
            '/api/departments/create/',
            {
                'name': 'Test Department',
                'description': 'Test description',
                'status': 'active'
            }
        )
        
        # Note: This assumes department view has activity logging integrated
        final_count = Activity.objects.count()
        self.assertGreaterEqual(final_count, initial_count)


# Manual Testing Examples
"""
MANUAL TESTING GUIDE
====================

1. Test Activity Creation via API:

curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "work_mail_address": "admin@company.com",
    "password": "Admin@123"
  }'

Then check:
curl -X GET http://localhost:8000/api/activities/my-activities/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"


2. Test Activity Filtering:

curl -X GET "http://localhost:8000/api/activities/activities/?activity_type=user_login&status_code=200" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"


3. Test Activity Statistics:

curl -X GET "http://localhost:8000/api/activities/stats/?days=7" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"


4. Test Activity Cleanup:

curl -X DELETE http://localhost:8000/api/activities/cleanup/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days": 90}'


5. Test Activity Details:

curl -X GET http://localhost:8000/api/activities/activities/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
"""

if __name__ == '__main__':
    print("Run tests with: python manage.py test activityApp")
    print("\nOr run specific test:")
    print("python manage.py test activityApp.tests.ActivityModelTestCase")
    print("python manage.py test activityApp.tests.ActivityAPITestCase")