from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets


class Department(models.Model):
    """Department model for organizing users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """Extended user model with additional fields"""
    
    USER_ROLES = [
        ('admin', 'Admin'),
        ('user', 'Regular User'),
    ]
    
    # Additional fields
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user')
    is_approved = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def get_department_name(self):
        return self.department.name if self.department else "No Department"


class UserRegistrationRequest(models.Model):
    """Model for handling user registration requests that need admin approval"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # User information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    whatsapp_number = models.CharField(max_length=15)
    
    # Request status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    one_time_code = models.CharField(max_length=6, blank=True)
    code_generated_at = models.DateTimeField(null=True, blank=True)
    code_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Admin actions
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.status}"
    
    def generate_one_time_code(self):
        """Generate a 6-digit one-time code"""
        self.one_time_code = str(secrets.randbelow(1000000)).zfill(6)
        self.code_generated_at = timezone.now()
        self.code_expires_at = timezone.now() + timezone.timedelta(hours=24)
        self.save()
        return self.one_time_code
    
    def is_code_valid(self):
        """Check if the one-time code is still valid"""
        if not self.code_expires_at:
            return False
        return timezone.now() < self.code_expires_at
    
    def approve_request(self, admin_user):
        """Approve the registration request"""
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject_request(self, admin_user, notes=""):
        """Reject the registration request"""
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()
    
    class Meta:
        ordering = ['-created_at']
