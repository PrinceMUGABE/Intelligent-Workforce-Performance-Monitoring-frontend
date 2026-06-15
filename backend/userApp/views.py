# views.py

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.db.utils import IntegrityError
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import CustomUser
from .serializers import CustomUserSerializer, ContactUsSerializer, DepartmentSerializer
import re
import random
import string
import logging
import traceback
import time
from departmentApp.models import Department
from activityApp.models import Activity  # Import Activity model

# Configure logging
logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================

def is_valid_password(password):
    """Validate password complexity."""
    try:
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        if not any(char.isdigit() for char in password):
            return "Password must include at least one number."
        if not any(char.isupper() for char in password):
            return "Password must include at least one uppercase letter."
        if not any(char.islower() for char in password):
            return "Password must include at least one lowercase letter."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return "Password must include at least one special character (!@#$%^&* etc.)."
        return None
    except Exception as e:
        error_msg = f"Error validating password: {str(e)}"
        print(error_msg)
        return "Error validating password format."

def is_valid_email(email):
    """Validate email format and domain."""
    try:
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        
        # Check format
        if not re.match(email_regex, email):
            return "Invalid email format."
        
        # Check if it's a Gmail for personal email
        if not email.endswith("@gmail.com"):
            return "Only Gmail addresses are allowed for personal email."
        
        return None
    except Exception as e:
        error_msg = f"Error validating email: {str(e)}"
        print(error_msg)
        return "Error validating email format."

def is_valid_phone(phone_number):
    """Validate phone number format."""
    try:
        # Remove spaces and check if it contains only digits and + sign
        cleaned_phone = phone_number.replace(" ", "").replace("-", "")
        if not cleaned_phone.startswith("+"):
            return "Phone number must start with country code (e.g., +250)"
        
        # Check if remaining characters are digits
        if not cleaned_phone[1:].isdigit():
            return "Phone number must contain only digits after the country code."
        
        # Check length (international format typically 10-15 digits)
        if len(cleaned_phone) < 10 or len(cleaned_phone) > 16:
            return "Phone number must be between 10 and 15 digits (including country code)."
        
        return None
    except Exception as e:
        error_msg = f"Error validating phone number: {str(e)}"
        print(error_msg)
        return "Error validating phone number format."

def generate_secure_password():
    """Generate a secure random password that meets complexity requirements."""
    try:
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special_chars)
        ]
        
        all_chars = lowercase + uppercase + digits + special_chars
        password.extend(random.choice(all_chars) for _ in range(4))
        
        random.shuffle(password)
        return ''.join(password)
    except Exception as e:
        error_msg = f"Error generating secure password: {str(e)}"
        print(error_msg)
        return None

def log_user_activity(activity_type, user, request, status_code, description, 
                     related_user_id=None, duration_ms=None, request_data=None, 
                     response_data=None, sanitize_sensitive=True):
    """
    Helper function to log user-related activities
    """
    # Sanitize sensitive data if requested
    sanitized_request_data = None
    sanitized_response_data = None
    
    if sanitize_sensitive and request_data:
        sanitized_request_data = request_data.copy()
        # Remove sensitive fields
        sensitive_fields = ['password', 'confirm_password', 'new_password', 
                           'current_password', 'token', 'refresh_token', 
                           'access_token', 'secret', 'key', 'authorization',
                           'otp']
        for field in sensitive_fields:
            if field in sanitized_request_data:
                sanitized_request_data[field] = '***REDACTED***'
    
    if sanitize_sensitive and response_data:
        sanitized_response_data = response_data.copy()
        # Remove sensitive data from response
        if isinstance(sanitized_response_data, dict):
            sensitive_response_fields = ['token', 'refresh', 'access', 'otp']
            for field in sensitive_response_fields:
                if field in sanitized_response_data:
                    sanitized_response_data[field] = '***REDACTED***'
    
    # Log the activity
    Activity.log_activity(
        activity_type=activity_type,
        user=user,
        status_code=status_code,
        description=description,
        request=request,
        related_user_id=related_user_id,
        duration_ms=duration_ms,
        request_data=sanitized_request_data if sanitize_sensitive else request_data,
        response_data=sanitized_response_data if sanitize_sensitive else response_data
    )

