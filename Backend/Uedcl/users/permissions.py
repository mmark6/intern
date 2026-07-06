
from rest_framework import permissions
from .models import User


class IsAdminUser(permissions.BasePermission):
    message = "Admin role required for this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.get_role_name() == 'ADMIN'


class IsManagerUser(permissions.BasePermission):
    
    message = "Manager role required for this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.get_role_name() in ['ADMIN', 'MANAGER']


class IsManagerOrAdmin(permissions.BasePermission):

    message = "Manager or Admin role required for this action."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.get_role_name() in ['ADMIN', 'MANAGER']


class IsAssigneeOrManager(permissions.BasePermission):
    """Only assignee or manager can modify task."""
    message = "You do not have permission to modify this resource."
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.get_role_name() == 'ADMIN':
            return True
        
        # Manager can modify any task
        if request.user.get_role_name() == 'MANAGER':
            return True
        
        # Member can only modify their own tasks
        return obj.assignee == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """Only owner or admin can modify resource."""
    message = "You do not have permission to modify this resource."
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.get_role_name() == 'ADMIN':
            return True
        
        # Owner can modify their own resource
        return obj.owner == request.user


class IsAuthenticated(permissions.BasePermission):
    """Check if user is authenticated."""
    message = "Authentication required. Please log in."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsReadOnly(permissions.BasePermission):
    """Allow read-only access."""
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class CustomPermission(permissions.BasePermission):
    """Custom permission based on user role."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        
        role_permissions = {
            'ADMIN': ['all'],
            'MANAGER': ['create', 'update', 'delete', 'list', 'retrieve'],
            'MEMBER': ['list', 'retrieve', 'update_own'],
        }
        
        user_role = request.user.get_role_name() if request.user.role else 'MEMBER'
        allowed_actions = role_permissions.get(user_role, ['list', 'retrieve'])
        
        # Check if action is allowed
        action = getattr(view, 'action', None)
        return action in allowed_actions or 'all' in allowed_actions
