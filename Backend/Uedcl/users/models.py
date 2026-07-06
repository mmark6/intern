from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    DESCRIPTION = {
        'ADMIN': 'Administrative access to all features',
        'MANAGER': 'Project and task management access',
        'MEMBER': 'Basic task viewing and updating access',
    }
    PERMISSIONS = {
        'ADMIN': ['all'],
        'MANAGER': ['create_project', 'manage_tasks', 'view_all'],
        'MEMBER': ['view_tasks', 'update_own_tasks'],
    }
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Additional user fields (keep email - it overrides parent for unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    
    # Username validation
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_name()})"
    
    def get_role_name(self):
        return self.role.name if self.role else 'MEMBER'
    
    def has_permission(self, permission):
        if not self.role:
            return permission in self.PERMISSIONS.get('MEMBER', [])
        
        role_permissions = self.PERMISSIONS.get(self.role.name, [])
        return permission in role_permissions or 'all' in role_permissions
    
    @property
    def PERMISSIONS(self):
        return Role.PERMISSIONS