# ==================== AUTHENTICATION VIEWS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user with activity logging"""
    start_time = time.time()
    
    try:
        print(f"\n{'='*50}")
        print(f"REGISTRATION REQUEST RECEIVED")
        print(f"{'='*50}")
        print(f"Submitted data: {request.data}\n")
        
        # Extract data
        phone_number = request.data.get('phone_number', '').strip()
        email = request.data.get('email', '').strip()
        full_name = request.data.get('full_name', '').strip()
        department = request.data.get('department').strip()
        role = request.data.get('role', 'employee').strip().lower()
        requesting_user = request.user if request.user.is_authenticated else None
        
        # Validate required fields
        if not phone_number:
            error_msg = "Phone number is required."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: {error_msg}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not email:
            error_msg = "Email address is required."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: {error_msg}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not full_name:
            error_msg = "Full name is required."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: {error_msg}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Validate phone number format
        phone_error = is_valid_phone(phone_number)
        if phone_error:
            print(f"ERROR: {phone_error}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: Invalid phone number format",
                request_data=request.data
            )
            return Response({"error": phone_error}, status=400)
        
        # Validate email format
        email_error = is_valid_email(email)
        if email_error:
            print(f"ERROR: {email_error}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: Invalid email format",
                request_data=request.data
            )
            return Response({"error": email_error}, status=400)
        
        # Check role-based permissions
        if role not in ['admin', 'manager', 'employee', 'analyst']:
            error_msg = f"Invalid role '{role}'. Must be one of: admin, manager, employee, analyst"
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: {error_msg}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Department validation based on role
        if role == 'employee':
            if not department:
                error_msg = "Department is required for employee users."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: {error_msg}",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            # Validate department exists and is active
            try:
                dept_obj = Department.objects.get(id=department, status='active')
            except Department.DoesNotExist:
                error_msg = "Invalid or inactive department selected."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: {error_msg}",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
        
        elif role in ['admin', 'manager', 'analyst']:
            # Admin and HR don't require department
            department = None
        
        # Role-based permission checks
        if role != 'employee' and not requesting_user:
            error_msg = "Only admin or Manager can create users with roles other than 'employee'."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=None,
                request=request,
                status_code='400',
                description=f"Registration failed: {error_msg}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if requesting_user:
            if role == 'admin' and not requesting_user.is_admin:
                error_msg = "Only admin can create admin users."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: User {requesting_user.email} attempted to create admin user",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=403)
            if role == 'manager' and not requesting_user.is_admin:
                error_msg = "Only admin can create Manager users."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: User {requesting_user.email} attempted to create manager user",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=403)
            if role == 'analyst' and not (requesting_user.is_admin or requesting_user.is_manager):
                error_msg = "Only admin or Manager can create analyst users."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: User {requesting_user.email} attempted to create analyst user",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=403)
        
        # Check for existing users
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            error_msg = "A user with this phone number already exists."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: Duplicate phone number",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if CustomUser.objects.filter(email=email).exists():
            error_msg = "A user with this email already exists."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: Duplicate email",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Handle password
        if requesting_user:
            password = generate_secure_password()
            if not password:
                error_msg = "Failed to generate secure password. Please try again."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=requesting_user,
                    request=request,
                    status_code='500',
                    description=f"Registration failed: Password generation error",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=500)
        else:
            password = request.data.get('password', '').strip()
            confirm_password = request.data.get('confirm_password', '').strip()
            
            if not password:
                error_msg = "Password is required."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=None,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: Password required",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if not confirm_password:
                error_msg = "Password confirmation is required."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=None,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: Password confirmation required",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if password != confirm_password:
                error_msg = "Passwords do not match."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_registration',
                    user=None,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: Passwords don't match",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            password_error = is_valid_password(password)
            if password_error:
                print(f"ERROR: {password_error}")
                log_user_activity(
                    activity_type='user_registration',
                    user=None,
                    request=request,
                    status_code='400',
                    description=f"Registration failed: Weak password",
                    request_data=request.data
                )
                return Response({"error": password_error}, status=400)
        
        # Generate work mail address
        try:
            work_mail_address = CustomUser.objects.generate_work_mail(full_name, role)
            print(f"Generated work email: {work_mail_address}")
        except Exception as e:
            error_msg = f"Failed to generate work email address: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='500',
                description=f"Registration failed: Work email generation error",
                request_data=request.data
            )
            return Response({"error": "Failed to generate work email address. Please try again."}, status=500)
        
        # Create user with proper parameters based on role
        try:
            if role == 'employee':
                user = CustomUser.objects.create_user(
                    phone_number=phone_number,
                    email=email,
                    full_name=full_name,
                    department=department,  # Pass department ID for employee
                    role=role,
                    work_mail_address=work_mail_address,
                    password=password,
                    created_by=requesting_user,
                    status='approved' if requesting_user else 'pending',
                    availability_status='active' if requesting_user else 'inactive'
                )
            else:  # admin or hr
                user = CustomUser.objects.create_user(
                    phone_number=phone_number,
                    email=email,
                    full_name=full_name,
                    department=None,
                    role=role,
                    work_mail_address=work_mail_address,
                    password=password,
                    created_by=requesting_user,
                    status='approved' if requesting_user else 'pending',
                    availability_status='active' if requesting_user else 'inactive'
                )
            
            print(f"SUCCESS: User created with ID: {user.id}")
            print(f"User details: {user.full_name} - {user.work_mail_address}")
            
        except IntegrityError as e:
            error_msg = f"Database integrity error: A user with this information already exists."
            print(f"ERROR: {error_msg}")
            print(f"IntegrityError details: {str(e)}")
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='400',
                description=f"Registration failed: Integrity error - duplicate user",
                request_data=request.data
            )
            return Response({"error": "A user with this information already exists."}, status=400)
        except Exception as e:
            error_msg = f"Error creating user: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='500',
                description=f"Registration failed: User creation error",
                request_data=request.data
            )
            return Response({"error": "Failed to create user account. Please try again."}, status=500)
        
        # Send email with credentials
        try:
            # Get department info for email
            dept_info = ""
            if role == 'employee':
                dept_info = f"Department: {user.department.name}"
            else:
                dept_info = "Department: N/A (Admin/Manager/Analyst)"
            
            subject = "Welcome to CodePulse Africa Ltd"
            message = f"""
        Hello {full_name},

        Your account has been successfully created in the Intelligent Workforce Performance Monitoring & Analyticcs System.

        Account Details:
        - Full Name: {full_name}
        - Role: {role.title()}
            - {dept_info}
            - Work Email: {work_mail_address}
            - Personal Email: {email}
            - Password: {password}

            Please use your work email ({work_mail_address}) to log in to the system.

            Important: This is a system-generated password. For security reasons, please change it after your first login.

            If you have any questions, please contact our support team.

            Best regards,
            CodePulse Africa Ltd Team
                        """
                        
            send_mail(
                            subject=subject,
                            message=message,
                            from_email="no-reply@codepulse_africa_ltd.com",
                            recipient_list=[email],
                            fail_silently=False,
                        )
            print(f"SUCCESS: Email sent to {email}")
            
            success_msg = "User registered successfully. Please check your email for login credentials."
            print(f"SUCCESS: {success_msg}")
            print(f"{'='*50}\n")
            
            # Calculate duration and log successful registration
            duration_ms = int((time.time() - start_time) * 1000)
            created_by = f"by {requesting_user.email}" if requesting_user else "self-registration"
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='201',
                description=f"User {user.email} ({user.role}) registered successfully {created_by}",
                related_user_id=user.id,
                duration_ms=duration_ms,
                request_data=request.data,
                response_data={'work_mail_address': work_mail_address, 'role': role}
            )
            
            # Also log user creation activity
            if requesting_user:
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='201',
                    description=f"User {requesting_user.email} created new user {user.email} ({user.role})",
                    related_user_id=user.id,
                    duration_ms=duration_ms
                )
                    
            return Response({
                        "message": success_msg,
                        "work_mail_address": work_mail_address,
                        "status": user.status,
                        "role": user.role
                    }, status=201)
                    
        except Exception as e:
            error_msg = f"Warning: User created but email failed to send: {str(e)}"
            print(f"WARNING: {error_msg}")
            
            # User created successfully but email failed - still return success
            success_msg = "User registered successfully. Please check your email for login credentials (email delivery may be delayed)."
            print(f"SUCCESS: {success_msg}")
            print(f"{'='*50}\n")
            
            # Calculate duration and log success (with email warning)
            duration_ms = int((time.time() - start_time) * 1000)
            created_by = f"by {requesting_user.email}" if requesting_user else "self-registration"
            log_user_activity(
                activity_type='user_registration',
                user=requesting_user,
                request=request,
                status_code='201',
                description=f"User {user.email} registered {created_by} but email delivery failed",
                related_user_id=user.id,
                duration_ms=duration_ms,
                request_data=request.data,
                response_data={'work_mail_address': work_mail_address, 'role': role, 'email_warning': True}
            )
            
            if requesting_user:
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='201',
                    description=f"User {requesting_user.email} created new user {user.email} (email delivery failed)",
                    related_user_id=user.id,
                    duration_ms=duration_ms
                )
                    
            return Response({
                        "message": success_msg,
                        "work_mail_address": work_mail_address,
                        "status": user.status,
                        "role": user.role,
                        "warning": "Email delivery may be delayed"
                    }, status=201)

    except Exception as e:
            error_msg = f"Unexpected error during registration: {str(e)}"
            print(f"CRITICAL ERROR: {error_msg}")
            print(traceback.format_exc())
            log_user_activity(
                activity_type='user_registration',
                user=request.user if request.user.is_authenticated else None,
                request=request,
                status_code='500',
                description=f"Registration failed: Unexpected error",
                request_data=request.data
            )
            return Response({
                "error": "An unexpected error occurred during registration. Please try again or contact support."
            }, status=500)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_user(request):
    """Login user with work mail and activity logging"""
    start_time = time.time()
    
    try:
        print(f"\n{'='*50}")
        print(f"LOGIN REQUEST RECEIVED")
        print(f"{'='*50}")
        
        identifier = request.data.get('work_mail_address', '').strip()
        password = request.data.get('password', '').strip()
        
        print(f"Login attempt with identifier: {identifier}")
        
        if not identifier:
            error_msg = "Work email is required."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_login',
                user=None,
                request=request,
                status_code='400',
                description="Login failed: Work email required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        if not password:
            error_msg = "Password is required."
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_login',
                user=None,
                request=request,
                status_code='400',
                description="Login failed: Password required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        user = CustomUser.objects.filter(work_mail_address=identifier).first()
        
        if not user:
            error_msg = "Invalid credentials. Please check your email and password."
            print(f"ERROR: User not found with identifier: {identifier}")
            log_user_activity(
                activity_type='user_login',
                user=None,
                request=request,
                status_code='401',
                description=f"Login failed: User not found with identifier {identifier}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        print(f"User found: {user.full_name} ({user.email})")
        
        if not check_password(password, user.password):
            error_msg = "Invalid credentials. Please check your email and password."
            print(f"ERROR: Invalid password for user: {user.email}")
            log_user_activity(
                activity_type='user_login',
                user=user,
                request=request,
                status_code='401',
                description=f"Login failed: Invalid password for user {user.email}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        if not user.is_active:
            error_msg = "Your account is inactive. Please contact the administrator."
            print(f"ERROR: Inactive account: {user.email}")
            log_user_activity(
                activity_type='user_login',
                user=user,
                request=request,
                status_code='401',
                description=f"Login failed: Account inactive for user {user.email}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        if user.status == 'pending':
            error_msg = "Your account is pending approval. Please wait for administrator approval."
            print(f"ERROR: Pending account: {user.email}")
            log_user_activity(
                activity_type='user_login',
                user=user,
                request=request,
                status_code='401',
                description=f"Login failed: Account pending approval for user {user.email}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        if user.status == 'rejected':
            error_msg = "Your account has been rejected. Please contact the administrator for more information."
            print(f"ERROR: Rejected account: {user.email}")
            log_user_activity(
                activity_type='user_login',
                user=user,
                request=request,
                status_code='401',
                description=f"Login failed: Account rejected for user {user.email}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=401)
        
        try:
            refresh = RefreshToken.for_user(user)
            print(f"SUCCESS: Login successful for user: {user.email}")
        except Exception as e:
            error_msg = f"Error generating authentication token: {str(e)}"
            print(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='user_login',
                user=user,
                request=request,
                status_code='500',
                description=f"Login failed: Token generation error for user {user.email}",
                request_data=request.data
            )
            return Response({"error": "Authentication error. Please try again."}, status=500)
        
        serializer = CustomUserSerializer(user)
        
        # Calculate duration and log successful login
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='user_login',
            user=user,
            request=request,
            status_code='200',
            description=f"User {user.email} logged in successfully",
            duration_ms=duration_ms,
            request_data=request.data
        )
        
        print(f"{'='*50}\n")
        
        return Response({
            **serializer.data,
            "token": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "message": "Login successful."
        }, status=200)
        
    except Exception as e:
        error_msg = f"Unexpected error during login: {str(e)}"
        print(f"CRITICAL ERROR: {error_msg}")
        print(traceback.format_exc())
        log_user_activity(
            activity_type='user_login',
            user=None,
            request=request,
            status_code='500',
            description="Login failed: Unexpected error",
            request_data=request.data
        )
        return Response({
            "error": "An unexpected error occurred during login. Please try again."
        }, status=500)

# ==================== PASSWORD MANAGEMENT ====================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_or_deactivate_user(request, user_id):
    """Delete or deactivate user based on role with activity logging"""
    start_time = time.time()
    
    try:
        target_user = CustomUser.objects.get(id=user_id)
        current_user = request.user
        
        if not current_user.is_admin:
            if current_user.is_manager and target_user.role == 'admin':
                log_user_activity(
                    activity_type='user_delete',
                    user=current_user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: Manager {current_user.email} attempted to delete admin user {target_user.email}",
                    related_user_id=target_user.id
                )
                return Response({"error": "HR cannot delete admin users."}, status=403)
            if current_user.is_mentor and target_user.role in ['admin', 'manager']:
                log_user_activity(
                    activity_type='user_delete',
                    user=current_user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: Mentor {current_user.email} attempted to delete admin/manager user {target_user.email}",
                    related_user_id=target_user.id
                )
                return Response({"error": "Mentors cannot delete admin or Manager users."}, status=403)
        
        if current_user.is_admin:
            # Store user info before deletion
            user_info = {
                'id': target_user.id,
                'email': target_user.email,
                'full_name': target_user.full_name,
                'role': target_user.role
            }
            target_user.delete()
            action = "deleted"
            action_type = 'user_delete'
        else:
            target_user.is_active = False
            target_user.availability_status = 'inactive'
            target_user.save()
            action = "deactivated"
            action_type = 'user_deactivate'
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type=action_type,
            user=current_user,
            request=request,
            status_code='200',
            description=f"User {current_user.email} {action} user {user_id} ({target_user.email if action == 'deactivated' else user_info['email']})",
            related_user_id=target_user.id if action == 'deactivated' else None,
            duration_ms=duration_ms,
            response_data={'action': action, 'user': user_info} if action == 'deleted' else None
        )
        
        return Response({"message": f"User {action} successfully."}, status=200)
        
    except ObjectDoesNotExist:
        log_user_activity(
            activity_type='user_delete',
            user=request.user,
            request=request,
            status_code='404',
            description=f"User {request.user.email} attempted to delete non-existent user ID: {user_id}",
            related_user_id=user_id
        )
        return Response({"error": "User not found."}, status=404)
    except Exception as e:
        log_user_activity(
            activity_type='user_delete',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error deleting user {user_id}: {str(e)}",
            related_user_id=user_id
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    """Update user information with department validation and activity logging"""
    
    print(f"\nSubmitted user data to update: {request.data}\n")
    start_time = time.time()
    
    if not request.user.is_admin and not request.user.is_manager:
        log_user_activity(
            activity_type='user_update',
            user=request.user,
            request=request,
            status_code='403',
            description=f"Permission denied: User {request.user.email} attempted to update user information"
        )
        return Response({"error": "You are not authorized to update user information."}, status=403)
    
    try:
        target_user = CustomUser.objects.get(id=user_id)
        
        # Store the original values for logging
        original_values = {
            'phone_number': target_user.phone_number,
            'email': target_user.email,
            'full_name': target_user.full_name,
            'department': target_user.department.id if target_user.department else None,
            'role': target_user.role,
            'status': target_user.status,
            'availability_status': target_user.availability_status
        }
        original_status = target_user.status
        original_is_active = target_user.is_active
        
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        department = request.data.get('department')
        role = request.data.get('role')
        status_val = request.data.get('status')
        availability_status = request.data.get('availability_status')
        
        # Check if user can update departments
        if ('department' in request.data):
            if not request.user.can_update_departments():
                print("ERROR: Only admin and Manager users can update departments.")
                log_user_activity(
                    activity_type='user_update',
                    user=request.user,
                    request=request,
                    status_code='403',
                    description=f"Permission denied: User {request.user.email} attempted to update departments",
                    related_user_id=target_user.id,
                    request_data=request.data
                )
                return Response({
                    "error": "Only admin and Manager users can update departments."
                }, status=403)
        
        # Prevent changing work mail address
        if 'work_mail_address' in request.data:
            print("ERROR: Work mail address cannot be changed.")
            log_user_activity(
                activity_type='user_update',
                user=request.user,
                request=request,
                status_code='400',
                description=f"Invalid update attempt: Work mail address change not allowed",
                related_user_id=target_user.id,
                request_data=request.data
            )
            return Response({"error": "Work mail address cannot be changed."}, status=400)
        
        # Validate uniqueness
        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exclude(id=user_id).exists():
            print("ERROR: A user with this phone number already exists.")
            log_user_activity(
                activity_type='user_update',
                user=request.user,
                request=request,
                status_code='400',
                description=f"Update failed: Duplicate phone number",
                related_user_id=target_user.id,
                request_data=request.data
            )
            return Response({"error": "A user with this phone number already exists."}, status=400)
        
        if email and CustomUser.objects.filter(email=email).exclude(id=user_id).exists():
            print("ERROR: A user with this email already exists.")
            log_user_activity(
                activity_type='user_update',
                user=request.user,
                request=request,
                status_code='400',
                description=f"Update failed: Duplicate email",
                related_user_id=target_user.id,
                request_data=request.data
            )
            return Response({"error": "A user with this email already exists."}, status=400)
        
        # Role-based department validation
        if role:
            # Role-based department validation
            if role == 'employee':
                # employee must have exactly one department
                if department is None:
                    print("ERROR: employee users must have a department assigned.")
                    log_user_activity(
                        activity_type='user_update',
                        user=request.user,
                        request=request,
                        status_code='400',
                        description=f"Update failed: employee must have department",
                        related_user_id=target_user.id,
                        request_data=request.data
                    )
                    return Response({
                        "error": "employee users must have a department assigned."
                    }, status=400)
                
                try:
                    dept_obj = Department.objects.get(id=department, status='active')
                    target_user.department = dept_obj
                except Department.DoesNotExist:
                    print("ERROR: Invalid or inactive department selected.")
                    log_user_activity(
                        activity_type='user_update',
                        user=request.user,
                        request=request,
                        status_code='400',
                        description=f"Update failed: Invalid department",
                        related_user_id=target_user.id,
                        request_data=request.data
                    )
                    return Response({
                        "error": "Invalid or inactive department selected."
                    }, status=400)
            
            elif role in ['admin', 'manager', 'analyst']:
                # Admin/HR don't have departments
                target_user.department = None

            target_user.role = role
        
        # If department is being updated without role change
        elif 'department' in request.data and target_user.role == 'employee':
            if department is None:
                print("ERROR: employee users must have a department assigned.")
                log_user_activity(
                    activity_type='user_update',
                    user=request.user,
                    request=request,
                    status_code='400',
                    description=f"Update failed: employee must have department",
                    related_user_id=target_user.id,
                    request_data=request.data
                )
                return Response({
                    "error": "employee users must have a department assigned."
                }, status=400)
            
            try:
                dept_obj = Department.objects.get(id=department, status='active')
                target_user.department = dept_obj
            except Department.DoesNotExist:
                print("ERROR: Invalid or inactive department selected.")
                log_user_activity(
                    activity_type='user_update',
                    user=request.user,
                    request=request,
                    status_code='400',
                    description=f"Update failed: Invalid department",
                    related_user_id=target_user.id,
                    request_data=request.data
                )
                return Response({
                    "error": "Invalid or inactive department selected."
                }, status=400)
        
        # Update other fields
        if phone_number:
            target_user.phone_number = phone_number
        if email:
            target_user.email = email
        if full_name:
            target_user.full_name = full_name
        if status_val:
            target_user.status = status_val
        if availability_status:
            target_user.availability_status = availability_status
        
        # Save with skip_validation to avoid full_clean() issues
        target_user.save(skip_validation=True)
        print(f"SUCCESS: User {target_user.id} saved with role={target_user.role}, department={target_user.department}")
        
        # Check if status changed from inactive to active and send email
        status_changed_to_active = (
            original_status in ['pending', 'rejected'] and 
            target_user.status == 'approved'
        )
        
        if status_changed_to_active:
            print(f"Status changed from '{original_status}' to 'approved' - sending activation email")
            
            try:
                # Get department info for email
                dept_info = ""
                if target_user.role == 'employee' and target_user.department:
                    dept_info = f"\n- Department: {target_user.department.name}"

                subject = "Account Activated - CodePulse Africa Ltd"
                message = f"""
Hello {target_user.full_name},

Great news! Your account has been approved and activated in the Intelligent Workforce Performance Monitoring & Analics System.

Account Details:
- Full Name: {target_user.full_name}
- Role: {target_user.role.title()}
- Work Email: {target_user.work_mail_address}
- Personal Email: {target_user.email}{dept_info}

You can now log in to the system using your work email address ({target_user.work_mail_address}) and your password.

If you have forgotten your password, you can reset it using the "Forgot Password" link on the login page.

Access the system at: [Your System URL]

If you have any questions or need assistance, please don't hesitate to contact our support team.

Welcome aboard!

Best regards,
CodePulse Africa Ltd Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email="no-reply@codepulse_africa_ltd.com",
                    recipient_list=[target_user.email],
                    fail_silently=False,
                )
                
                print(f"SUCCESS: Account activation email sent to {target_user.email}")
                
            except Exception as e:
                error_msg = f"Warning: User updated but activation email failed to send: {str(e)}"
                print(f"WARNING: {error_msg}")
                # Continue even if email fails - user is still activated
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare changed fields for logging
        changed_fields = []
        if phone_number and phone_number != original_values['phone_number']:
            changed_fields.append(f"phone: {original_values['phone_number']} → {phone_number}")
        if email and email != original_values['email']:
            changed_fields.append(f"email: {original_values['email']} → {email}")
        if full_name and full_name != original_values['full_name']:
            changed_fields.append(f"name: {original_values['full_name']} → {full_name}")
        if role and role != original_values['role']:
            changed_fields.append(f"role: {original_values['role']} → {role}")
        if status_val and status_val != original_values['status']:
            changed_fields.append(f"status: {original_values['status']} → {status_val}")
        if availability_status and availability_status != original_values['availability_status']:
            changed_fields.append(f"availability: {original_values['availability_status']} → {availability_status}")
        
        # Log the update activity
        description = f"User {request.user.email} updated user {target_user.email}"
        if changed_fields:
            description += f": {', '.join(changed_fields)}"
        
        log_user_activity(
            activity_type='user_update',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_user_id=target_user.id,
            duration_ms=duration_ms,
            request_data=request.data,
            response_data={'changed_fields': changed_fields, 'status_changed': status_changed_to_active}
        )
        
        serializer = CustomUserSerializer(target_user)
        print(f"SUCCESS: User {target_user.id} updated successfully")
        
        response_message = "User updated successfully."
        if status_changed_to_active:
            response_message += " Activation email has been sent to the user."
        
        return Response({
            "message": response_message,
            "user": serializer.data,
            "email_sent": status_changed_to_active
        }, status=200)
        
    except ObjectDoesNotExist:
        print("ERROR: User with the given ID does not exist.")
        log_user_activity(
            activity_type='user_update',
            user=request.user,
            request=request,
            status_code='404',
            description=f"Update failed: User ID {user_id} not found",
            related_user_id=user_id,
            request_data=request.data
        )
        return Response({"error": "User with the given ID does not exist."}, status=404)
    except ValidationError as ve:
        print(f"ERROR: Validation error: {str(ve)}")
        log_user_activity(
            activity_type='user_update',
            user=request.user,
            request=request,
            status_code='400',
            description=f"Update failed: Validation error",
            related_user_id=user_id,
            request_data=request.data,
            response_data={'validation_error': str(ve)}
        )
        return Response({"error": f"Validation error: {str(ve)}"}, status=400)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())
        log_user_activity(
            activity_type='user_update',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Update failed: Unexpected error",
            related_user_id=user_id,
            request_data=request.data
        )
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)    
 
 
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_users(request):
    """List all users with proper permissions and activity logging"""
    start_time = time.time()
    
    if not request.user.is_admin and not request.user.is_manager:
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='403',
            description=f"Permission denied: User {request.user.email} attempted to view all users"
        )
        return Response({"error": "You are not authorized to view all users."}, status=403)
    
    try:
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User {request.user.email} viewed all users list ({users.count()} users)",
            duration_ms=duration_ms
        )
        
        return Response({"users": serializer.data}, status=200)
    except Exception as e:
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing all users: {str(e)}"
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_employees(request):
    """List all employees with proper permissions and activity logging"""
    start_time = time.time()
    
    if not request.user.is_admin and not request.user.is_manager:
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='403',
            description=f"Permission denied: User {request.user.email} attempted to view all employees"
        )
        return Response({"error": "You are not authorized to view all employees."}, status=403)

    try:
        employees = CustomUser.objects.filter(role='employee')
        serializer = CustomUserSerializer(employees, many=True)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User {request.user.email} viewed all employees list ({employees.count()} employees)",
            duration_ms=duration_ms
        )
        
        return Response({"users": serializer.data}, status=200)
    except Exception as e:
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing all employees: {str(e)}"
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_id(request, user_id):
    """Get user by ID with activity logging"""
    start_time = time.time()
    
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Check permissions - users can only view their own profile unless admin/HR/manager
        if not request.user.is_admin and not request.user.is_manager and request.user.id != user_id:
            log_user_activity(
                activity_type='user_view',
                user=request.user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {request.user.email} attempted to view user {user.email}",
                related_user_id=user_id
            )
            return Response({"error": "You are not authorized to access this user."}, status=403)
        
        serializer = CustomUserSerializer(user)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        viewed_by = "self" if request.user.id == user_id else f"by {request.user.email}"
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User {user.email} viewed {viewed_by}",
            related_user_id=user_id,
            duration_ms=duration_ms
        )
        
        return Response(serializer.data, status=200)
    except ObjectDoesNotExist:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='404',
            description=f"User view failed: User ID {user_id} not found",
            related_user_id=user_id
        )
        return Response({"error": "User with the given ID does not exist."}, status=404)
    except Exception as e:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing user {user_id}: {str(e)}",
            related_user_id=user_id
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_email(request):
    """Get user by email with activity logging"""
    start_time = time.time()
    
    email = request.query_params.get('email')
    
    if not email:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='400',
            description="User search failed: Email parameter missing"
        )
        return Response({"error": "Email is required to search for a user."}, status=400)
    
    try:
        user = CustomUser.objects.get(email=email)
        
        # Check permissions - users can only view their own profile unless admin/HR
        if not request.user.is_admin and not request.user.is_manager and request.user.email != email:
            log_user_activity(
                activity_type='user_view',
                user=request.user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {request.user.email} attempted to view user {email}",
                related_user_id=user.id
            )
            return Response({"error": "You are not authorized to access this user."}, status=403)
        
        serializer = CustomUserSerializer(user)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        viewed_by = "self" if request.user.email == email else f"by {request.user.email}"
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User {email} viewed {viewed_by}",
            related_user_id=user.id,
            duration_ms=duration_ms
        )
        
        return Response(serializer.data, status=200)
    except ObjectDoesNotExist:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='404',
            description=f"User search failed: Email {email} not found"
        )
        return Response({"error": "User with the given email does not exist."}, status=404)
    except Exception as e:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error searching user by email {email}: {str(e)}"
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_phone(request):
    """Get user by phone number with activity logging"""
    start_time = time.time()
    
    phone_number = request.query_params.get('phone_number')
    
    if not phone_number:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='400',
            description="User search failed: Phone number parameter missing"
        )
        return Response({"error": "Phone number is required to search for a user."}, status=400)
    
    try:
        user = CustomUser.objects.get(phone_number=phone_number)
        
        # Check permissions - users can only view their own profile unless admin/HR
        if not request.user.is_admin and not request.user.is_manager and request.user.phone_number != phone_number:
            log_user_activity(
                activity_type='user_view',
                user=request.user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {request.user.email} attempted to view user with phone {phone_number}",
                related_user_id=user.id
            )
            return Response({"error": "You are not authorized to access this user."}, status=403)
        
        serializer = CustomUserSerializer(user)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        viewed_by = "self" if request.user.phone_number == phone_number else f"by {request.user.email}"
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User with phone {phone_number} viewed {viewed_by}",
            related_user_id=user.id,
            duration_ms=duration_ms
        )
        
        return Response(serializer.data, status=200)
    except ObjectDoesNotExist:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='404',
            description=f"User search failed: Phone number {phone_number} not found"
        )
        return Response({"error": "User with the given phone number does not exist."}, status=404)
    except Exception as e:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error searching user by phone {phone_number}: {str(e)}"
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def activate_user(request, user_id):
    """Activate user account with activity logging"""
    start_time = time.time()
    
    try:
        # Check permissions
        if not request.user.is_admin and not request.user.is_manager:
            log_user_activity(
                activity_type='user_activate',
                user=request.user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {request.user.email} attempted to activate user"
            )
            return Response({"error": "You are not authorized to activate users."}, status=403)
        
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Check if the user is already active
        if user.status == 'approved':
            log_user_activity(
                activity_type='user_activate',
                user=request.user,
                request=request,
                status_code='400',
                description=f"User activation failed: User {user.email} already active",
                related_user_id=user_id
            )
            return Response({"message": "This user account is already activated."}, status=400)
        
        # Store original status for logging
        original_status = user.status
        
        # Activate the user
        user.status = 'approved'
        user.is_active = True
        user.availability_status = 'active'
        user.save()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Send notification email
        try:
            send_mail(
                subject="Account Activated - CodePulse Africa Ltd",
                message=f"Your account has been activated. You can now log in using your work email: {user.work_mail_address}",
                from_email="no-reply@codepulse_africa_ltd.com",
                recipient_list=[user.email],
            )
            email_sent = True
        except Exception as e:
            email_sent = False
        
        # Log the activation
        description = f"User {request.user.email} activated user {user.email} (status: {original_status} → approved)"
        log_user_activity(
            activity_type='user_activate',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_user_id=user_id,
            duration_ms=duration_ms,
            response_data={'original_status': original_status, 'email_sent': email_sent}
        )
        
        return Response({"message": "User activated successfully."}, status=200)
        
    except Exception as e:
        log_user_activity(
            activity_type='user_activate',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error activating user {user_id}: {str(e)}",
            related_user_id=user_id
        )
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def deactivate_user(request, user_id):
    """Deactivate user account with activity logging"""
    start_time = time.time()
    
    try:
        # Check permissions
        if not request.user.is_admin and not request.user.is_manager:
            log_user_activity(
                activity_type='user_deactivate',
                user=request.user,
                request=request,
                status_code='403',
                description=f"Permission denied: User {request.user.email} attempted to deactivate user"
            )
            return Response({"error": "You are not authorized to deactivate users."}, status=403)
        
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Check if the user is already deactivated
        if user.status != 'approved':
            log_user_activity(
                activity_type='user_deactivate',
                user=request.user,
                request=request,
                status_code='400',
                description=f"User deactivation failed: User {user.email} already deactivated (status: {user.status})",
                related_user_id=user_id
            )
            return Response({"message": "This user account is already deactivated."}, status=400)
        
        # Store original status for logging
        original_status = user.status
        
        # Deactivate the user
        user.status = 'rejected'
        user.is_active = False
        user.availability_status = 'inactive'
        user.save()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log the deactivation
        description = f"User {request.user.email} deactivated user {user.email} (status: {original_status} → rejected)"
        log_user_activity(
            activity_type='user_deactivate',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_user_id=user_id,
            duration_ms=duration_ms,
            response_data={'original_status': original_status}
        )
        
        return Response({"message": "User deactivated successfully."}, status=200)
        
    except Exception as e:
        log_user_activity(
            activity_type='user_deactivate',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error deactivating user {user_id}: {str(e)}",
            related_user_id=user_id
        )
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_status(request, user_id):
    """Admin/Manager can update user status with activity logging"""
    start_time = time.time()
    
    if not request.user.is_admin and not request.user.is_manager:
        log_user_activity(
            activity_type='user_status_change',
            user=request.user,
            request=request,
            status_code='403',
            description=f"Permission denied: User {request.user.email} attempted to update user status"
        )
        return Response({"error": "You are not authorized to update user status."}, status=403)
    
    try:
        target_user = CustomUser.objects.get(id=user_id)
        new_status = request.data.get('status')
        
        # Store original status for logging
        original_status = target_user.status
        original_is_active = target_user.is_active
        
        if new_status not in ['pending', 'approved', 'rejected']:
            log_user_activity(
                activity_type='user_status_change',
                user=request.user,
                request=request,
                status_code='400',
                description=f"Status update failed: Invalid status value '{new_status}'",
                related_user_id=user_id,
                request_data=request.data
            )
            return Response({"error": "Invalid status value."}, status=400)
        
        target_user.status = new_status
        
        if new_status == 'approved':
            target_user.availability_status = 'active'
            target_user.is_active = True
        else:
            target_user.availability_status = 'inactive'
            target_user.is_active = False
        
        target_user.save()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Send notification email for approval
        email_sent = False
        if new_status == 'approved' and original_status != 'approved':
            try:
                send_mail(
                    subject="Account Approved - CodePulse Africa Ltd",
                    message=f"Your account has been approved. You can now log in using your work email: {target_user.work_mail_address}",
                    from_email="no-reply@codepulse_africa_ltd.com",
                    recipient_list=[target_user.email],
                )
                email_sent = True
            except Exception as e:
                email_sent = False
        
        # Log the status change
        description = f"User {request.user.email} changed status of user {target_user.email} from {original_status} to {new_status}"
        log_user_activity(
            activity_type='user_status_change',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            related_user_id=user_id,
            duration_ms=duration_ms,
            request_data=request.data,
            response_data={
                'original_status': original_status,
                'new_status': new_status,
                'email_sent': email_sent
            }
        )
        
        serializer = CustomUserSerializer(target_user)
        return Response({
            "message": f"User status updated to {new_status}.",
            "user": serializer.data,
            "email_sent": email_sent
        }, status=200)
        
    except ObjectDoesNotExist:
        log_user_activity(
            activity_type='user_status_change',
            user=request.user,
            request=request,
            status_code='404',
            description=f"Status update failed: User ID {user_id} not found",
            related_user_id=user_id,
            request_data=request.data
        )
        return Response({"error": "User not found."}, status=404)
    except Exception as e:
        log_user_activity(
            activity_type='user_status_change',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error updating user status: {str(e)}",
            related_user_id=user_id,
            request_data=request.data
        )
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

# ==================== PROFILE MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get logged-in user's information with activity logging"""
    start_time = time.time()
    
    try:
        serializer = CustomUserSerializer(request.user)
        
        # Calculate duration and log activity
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='200',
            description=f"User {request.user.email} viewed their own profile",
            related_user_id=request.user.id,
            duration_ms=duration_ms
        )
        
        print("\n user profile: ", serializer.data, "\n")
        return Response(serializer.data, status=200)
    except Exception as e:
        log_user_activity(
            activity_type='user_view',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing own profile: {str(e)}"
        )
        return Response({"error": f"An error occurred: {str(e)}"}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user's own profile (cannot change departments) with activity logging"""
    start_time = time.time()
    
    user = request.user
    
    if 'work_mail_address' in request.data:
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='400',
            description="Profile update failed: Work mail address change attempted",
            request_data=request.data
        )
        return Response({"error": "Work mail address cannot be changed."}, status=400)
    
    if 'role' in request.data:
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='400',
            description="Profile update failed: Role change attempted",
            request_data=request.data
        )
        return Response({"error": "Role cannot be changed."}, status=400)
    
    if 'department' in request.data:
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='403',
            description="Profile update failed: Department change attempted",
            request_data=request.data
        )
        return Response({
            "error": "You cannot change your department(s). Please contact admin or HR."
        }, status=403)
    
    # Store original values for logging
    original_values = {
        'phone_number': user.phone_number,
        'email': user.email,
        'full_name': user.full_name,
        'availability_status': user.availability_status
    }
    
    allowed_fields = ['phone_number', 'email', 'full_name', 'availability_status']
    
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    
    try:
        if 'phone_number' in request.data:
            if CustomUser.objects.filter(phone_number=request.data['phone_number']).exclude(id=user.id).exists():
                log_user_activity(
                    activity_type='profile_update',
                    user=user,
                    request=request,
                    status_code='400',
                    description="Profile update failed: Duplicate phone number",
                    request_data=request.data
                )
                return Response({"error": "Phone number already exists."}, status=400)
        
        if 'email' in request.data:
            if CustomUser.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
                log_user_activity(
                    activity_type='profile_update',
                    user=user,
                    request=request,
                    status_code='400',
                    description="Profile update failed: Duplicate email",
                    request_data=request.data
                )
                return Response({"error": "Email already exists."}, status=400)
        
        user.save()
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Prepare changed fields for logging
        changed_fields = []
        if 'phone_number' in request.data and request.data['phone_number'] != original_values['phone_number']:
            changed_fields.append(f"phone: {original_values['phone_number']} → {request.data['phone_number']}")
        if 'email' in request.data and request.data['email'] != original_values['email']:
            changed_fields.append(f"email: {original_values['email']} → {request.data['email']}")
        if 'full_name' in request.data and request.data['full_name'] != original_values['full_name']:
            changed_fields.append(f"name: {original_values['full_name']} → {request.data['full_name']}")
        if 'availability_status' in request.data and request.data['availability_status'] != original_values['availability_status']:
            changed_fields.append(f"availability: {original_values['availability_status']} → {request.data['availability_status']}")
        
        # Log the profile update
        description = f"User {user.email} updated their profile"
        if changed_fields:
            description += f": {', '.join(changed_fields)}"
        
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='200',
            description=description,
            duration_ms=duration_ms,
            request_data=request.data,
            response_data={'changed_fields': changed_fields}
        )
        
        serializer = CustomUserSerializer(user)
        return Response({
            "message": "Profile updated successfully.",
            "user": serializer.data
        }, status=200)
    except IntegrityError:
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='400',
            description="Profile update failed: Integrity error",
            request_data=request.data
        )
        return Response({"error": "Update failed due to data conflict."}, status=400)
    except Exception as e:
        log_user_activity(
            activity_type='profile_update',
            user=user,
            request=request,
            status_code='500',
            description=f"Profile update failed: {str(e)}",
            request_data=request.data
        )
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


