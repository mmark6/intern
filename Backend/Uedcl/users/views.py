
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import UserRateThrottle
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .models import User, Role
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    RoleSerializer,
    CustomTokenObtainPairSerializer,
)
from .permissions import IsAdminUser
from .validators import sanitize_dict


class LoginRateThrottle(UserRateThrottle):

    scope = 'login'


@method_decorator(never_cache, name='dispatch')
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        # Don't sanitize email/passwords - they contain valid chars like @ and !
        raw_data = dict(request.data)
        email = raw_data.pop('email', '')
        password = raw_data.pop('password', '')
        password2 = raw_data.pop('password2', '')
        data = sanitize_dict(raw_data)
        if email:
            data['email'] = email
        if password:
            data['password'] = password
        if password2:
            data['password2'] = password2

        logger.debug('[Register] Received data: username=%s, email=%s', data.get('username'), data.get('email'))

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            logger.debug('[Register] User created: %s', user.username)
            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)

        logger.debug('[Register] Validation errors: %s', serializer.errors)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(never_cache, name='dispatch')
class LoginView(APIView):

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        # Don't sanitize email/password - they contain valid chars like @ and !
        raw_data = dict(request.data)
        email = raw_data.pop('email', '')
        password = raw_data.pop('password', '')
        data = sanitize_dict(raw_data)
        if email:
            data['email'] = email
        if password:
            data['password'] = password

        logger.debug('[Login] Attempt: email=%s', data.get('email'))

        serializer = CustomTokenObtainPairSerializer(data=data)
        if serializer.is_valid():
            logger.debug('[Login] Success: email=%s', data.get('email'))

            # Log successful login
            try:
                from audit_logs.utils import log_audit
                user_obj = serializer.validated_data.get('user')
                log_audit(request, 'LOGIN', 'USER', getattr(user_obj, 'id', None), getattr(user_obj, 'username', ''), 'User logged in', user=user_obj)
            except Exception:
                pass  # Don't break login if audit fails

            token_data = serializer.validated_data
            # Ensure frontend gets the exact user shape it expects
            user_obj = token_data.get('user')

            return Response({
                'success': True,
                'access_token': token_data['access'],
                'refresh_token': token_data['refresh'],
                'user': user_obj,
            }, status=status.HTTP_200_OK)

        logger.debug('[Login] Failed: email=%s, errors=%s', data.get('email'), serializer.errors)
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Invalid username or password',
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Log logout
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'LOGOUT', 'USER', request.user.id, request.user.username, 'User logged out')
        except Exception:
            pass  

        return Response({
            'success': True,
            'message': 'Logged out successfully',
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'success': True,
            'user': UserSerializer(request.user).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        data = sanitize_dict(request.data)

       
        allowed_fields = ['phone', 'first_name', 'last_name']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return Response({
                'success': False,
                'error': 'No valid fields to update',
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)



def _role_name(user):
    if not user or not user.is_authenticated:
        return ''
    return user.get_role_name() if hasattr(user, 'get_role_name') else ''


def _is_admin(user):
    return _role_name(user) == 'ADMIN'


def _is_manager_or_admin(user):
    return _role_name(user) in ('ADMIN', 'MANAGER')


class UserListCreateView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Return all users for both admin view and assignee selection (newest created first)
        users = User.objects.order_by('-created_at')

        serializer = UserSerializer(users, many=True)
        # Log audit
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'USER', None, 'User List', 'Viewed user list')
        except Exception:
            pass
        return Response({
            'success': True,
            'count': users.count(),
            'users': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not _is_admin(request.user):
            return Response({
                'success': False,
                'error': 'Permission denied. Admin role required.',
            }, status=status.HTTP_403_FORBIDDEN)

        # Get password directly first (don't sanitize passwords - it corrupts them!)
        password = request.data.get('password', '')
        password2 = request.data.get('password2', '')

        # Sanitize the rest of the data (but not passwords)
        data = sanitize_dict(request.data)

        # Put back the unsanitized passwords
        data['password'] = password
        data['password2'] = password2

        import logging
        logger = logging.getLogger(__name__)

        logger.debug('[AdminCreate] Creating user with username: %s, email: %s, role: %s',
                    data.get('username'), data.get('email'), data.get('role'))
        logger.debug('[AdminCreate] Password provided: %s', 'yes' if data.get('password') else 'NO')

        # Pass context to skip uniqueness validation for admin-created users
        serializer = UserSerializer(data=data, context={'admin_create': True})
        if serializer.is_valid():
            user = serializer.save()
            # Log user creation by admin
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'CREATE', 'USER', user.id, user.username, f'Created user: {user.username} with role: {data.get("role")}')
            except Exception:
                pass
            # Verify password was hashed correctly
            password_check = user.check_password(data.get('password', ''))
            logger.debug('[AdminCreate] User %s created, password valid: %s', user.username, password_check)
            return Response({
                'success': True,
                'message': 'User created successfully',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        print(f"User creation failed: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def _can_view_or_edit(self, request, pk):
        return str(pk) == str(request.user.id) or _is_admin(request.user)

    def get(self, request, pk):
        if not self._can_view_or_edit(request, pk):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
            }, status=status.HTTP_404_NOT_FOUND)
        # Log audit
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'USER', user.id, user.username, f'Viewed user profile: {user.username}')
        except Exception:
            pass
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        if not self._can_view_or_edit(request, pk):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
            }, status=status.HTTP_404_NOT_FOUND)

        data = sanitize_dict(request.data)
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            # Log user profile update
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'UPDATE', 'USER', user.id, user.username, f'Updated user profile: {user.username}')
            except Exception:
                pass
            return Response({
                'success': True,
                'message': 'User updated successfully',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    put = patch

    def delete(self, request, pk):
        if not _is_admin(request.user):
            return Response({
                'success': False,
                'error': 'Permission denied. Admin role required.',
            }, status=status.HTTP_403_FORBIDDEN)
        if str(pk) == str(request.user.id):
            return Response({
                'success': False,
                'error': 'Cannot delete your own account',
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found',
            }, status=status.HTTP_404_NOT_FOUND)
        username = user.username
        user.delete()
        # Log user deletion by admin
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'DELETE', 'USER', pk, username, f'Deleted user: {username}')
        except Exception:
            pass
        return Response({
            'success': True,
            'message': 'User deleted successfully',
        }, status=status.HTTP_204_NO_CONTENT)



class RoleListCreateView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        roles = Role.objects.all()
        return Response({
            'success': True,
            'count': roles.count(),
            'roles': RoleSerializer(roles, many=True).data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        data = sanitize_dict(request.data)
        serializer = RoleSerializer(data=data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                'success': True,
                'message': 'Role created successfully',
                'role': RoleSerializer(role).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class UserImageView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No image provided',
            }, status=status.HTTP_400_BAD_REQUEST)

        image = request.FILES['image']
        user = request.user

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image.content_type not in allowed_types:
            return Response({
                'success': False,
                'error': 'Invalid image type. Allowed: JPEG, PNG, GIF, WebP',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return Response({
                'success': False,
                'error': 'Image too large. Max 5MB',
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete old image if exists
        if user.image:
            user.image.delete()

        user.image = image
        user.save()

        return Response({
            'success': True,
            'message': 'Image uploaded successfully',
            'image': request.build_absolute_uri(user.image.url),
        }, status=status.HTTP_200_OK)

    def delete(self, request):
      
        user = request.user
        if user.image:
            user.image.delete()
            user.image = None
            user.save()
            return Response({
                'success': True,
                'message': 'Image removed successfully',
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'error': 'No image to remove',
        }, status=status.HTTP_400_BAD_REQUEST)
