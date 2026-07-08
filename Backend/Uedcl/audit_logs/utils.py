"""Utility functions for audit logging."""

from .models import AuditLog


def log_audit(request, action, target_type, target_id=None, target_name='', description='', user=None):
    """Log an audit event."""

    if user is None and request and hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False):
        user = request.user

    username = user.username if user else 'Anonymous'

    # Get IP address
    ip_address = ''
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')

    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

    AuditLog.objects.create(
        user=user,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )