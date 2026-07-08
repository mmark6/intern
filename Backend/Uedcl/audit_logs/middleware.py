import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(MiddlewareMixin):
    """Persist a generic audit entry for authenticated API activity."""

    def process_response(self, request, response):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return response

        if request.method == 'OPTIONS':
            return response

        path = request.path or ''
        if path.startswith('/api/audit-logs/'):
            return response

        try:
            from audit_logs.utils import log_audit

            log_audit(
                request,
                'VIEW',
                'USER',
                getattr(user, 'id', None),
                getattr(user, 'username', ''),
                f"Authenticated request to {request.method} {path} (status {response.status_code})",
                user=user,
            )
        except Exception as exc:
            logger.exception('Failed to persist audit log for authenticated request: %s', exc)

        return response
