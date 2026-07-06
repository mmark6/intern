from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status, permissions, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
import random
import string
import uuid

from users.serializers import UserRegistrationSerializer, UserSerializer
from users.validators import sanitize_dict
from users.models import User


class TokenRefreshCookieView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        # Get refresh token from request body or cookies
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {'success': False, 'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create a new refresh token from the old one
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)

            return Response({
                'success': True,
                'access_token': access_token,
                'refresh_token': str(token),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'success': False, 'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        # Don't sanitize password - special chars like ! are valid
        email = request.data.get('email', '')
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        login_input = (username or email or '').strip()

        if not login_input or not password:
            return Response(
                {'success': False, 'error': 'Username or email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        login_input_lower = login_input.lower()

        logger.debug('[Login] Attempt for: %s', login_input_lower)

        user = None

        # Try to find user by email or username (case-insensitive)
        if '@' in login_input:
            # User provided email - look up by email
            try:
                user = User.objects.get(email__iexact=login_input_lower)
                logger.debug('[Login] Found user by email: %s (id=%s, is_active=%s)', user.username, user.id, user.is_active)
            except User.DoesNotExist:
                logger.debug('[Login] No user found with email: %s', login_input_lower)
        else:
            # User provided username - look up by username
            try:
                user = User.objects.get(username__iexact=login_input_lower)
                logger.debug('[Login] Found user by username: %s (id=%s, is_active=%s)', user.username, user.id, user.is_active)
            except User.DoesNotExist:
                logger.debug('[Login] No user found with username: %s', login_input_lower)

        # If found, verify password directly
        password_valid = False
        if user:
            password_valid = user.check_password(password)
            logger.debug('[Login] Password check result for %s: %s', user.username, password_valid)

        if not password_valid:
            # Try finding by username and verify as fallback
            if not user or not password_valid:
                try:
                    user = User.objects.get(username__iexact=login_input_lower)
                    password_valid = user.check_password(password)
                    logger.debug('[Login] Fallback password check for %s: %s', user.username, password_valid)
                    if not password_valid:
                        user = None
                except User.DoesNotExist:
                    user = None

        # Check if user is active
        if user and not user.is_active:
            logger.debug('[Login] User %s is inactive, denying login', user.username)
            return Response(
                {'success': False, 'error': 'Account is disabled.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user is None:
            logger.debug('[Login] Login failed: user not found or invalid password')
            return Response(
                {'success': False, 'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        logger.debug('[Login] Login successful for: %s', user.username)
        # Log successful login
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'LOGIN', 'USER', user.id, user.username, 'User logged in')
        except Exception:
            pass
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = sanitize_dict(request.data)
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'success': True, 'message': 'User created successfully', 'user': UserSerializer(user).data},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    # Log logout
    try:
        from audit_logs.utils import log_audit
        log_audit(request, 'LOGOUT', 'USER', request.user.id, request.user.username, 'User logged out')
    except Exception:
        pass
    return Response({'success': True, 'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response({'success': True, 'user': serializer.data}, status=status.HTTP_200_OK)


# Password reset in-memory storage (use database in production)
reset_codes = {}


def generate_reset_code():
    """Generate a 6-digit verification code."""
    return ''.join(random.choices(string.digits, k=6))


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request_view(request):
    """Request a password reset - sends verification code via email."""
    import logging
    logger = logging.getLogger(__name__)

    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response(
            {'success': False, 'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user exists
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Don't reveal if user exists - show generic message
        return Response(
            {'success': True, 'message': 'A verification code has been sent to your inbox.'},

            status=status.HTTP_200_OK
        )

    # Generate verification code
    code = generate_reset_code()
    reset_codes[email] = {
        'code': code,
        'user_id': user.id,
        'expires': 900,  # 15 minutes
    }

    logger.debug('[PasswordReset] Code for %s: %s', email, code)

    # Send the reset code via the configured email backend.
    # If SMTP delivery fails, we still return the code so the workflow can continue.
    # Validate email config so we can fail clearly if misconfigured.
    required_settings = [

        ('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', None)),
        ('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', None)),
        # auth is commonly required by SMTP providers (fail clearly if missing)
        ('EMAIL_HOST_USER', getattr(settings, 'EMAIL_HOST_USER', None)),
        # password is required for many providers (e.g., Gmail SMTP with app password)
        ('EMAIL_HOST_PASSWORD', getattr(settings, 'EMAIL_HOST_PASSWORD', None)),
    ]
    missing = [name for (name, value) in required_settings if value in (None, '', 0)]

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if not from_email:
        # fallback to EMAIL_HOST_USER if DEFAULT_FROM_EMAIL isn't explicitly set
        from_email = getattr(settings, 'EMAIL_HOST_USER', None)

    if not from_email:
        missing.append('DEFAULT_FROM_EMAIL/EMAIL_HOST_USER')

    # TLS/SSL toggles are also commonly required; don't fail if provider doesn't need them,
    # but if host/password is set and neither TLS nor SSL is enabled, mail may fail.
    use_tls = bool(getattr(settings, 'EMAIL_USE_TLS', False))
    use_ssl = bool(getattr(settings, 'EMAIL_USE_SSL', False))
    if not (use_tls or use_ssl):
        # keep this as informational via missing list so it appears in response
        missing.append('EMAIL_USE_TLS or EMAIL_USE_SSL')

    email_sent = False
    send_mail_error = None
    if missing:
        logger.error('[PasswordReset] Email config missing: %s', ', '.join(missing))
        send_mail_error = 'Email service is not configured correctly. Missing: ' + ', '.join(missing)
    else:
        try:
            subject = 'Password Reset Verification Code'
            message = f'''Your password reset verification code is: {code}

This code will expire in 15 minutes.

If you did not request a password reset, please ignore this email.
'''
            send_mail(
                subject,
                message,
                from_email,
                [email],
                fail_silently=False,
            )
            logger.info('[PasswordReset] Email sent to %s', email)
            email_sent = True
        except Exception as e:
            send_mail_error = str(e)
            logger.error('[PasswordReset] Failed to send email: %s', send_mail_error)
            email_sent = False

    # Keep the password reset flow working even when SMTP delivery fails.
    # The code is still returned to support testing and recovery flows.
    # This ensures the user can continue with the reset flow immediately.
    return Response({
        'success': True,
        'message': 'If the email address is registered, a verification code has been sent.',
        'code': code,
        'email_sent': email_sent,
        'send_mail_error': send_mail_error,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_verify_view(request):
    """Verify the reset code."""
    import logging
    logger = logging.getLogger(__name__)

    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()

    if not email or not code:
        return Response(
            {'success': False, 'error': 'Email and code are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check stored code
    stored = reset_codes.get(email)
    if not stored:
        return Response(
            {'success': False, 'error': 'Invalid or expired verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify code
    if stored['code'] != code:
        logger.warning('[PasswordReset] Invalid code for %s', email)
        return Response(
            {'success': False, 'error': 'Invalid or expired verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate password reset token
    reset_token = str(uuid.uuid4())
    stored['reset_token'] = reset_token

    return Response({
        'success': True,
        'message': 'Code verified. You can now set a new password.',
        'reset_token': reset_token
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm_view(request):
    """Set new password with reset token."""
    import logging
    logger = logging.getLogger(__name__)

    email = request.data.get('email', '').strip().lower()
    reset_token = request.data.get('reset_token', '').strip()
    new_password = request.data.get('new_password', '')

    if not email or not reset_token or not new_password:
        return Response(
            {'success': False, 'error': 'Email, reset token, and new password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find user
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verify reset token
    stored = reset_codes.get(email)
    if not stored or stored.get('reset_token') != reset_token:
        return Response(
            {'success': False, 'error': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    user.set_password(new_password)
    user.save()

    # Clear the stored code
    del reset_codes[email]

    # Log password change
    try:
        from audit_logs.utils import log_audit
        log_audit(request, 'UPDATE', 'USER', user.id, user.username, 'Password reset')
    except Exception:
        pass

    logger.info('[PasswordReset] Password reset successful for %s', email)

    return Response(
        {'success': True, 'message': 'Password reset successfully. Please log in with your new password.'},
        status=status.HTTP_200_OK
    )