# ==================== CONTACT US ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def contact_us(request):
    """Handle contact us form submission with activity logging"""
    start_time = time.time()
    
    logger.info("Received contact request with data: %s", request.data)
    
    serializer = ContactUsSerializer(data=request.data)
    
    if serializer.is_valid():
        names = serializer.validated_data['names']
        email = serializer.validated_data['email']
        subject = serializer.validated_data['subject']
        description = serializer.validated_data['description']
        
        # Check for empty fields
        if not names.strip():
            logger.error("Name field is empty.")
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='400',
                description="Contact form submission failed: Name field empty",
                request_data=request.data
            )
            return Response({"error": "Name field cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not subject.strip():
            logger.error("Subject field is empty.")
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='400',
                description="Contact form submission failed: Subject field empty",
                request_data=request.data
            )
            return Response({"error": "Subject field cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not description.strip():
            logger.error("Description field is empty.")
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='400',
                description="Contact form submission failed: Description field empty",
                request_data=request.data
            )
            return Response({"error": "Description field cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            logger.error("Invalid email format: %s", email)
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='400',
                description=f"Contact form submission failed: Invalid email format {email}",
                request_data=request.data
            )
            return Response({"error": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

        # Sending email
        try:
            send_mail(
                subject=f"Contact Us: {subject}",
                message=f"Name: {names}\nEmail: {email}\n\nDescription:\n{description}",
                from_email=email,
                recipient_list=['princemugabe568@gmail.com'],
                fail_silently=False,
            )
            logger.info("Email sent successfully to %s", email)
            
            # Calculate duration and log successful submission
            duration_ms = int((time.time() - start_time) * 1000)
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='200',
                description=f"Contact form submitted successfully by {names} ({email})",
                duration_ms=duration_ms,
                request_data={'names': names, 'email': email, 'subject': subject}
            )
            
            return Response({"message": "Email sent successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("An error occurred while sending email: %s", e)
            log_user_activity(
                activity_type='contact_submission',
                user=None,
                request=request,
                status_code='500',
                description=f"Contact form submission failed: Email sending error",
                request_data=request.data
            )
            return Response({"error": "Failed to send email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    logger.error("Invalid serializer data: %s", serializer.errors)
    log_user_activity(
        activity_type='contact_submission',
        user=None,
        request=request,
        status_code='400',
        description="Contact form submission failed: Invalid data",
        request_data=request.data,
        response_data={'errors': serializer.errors}
    )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






import traceback
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser
from .utils import generate_otp, store_otp, verify_otp, send_otp_email
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset_otp(request):
    """Request OTP for password reset with activity logging"""
    start_time = time.time()
    
    try:
        logger.info("\n" + "="*50)
        logger.info("PASSWORD RESET OTP REQUEST")
        logger.info("="*50)
        
        work_mail_address = request.data.get('work_mail_address', '').strip()
        
        if not work_mail_address:
            error_msg = "Work email address is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='otp_request',
                user=None,
                request=request,
                status_code='400',
                description="Password reset OTP request failed: Work email required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Check if user exists with this work email
        try:
            user = CustomUser.objects.get(work_mail_address=work_mail_address)
            logger.info(f"User found: {user.full_name}")
        except CustomUser.DoesNotExist:
            error_msg = "No account found with this work email address."
            logger.error(f"ERROR: {error_msg} - {work_mail_address}")
            log_user_activity(
                activity_type='otp_request',
                user=None,
                request=request,
                status_code='404',
                description=f"Password reset OTP request failed: User {work_mail_address} not found",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=404)
        
        # Check if user is active
        if not user.is_active or user.status != 'approved':
            error_msg = "Your account is not active. Please contact administrator."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='otp_request',
                user=user,
                request=request,
                status_code='400',
                description=f"Password reset OTP request failed: User {work_mail_address} account inactive",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Generate OTP
        otp = generate_otp(6)
        logger.info(f"Generated OTP: {otp} for user: {work_mail_address}")
        
        # Store OTP in cache (expires in 30 seconds)
        cache_key = store_otp(work_mail_address, otp, expiry_seconds=30)
        logger.info(f"OTP stored with cache key: {cache_key}")
        
        # Send OTP via email
        logger.info(f"Attempting to send OTP email to {user.email}...")
        email_sent = send_otp_email(user, otp)
        
        if not email_sent:
            error_msg = "Failed to send OTP email. Please try again."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='otp_request',
                user=user,
                request=request,
                status_code='500',
                description=f"Password reset OTP request failed: Email sending error for {work_mail_address}",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=500)
        
        # Calculate duration and log successful OTP request
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='otp_request',
            user=user,
            request=request,
            status_code='200',
            description=f"Password reset OTP sent to {work_mail_address}",
            duration_ms=duration_ms,
            request_data={'work_mail_address': work_mail_address}
        )
        
        logger.info(f"SUCCESS: OTP sent to {user.email}")
        logger.info("="*50 + "\n")
        
        return Response({
            "message": "OTP has been sent to your registered email address.",
            "work_mail_address": work_mail_address,
            "email": user.email,  # For debugging
            "expires_in": "30 seconds"
        }, status=200)
        
    except Exception as e:
        error_msg = f"Unexpected error during OTP request: {str(e)}"
        logger.error(f"CRITICAL ERROR: {error_msg}")
        logger.error(traceback.format_exc())
        log_user_activity(
            activity_type='otp_request',
            user=None,
            request=request,
            status_code='500',
            description=f"Password reset OTP request failed: Unexpected error",
            request_data=request.data
        )
        return Response({
            "error": "An unexpected error occurred. Please try again.",
            "detail": str(e)  # Include detail for debugging
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_otp(request):
    """Verify OTP for password reset with activity logging"""
    start_time = time.time()
    
    try:
        logger.info("\n" + "="*50)
        logger.info("VERIFY RESET OTP")
        logger.info("="*50)
        
        work_mail_address = request.data.get('work_mail_address', '').strip()
        otp = request.data.get('otp', '').strip()
        
        if not work_mail_address:
            error_msg = "Work email address is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='otp_verification',
                user=None,
                request=request,
                status_code='400',
                description="OTP verification failed: Work email required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not otp:
            error_msg = "OTP is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='otp_verification',
                user=None,
                request=request,
                status_code='400',
                description="OTP verification failed: OTP required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        logger.info(f"Verifying OTP for: {work_mail_address}")
        
        # Verify OTP
        is_valid, message = verify_otp(work_mail_address, otp)
        
        if not is_valid:
            logger.error(f"ERROR: OTP verification failed - {message}")
            log_user_activity(
                activity_type='otp_verification',
                user=None,
                request=request,
                status_code='400',
                description=f"OTP verification failed for {work_mail_address}: {message}",
                request_data=request.data
            )
            return Response({"error": message}, status=400)
        
        # Calculate duration and log successful OTP verification
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='otp_verification',
            user=None,
            request=request,
            status_code='200',
            description=f"OTP verified successfully for {work_mail_address}",
            duration_ms=duration_ms,
            request_data={'work_mail_address': work_mail_address}
        )
        
        logger.info(f"SUCCESS: OTP verified for {work_mail_address}")
        logger.info("="*50 + "\n")
        
        return Response({
            "message": "OTP verified successfully. You can now reset your password.",
            "verified": True,
            "work_mail_address": work_mail_address
        }, status=200)
        
    except Exception as e:
        error_msg = f"Unexpected error during OTP verification: {str(e)}"
        logger.error(f"CRITICAL ERROR: {error_msg}")
        logger.error(traceback.format_exc())
        log_user_activity(
            activity_type='otp_verification',
            user=None,
            request=request,
            status_code='500',
            description=f"OTP verification failed: Unexpected error",
            request_data=request.data
        )
        return Response({
            "error": "An unexpected error occurred. Please try again.",
            "detail": str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_with_otp(request):
    """Reset password after OTP verification with activity logging"""
    start_time = time.time()
    
    try:
        logger.info("\n" + "="*50)
        logger.info("PASSWORD RESET WITH OTP")
        logger.info("="*50)
        
        work_mail_address = request.data.get('work_mail_address', '').strip()
        # otp = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '').strip()
        confirm_password = request.data.get('confirm_password', '').strip()
        
        # Validate inputs
        if not work_mail_address:
            error_msg = "Work email address is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='400',
                description="Password reset failed: Work email required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # if not otp:
        #     error_msg = "OTP is required."
        #     logger.error(f"ERROR: {error_msg}")
        #     log_user_activity(
        #         activity_type='password_reset_complete',
        #         user=None,
        #         request=request,
        #         status_code='400',
        #         description="Password reset failed: OTP required",
        #         request_data=request.data
        #     )
        #     return Response({"error": error_msg}, status=400)
        
        if not new_password:
            error_msg = "New password is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='400',
                description="Password reset failed: New password required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not confirm_password:
            error_msg = "Password confirmation is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='400',
                description="Password reset failed: Password confirmation required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if new_password != confirm_password:
            error_msg = "Passwords do not match."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='400',
                description="Password reset failed: Passwords don't match",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Validate password strength
        password_error = is_valid_password(new_password)
        if password_error:
            logger.error(f"ERROR: {password_error}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='400',
                description="Password reset failed: Weak password",
                request_data=request.data
            )
            return Response({"error": password_error}, status=400)
        
        # Verify OTP one more time
        # is_valid, message = verify_otp(work_mail_address, otp)
        
        # if not is_valid:
        #     logger.error(f"ERROR: OTP verification failed - {message}")
        #     log_user_activity(
        #         activity_type='password_reset_complete',
        #         user=None,
        #         request=request,
        #         status_code='400',
        #         description=f"Password reset failed: OTP verification failed",
        #         request_data=request.data
        #     )
        #     return Response({"error": message}, status=400)
        
        # Get user
        try:
            user = CustomUser.objects.get(work_mail_address=work_mail_address)
            logger.info(f"User found: {user.full_name}")
        except CustomUser.DoesNotExist:
            error_msg = "User not found."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_reset_complete',
                user=None,
                request=request,
                status_code='404',
                description=f"Password reset failed: User {work_mail_address} not found",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=404)
        
        # Update password
        user.set_password(new_password)
        user.save()
        logger.info(f"SUCCESS: Password updated for user: {work_mail_address}")
        
        # Send confirmation email
        email_sent = False
        try:
            send_mail(
                subject="Password Reset Successful - CodePulse Africa Ltd",
                message=f"""
Hello {user.full_name},

Your password has been successfully reset for the Intelligent Workforce Performance Monitoring & Analytics System.

If you did not perform this action, please contact our support team immediately.

Best regards,
CodePulse Africa Ltd  Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"SUCCESS: Confirmation email sent to {user.email}")
            email_sent = True
        except Exception as e:
            logger.warning(f"WARNING: Password reset successful but email failed: {str(e)}")
            email_sent = False
        
        # Calculate duration and log successful password reset
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='password_reset_complete',
            user=user,
            request=request,
            status_code='200',
            description=f"Password reset successfully for {work_mail_address}",
            duration_ms=duration_ms,
            request_data={'work_mail_address': work_mail_address},
            response_data={'email_sent': email_sent}
        )
        
        logger.info("="*50 + "\n")
        
        return Response({
            "message": "Password reset successfully. You can now login with your new password.",
            "success": True,
            "email_sent": email_sent
        }, status=200)
        
    except Exception as e:
        error_msg = f"Unexpected error during password reset: {str(e)}"
        logger.error(f"CRITICAL ERROR: {error_msg}")
        logger.error(traceback.format_exc())
        log_user_activity(
            activity_type='password_reset_complete',
            user=None,
            request=request,
            status_code='500',
            description=f"Password reset failed: Unexpected error",
            request_data=request.data
        )
        return Response({
            "error": "An unexpected error occurred. Please try again.",
            "detail": str(e)
        }, status=500)
    





@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def users_list_create(request):
    """
    GET: List all users (admin/Manager only)
    POST: Create new user (admin/Manager only)
    """
    # Check permissions for both methods
    if not request.user.is_admin and not request.user.is_manager:
        log_user_activity(
            activity_type='users_list',
            user=request.user,
            request=request,
            status_code='403',
            description=f"Permission denied: User {request.user.email} attempted to access users list/create"
        )
        return Response({
            "error": "You are not authorized to perform this action."
        }, status=403)
    
    if request.method == 'GET':
        start_time = time.time()
        try:
            users = CustomUser.objects.all()
            serializer = CustomUserSerializer(users, many=True)
            
            # Calculate duration and log activity
            duration_ms = int((time.time() - start_time) * 1000)
            log_user_activity(
                activity_type='users_list',
                user=request.user,
                request=request,
                status_code='200',
                description=f"User {request.user.email} viewed users list ({users.count()} users)",
                duration_ms=duration_ms
            )
            
            return Response({"users": serializer.data}, status=200)
        except Exception as e:
            log_user_activity(
                activity_type='users_list',
                user=request.user,
                request=request,
                status_code='500',
                description=f"Error viewing users list: {str(e)}"
            )
            return Response({"error": f"An error occurred: {str(e)}"}, status=500)
    
    elif request.method == 'POST':
        # This is essentially the register_user function logic
        # We'll reuse it but ensure we log the activity
        start_time = time.time()
        
        try:
            print(f"\n{'='*50}")
            print(f"REGISTRATION REQUEST RECEIVED")
            print(f"{'='*50}")
            print(f"Submitted data: {request.data}\n")
            
            # Extract data
            phone_number = request.data.get('phone_number', '').strip()
            email = request.data.get('email', '').strip()
            full_name = request.data.get('full_name', '').strip()
            department = request.data.get('department') or None
            role = request.data.get('role', 'employee').strip().lower()
            requesting_user = request.user if request.user.is_authenticated else None
            
            # Validate required fields
            if not phone_number:
                error_msg = "Phone number is required."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Phone number required",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if not email:
                error_msg = "Email address is required."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Email required",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if not full_name:
                error_msg = "Full name is required."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Full name required",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            # Validate phone number format
            phone_error = is_valid_phone(phone_number)
            if phone_error:
                print(f"ERROR: {phone_error}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Invalid phone number",
                    request_data=request.data
                )
                return Response({"error": phone_error}, status=400)
            
            # Validate email format
            email_error = is_valid_email(email)
            if email_error:
                print(f"ERROR: {email_error}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Invalid email",
                    request_data=request.data
                )
                return Response({"error": email_error}, status=400)
            
            # Check role-based permissions
            if role not in ['admin', 'manager', 'employee', 'analyst']:
                error_msg = f"Invalid role '{role}'. Must be one of: admin, manager, employee, analyst"
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Invalid role {role}",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            # Department validation based on role
            if role == 'employee':
                if not department:
                    error_msg = "Department is required for employee users."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Department required for employee",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=400)
                
                # Validate department exists and is active
                try:
                    dept_obj = Department.objects.get(id=department, status='active')
                except Department.DoesNotExist:
                    error_msg = "Invalid or inactive department selected."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Invalid department",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=400)

            elif role in ['admin', 'manager', 'analyst']:
                # Admin and HR don't require departments
                department = None
            
            # Role-based permission checks
            if role != 'employee' and not requesting_user:
                error_msg = "Only admin or HR can create users with roles other than 'employee'."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=None,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Permission required for role {role}",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if requesting_user:
                if role == 'admin' and not requesting_user.is_admin:
                    error_msg = "Only admin can create admin users."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='403',
                        description=f"Permission denied: User {requesting_user.email} attempted to create admin user",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=403)
                if role == 'manager' and not requesting_user.is_admin:
                    error_msg = "Only admin can create Manager users."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='403',
                        description=f"Permission denied: User {requesting_user.email} attempted to create manager user",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=403)
                if role == 'analyst' and not (requesting_user.is_admin or requesting_user.is_manager):
                    error_msg = "Only admin or Manager can create analyst users."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='403',
                        description=f"Permission denied: User {requesting_user.email} attempted to create analyst user",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=403)
            
            # Check for existing users
            if CustomUser.objects.filter(phone_number=phone_number).exists():
                error_msg = "A user with this phone number already exists."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Duplicate phone number",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            if CustomUser.objects.filter(email=email).exists():
                error_msg = "A user with this email already exists."
                print(f"ERROR: {error_msg}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Duplicate email",
                    request_data=request.data
                )
                return Response({"error": error_msg}, status=400)
            
            # Handle password
            if requesting_user:
                password = generate_secure_password()
                if not password:
                    error_msg = "Failed to generate secure password. Please try again."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=requesting_user,
                        request=request,
                        status_code='500',
                        description=f"User creation failed: Password generation error",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=500)
            else:
                password = request.data.get('password', '').strip()
                confirm_password = request.data.get('confirm_password', '').strip()
                
                if not password:
                    error_msg = "Password is required."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=None,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Password required",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=400)
                
                if not confirm_password:
                    error_msg = "Password confirmation is required."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=None,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Password confirmation required",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=400)
                
                if password != confirm_password:
                    error_msg = "Passwords do not match."
                    print(f"ERROR: {error_msg}")
                    log_user_activity(
                        activity_type='user_create',
                        user=None,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Passwords don't match",
                        request_data=request.data
                    )
                    return Response({"error": error_msg}, status=400)
                
                password_error = is_valid_password(password)
                if password_error:
                    print(f"ERROR: {password_error}")
                    log_user_activity(
                        activity_type='user_create',
                        user=None,
                        request=request,
                        status_code='400',
                        description=f"User creation failed: Weak password",
                        request_data=request.data
                    )
                    return Response({"error": password_error}, status=400)
            
            # Generate work mail address
            try:
                work_mail_address = CustomUser.objects.generate_work_mail(full_name, role)
                print(f"Generated work email: {work_mail_address}")
            except Exception as e:
                error_msg = f"Failed to generate work email address: {str(e)}"
                print(f"ERROR: {error_msg}")
                print(traceback.format_exc())
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='500',
                    description=f"User creation failed: Work email generation error",
                    request_data=request.data
                )
                return Response({"error": "Failed to generate work email address. Please try again."}, status=500)
            
            # Create user with proper parameters based on role
            try:
                if role == 'employee':
                    user = CustomUser.objects.create_user(
                        phone_number=phone_number,
                        email=email,
                        full_name=full_name,
                        department=department,  # Pass department ID for employee
                        role=role,
                        work_mail_address=work_mail_address,
                        password=password,
                        created_by=requesting_user,
                        status='approved' if requesting_user else 'pending',
                        availability_status='active' if requesting_user else 'inactive'
                    )
                else:  # admin or manager or analyst
                    user = CustomUser.objects.create_user(
                        phone_number=phone_number,
                        email=email,
                        full_name=full_name,
                        department=None,
                        role=role,
                        work_mail_address=work_mail_address,
                        password=password,
                        created_by=requesting_user,
                        status='approved' if requesting_user else 'pending',
                        availability_status='active' if requesting_user else 'inactive'
                    )
                
                print(f"SUCCESS: User created with ID: {user.id}")
                print(f"User details: {user.full_name} - {user.work_mail_address}")
                
                if role == 'mentor':
                    print(f"Mentor departments: {[d.name for d in user.departments.all()]}")
                    
            except IntegrityError as e:
                error_msg = f"Database integrity error: A user with this information already exists."
                print(f"ERROR: {error_msg}")
                print(f"IntegrityError details: {str(e)}")
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='400',
                    description=f"User creation failed: Integrity error - duplicate user",
                    request_data=request.data
                )
                return Response({"error": "A user with this information already exists."}, status=400)
            except Exception as e:
                error_msg = f"Error creating user: {str(e)}"
                print(f"ERROR: {error_msg}")
                print(traceback.format_exc())
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='500',
                    description=f"User creation failed: User creation error",
                    request_data=request.data
                )
                return Response({"error": "Failed to create user account. Please try again."}, status=500)
            
            # Send email with credentials
            email_sent = False
            try:
                # Get department info for email
                dept_info = ""
                if role == 'employee':
                    dept_info = f"Department: {user.department.name}"
                elif role == 'mentor':
                    dept_names = [d.name for d in user.departments.all()]
                    dept_info = f"Departments: {', '.join(dept_names)}"
                else:
                    dept_info = "Department: N/A (Admin/HR)"
                
                subject = "Welcome to COdePulse Africa Ltd"
                message = f"""
            Hello {full_name},

            Your account has been successfully created in the Intelligent Workforce Performance Monitoring & Analytics System.

            Account Details:
            - Full Name: {full_name}
            - Role: {role.title()}
                - {dept_info}
                - Work Email: {work_mail_address}
                - Personal Email: {email}
                - Password: {password}

                Please use your work email ({work_mail_address}) to log in to the system.

                Important: This is a system-generated password. For security reasons, please change it after your first login.

                If you have any questions, please contact our support team.

                Best regards,
                CodePulse Africa Ltd Team
                            """
                            
                send_mail(
                                subject=subject,
                                message=message,
                                from_email="no-reply@codepulse_africa_ltd.com",
                                recipient_list=[email],
                                fail_silently=False,
                            )
                print(f"SUCCESS: Email sent to {email}")
                email_sent = True
                
                success_msg = "User registered successfully. Please check your email for login credentials."
                print(f"SUCCESS: {success_msg}")
                print(f"{'='*50}\n")
                
                # Calculate duration and log successful creation
                duration_ms = int((time.time() - start_time) * 1000)
                description = f"User {requesting_user.email} created new user {user.email} ({user.role})"
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='201',
                    description=description,
                    related_user_id=user.id,
                    duration_ms=duration_ms,
                    request_data=request.data,
                    response_data={
                        'work_mail_address': work_mail_address, 
                        'role': role,
                        'email_sent': email_sent
                    }
                )
                        
                return Response({
                            "message": success_msg,
                            "work_mail_address": work_mail_address,
                            "status": user.status,
                            "role": user.role
                        }, status=201)
                        
            except Exception as e:
                error_msg = f"Warning: User created but email failed to send: {str(e)}"
                print(f"WARNING: {error_msg}")
                email_sent = False
                
                # User created successfully but email failed - still return success
                success_msg = "User registered successfully. Please check your email for login credentials (email delivery may be delayed)."
                print(f"SUCCESS: {success_msg}")
                print(f"{'='*50}\n")
                
                # Calculate duration and log successful creation (with email warning)
                duration_ms = int((time.time() - start_time) * 1000)
                description = f"User {requesting_user.email} created new user {user.email} (email delivery failed)"
                log_user_activity(
                    activity_type='user_create',
                    user=requesting_user,
                    request=request,
                    status_code='201',
                    description=description,
                    related_user_id=user.id,
                    duration_ms=duration_ms,
                    request_data=request.data,
                    response_data={
                        'work_mail_address': work_mail_address, 
                        'role': role,
                        'email_sent': email_sent,
                        'email_warning': True
                    }
                )
                        
                return Response({
                            "message": success_msg,
                            "work_mail_address": work_mail_address,
                            "status": user.status,
                            "role": user.role,
                            "warning": "Email delivery may be delayed"
                        }, status=201)

        except Exception as e:
            error_msg = f"Unexpected error during registration: {str(e)}"
            print(f"CRITICAL ERROR: {error_msg}")
            print(traceback.format_exc())
            log_user_activity(
                activity_type='user_create',
                user=request.user if request.user.is_authenticated else None,
                request=request,
                status_code='500',
                description=f"User creation failed: Unexpected error",
                request_data=request.data
            )
            return Response({
                "error": "An unexpected error occurred during registration. Please try again or contact support."
            }, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_departments(request):
    """
    Get departments the logged-in user belongs to based on their role:
    - employee: Returns their single assigned department (ForeignKey)
    - Mentor: Returns all departments they're associated with (ManyToMany)
    - Admin/HR: Returns all departments in the system
    """
    start_time = time.time()
    
    try:
        user = CustomUser.objects.get(id=request.user.id)
    except CustomUser.DoesNotExist:
        print(f"User with ID {request.user.id} does not exist.")
        log_user_activity(
            activity_type='departments_list',
            user=request.user,
            request=request,
            status_code='404',
            description=f"User departments view failed: User {request.user.id} not found"
        )
        return Response(
            {
                'success': False,
                'message': 'User not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        # Determine which departments to return based on user role
        if user.role == 'employee':
            # employee: get their single department (ForeignKey)
            if user.department:
                departments = Department.objects.filter(id=user.department.id)
            else:
                departments = Department.objects.none()
        
        elif user.role in ['admin', 'manager', 'analyst']:
            # Admin/HR: get all departments in the system
            departments = Department.objects.all()
        
        else:
            # Unknown role
            departments = Department.objects.none()
        
        # Optional filtering by status
        status_filter = request.query_params.get('status', None)
        if status_filter:
            if status_filter not in ['active', 'inactive']:
                log_user_activity(
                    activity_type='departments_list',
                    user=user,
                    request=request,
                    status_code='400',
                    description=f"User departments view failed: Invalid status filter {status_filter}"
                )
                return Response(
                    {
                        'success': False,
                        'message': 'Invalid status filter. Use "active" or "inactive".'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            departments = departments.filter(status=status_filter)
        
        serializer = DepartmentSerializer(departments, many=True)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Build response message based on role
        if user.role == 'employee':
            message = 'Your assigned department retrieved successfully.'
            description = f"Employee {user.email} viewed their assigned department"
        elif user.role in ['admin', 'manager', 'analyst']:
            message = 'All departments retrieved successfully.'
            description = f"{user.role.capitalize()} {user.email} viewed all departments"
        else:
            message = 'Departments retrieved successfully.'
            description = f"User {user.email} with unknown role viewed departments"
        
        # Log activity
        log_user_activity(
            activity_type='departments_list',
            user=user,
            request=request,
            status_code='200',
            description=description,
            duration_ms=duration_ms,
            request_data=dict(request.query_params)
        )
        
        return Response(
            {
                'success': True,
                'message': message,
                'count': departments.count(),
                'user_role': user.role,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        log_user_activity(
            activity_type='departments_list',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Error viewing user departments: {str(e)}"
        )
        return Response(
            {
                'success': False,
                'message': f'An error occurred while retrieving your departments: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for logged-in user with current password verification and activity logging"""
    start_time = time.time()
    
    try:
        logger.info("\n" + "="*50)
        logger.info("PASSWORD CHANGE REQUEST")
        logger.info("="*50)
        
        user = request.user
        current_password = request.data.get('current_password', '').strip()
        new_password = request.data.get('new_password', '').strip()
        confirm_password = request.data.get('confirm_password', '').strip()
        
        # Validate required fields
        if not current_password:
            error_msg = "Current password is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: Current password required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not new_password:
            error_msg = "New password is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: New password required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        if not confirm_password:
            error_msg = "Password confirmation is required."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: Password confirmation required",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Verify current password
        if not user.check_password(current_password):
            error_msg = "Current password is incorrect."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: Incorrect current password",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Check if new password is same as current
        if user.check_password(new_password):
            error_msg = "New password cannot be the same as current password."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: New password same as current",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Check password match
        if new_password != confirm_password:
            error_msg = "New passwords do not match."
            logger.error(f"ERROR: {error_msg}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: Passwords don't match",
                request_data=request.data
            )
            return Response({"error": error_msg}, status=400)
        
        # Validate password strength
        password_error = is_valid_password(new_password)
        if password_error:
            logger.error(f"ERROR: {password_error}")
            log_user_activity(
                activity_type='password_change',
                user=user,
                request=request,
                status_code='400',
                description="Password change failed: Weak password",
                request_data=request.data
            )
            return Response({"error": password_error}, status=400)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        logger.info(f"SUCCESS: Password changed for user: {user.work_mail_address}")
        
        # Send notification email
        email_sent = False
        try:
            send_mail(
                subject="Password Changed Successfully - CodePulse Africa Ltd",
                message=f"""
Hello {user.full_name},

Your password has been successfully changed for the Intelligent Workforce Performance Monitoring & Analytics System.

If you did not make this change, please contact our support team immediately.

Best regards,
CodePulse Africa Ltd Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"SUCCESS: Notification email sent to {user.email}")
            email_sent = True
        except Exception as e:
            logger.warning(f"WARNING: Password changed but email failed: {str(e)}")
            email_sent = False
        
        # Calculate duration and log successful password change
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='password_change',
            user=user,
            request=request,
            status_code='200',
            description=f"User {user.email} changed their password successfully",
            duration_ms=duration_ms,
            request_data={'work_mail_address': user.work_mail_address},
            response_data={'email_sent': email_sent}
        )
        
        logger.info("="*50 + "\n")
        
        return Response({
            "message": "Password changed successfully.",
            "success": True,
            "email_sent": email_sent
        }, status=200)
        
    except Exception as e:
        error_msg = f"Unexpected error during password change: {str(e)}"
        logger.error(f"CRITICAL ERROR: {error_msg}")
        logger.error(traceback.format_exc())
        log_user_activity(
            activity_type='password_change',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Password change failed: Unexpected error",
            request_data=request.data
        )
        return Response({
            "error": "An unexpected error occurred. Please try again.",
            "detail": str(e)
        }, status=500)
    

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and blacklist refresh token with activity logging"""
    start_time = time.time()
    
    try:
        print("\n" + "="*50)
        print("LOGOUT REQUEST")
        print("="*50)
        
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            print("No refresh token provided")
            # Still log the logout activity
            duration_ms = int((time.time() - start_time) * 1000)
            log_user_activity(
                activity_type='user_logout',
                user=request.user,
                request=request,
                status_code='200',
                description=f"User {request.user.email} logged out (no token to blacklist)",
                duration_ms=duration_ms
            )
            return Response({
                "message": "Logged out successfully (no token to blacklist)"
            }, status=200)
        
        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            print(f"SUCCESS: Token blacklisted for user: {request.user.work_mail_address}")
            token_blacklisted = True
        except TokenError as e:
            print(f"Token error during blacklist: {str(e)}")
            # Token might already be invalid/blacklisted, but we still log them out
            token_blacklisted = False
        
        # Calculate duration and log logout activity
        duration_ms = int((time.time() - start_time) * 1000)
        description = f"User {request.user.email} logged out"
        if token_blacklisted is not None:
            description += f" (token blacklisted: {token_blacklisted})"
        
        log_user_activity(
            activity_type='user_logout',
            user=request.user,
            request=request,
            status_code='200',
            description=description,
            duration_ms=duration_ms,
            request_data={'token_blacklisted': token_blacklisted}
        )
        
        print("="*50 + "\n")
        
        return Response({
            "message": "Logged out successfully"
        }, status=200)
        
    except Exception as e:
        print(f"Error during logout: {str(e)}")
        print(traceback.format_exc())
        # Even if there's an error, we return success to ensure user is logged out on frontend
        # But still log the attempt
        log_user_activity(
            activity_type='user_logout',
            user=request.user,
            request=request,
            status_code='500',
            description=f"Logout with error: {str(e)}"
        )
        return Response({
            "message": "Logged out successfully"
        }, status=200)


# Add this endpoint to verify token validity
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Verify if the current access token is valid with activity logging"""
    start_time = time.time()
    
    try:
        user = request.user
        serializer = CustomUserSerializer(user)
        
        # Calculate duration and log token verification
        duration_ms = int((time.time() - start_time) * 1000)
        log_user_activity(
            activity_type='user_login',
            user=user,
            request=request,
            status_code='200',
            description=f"Token verified for user {user.email}",
            duration_ms=duration_ms
        )
        
        return Response({
            "valid": True,
            "user": serializer.data
        }, status=200)
        
    except Exception as e:
        log_user_activity(
            activity_type='user_login',
            user=None,
            request=request,
            status_code='401',
            description=f"Token verification failed: {str(e)}"
        )
        return Response({
            "valid": False,
            "error": str(e)
        }, status=401)