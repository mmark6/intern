from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import AuditLog


class AuditLogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only admin can view audit logs
        role = getattr(request.user, 'role', None)
        role_name = getattr(role, 'name', '') if role else ''
        if role_name != 'ADMIN':
            return Response({
                'success': False,
                'error': 'Permission denied. Admin role required.',
            }, status=status.HTTP_403_FORBIDDEN)

        logs = AuditLog.objects.order_by('-timestamp')[:100]  # Last 100 logs

        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'username': log.username,
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'target_name': log.target_name,
                'description': log.description,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            })

        return Response({
            'success': True,
            'count': len(data),
            'logs': data,
        }, status=status.HTTP_200_OK)