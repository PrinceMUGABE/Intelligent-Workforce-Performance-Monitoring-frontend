# userApp/models.py - Fixed with Custom Email Field

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
import random
import string
import re


class WorkEmailValidator(EmailValidator):
    """Custom email validator that allows underscores in domain names"""
    message = "Enter a valid work email address."
    
    # Modified regex to allow underscores in domain
    domain_regex = r'((?:[A-Z0-9_](?:[A-Z0-9_-]{0,61}[A-Z0-9_])?\.)+)(?:[A-Z0-9_-]{2,63}(?<!-))$'
    
    def __call__(self, value):
        # Custom validation for work email
        if not value or '@' not in value:
            raise ValidationError(self.message, code=self.code)
        
        # Split into local and domain parts
        parts = value.rsplit('@', 1)
        if len(parts) != 2:
            raise ValidationError(self.message, code=self.code)
        
        local_part, domain_part = parts
        
        # Validate local part (before @)
        if not local_part or len(local_part) > 64:
            raise ValidationError(self.message, code=self.code)
        
        # Validate domain part (after @) - allow underscores
        if not domain_part:
            raise ValidationError(self.message, code=self.code)
        
        # Check for valid domain format (allowing underscores)
        domain_pattern = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*\.[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, domain_part):
            raise ValidationError(self.message, code=self.code)


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, email=None, full_name=None, role=None, department=None, 
                    departments=None, status='pending', availability_status='inactive', 
                    work_mail_address=None, password=None, created_by=None):
        if not phone_number:
            raise ValueError("The phone number must be provided")
        if not full_name:
            raise ValueError("The full name must be provided")
        if not role:
            raise ValueError("The role must be provided")
        if role not in [choice[0] for choice in CustomUser.ROLE_CHOICES]:
            raise ValueError("Invalid role selected")
        
        # Department validation based on role
        from departmentApp.models import Department
        
        if role == 'employee':
            # Employees require a single department (ForeignKey)
            if not department:
                raise ValueError("The department must be provided for employee users")
            
            if not Department.objects.filter(id=department, status='active').exists():
                raise ValueError("Invalid or inactive department selected")
        
        elif role in ['admin', 'manager', 'analyst']:
            # Admin and HR don't require departments
            department = None
            departments = None

        user = self.model(
            phone_number=phone_number,
            full_name=full_name,
            role=role,
            department_id=department if role == 'employee' else None,
            status=status,
            availability_status=availability_status
        )
        
        if email:
            email = self.normalize_email(email)
            user.email = email
        
        if work_mail_address:
            user.work_mail_address = work_mail_address
        else:
            user.work_mail_address = self.generate_work_mail(full_name, role)
        
        if created_by:
            user.created_by = created_by
            
        user.set_password(password)
        user.save(using=self._db)

        
        return user

    def create_superuser(self, phone_number, email, full_name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone number must be provided for superuser")
        if not email:
            raise ValueError("The email must be provided for superuser")
        if not full_name:
            raise ValueError("The full name must be provided for superuser")
        if not password:
            raise ValueError("The password must be provided for superuser")
        
        work_mail = self.generate_work_mail(full_name, 'admin')
        
        user = self.create_user(
            phone_number=phone_number,
            email=email,
            full_name=full_name,
            role='admin',
            department=None,
            status='approved',
            availability_status='active',
            work_mail_address=work_mail,
            password=password
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    @staticmethod
    def generate_work_mail(full_name, role):
        """Generate work mail address from full name with role prefix."""
        full_name = full_name.strip()
        names = full_name.split()
        
        role_prefixes = {
            'admin': 'admin',
            'manager': 'manager',
            'analyst': 'analyst',
            'employee': 'employee'
        }
        role_prefix = role_prefixes.get(role, 'user')
        
        if len(names) >= 2:
            first_initial = names[0][0].lower()
            last_name = names[-1].lower().replace(' ', '')
            base_mail = f"{first_initial}.{last_name}@{role_prefix}_codepulse_africa_ltd.com"
        else:
            base_mail = f"{full_name.lower().replace(' ', '')}@{role_prefix}_codepulse_africa_ltd.com"
        
        from userApp.models import CustomUser
        mail_exists = CustomUser.objects.filter(work_mail_address=base_mail).exists()
        
        if not mail_exists:
            return base_mail
        
        random_num = random.randint(100, 999)
        if len(names) >= 2:
            return f"{first_initial}.{last_name}{random_num}@{role_prefix}_codepulse_africa_ltd.com"
        else:
            return f"{full_name.lower().replace(' ', '')}{random_num}@{role_prefix}_codepulse_africa_ltd.com"

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
        ('none', 'No Day Off'),
    ]

    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    
    # Use CharField instead of EmailField to avoid validation issues with custom domain
    work_mail_address = models.CharField(
        max_length=255,
        unique=True,
        validators=[WorkEmailValidator()],
        help_text="Work email address with custom domain format"
    )
    
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    
    # Single department for employee users (ForeignKey)
    department = models.ForeignKey(
        'departmentApp.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='inactive')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    
    day_off = models.CharField(
        max_length=20, 
        choices=DAY_CHOICES, 
        default='none',
        blank=True,
        null=True,
        help_text="User's preferred day off"
    )
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'full_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.work_mail_address

    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_analyst(self):
        return self.role == 'analyst'
    
    @property
    def is_employee(self):
        return self.role == 'employee'
    
    def can_update_departments(self):
        """Check if user can update other users' departments"""
        return self.role in ['admin', 'manager']
    
    def clean(self):
        """Validate department requirements based on role"""
        super().clean()
        
        # employees require a single department
        if self.role == 'employee' and not self.department:
            raise ValidationError({'department': 'Employee users must have a department assigned.'})
        
        # Admin and HR don't require departments
        if self.role in ['admin', 'manager', 'analyst']:
            self.department = None
    
    def save(self, *args, **kwargs):
        # Only validate if not bypassing validation
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        super().save(*args, **kwargs)
        