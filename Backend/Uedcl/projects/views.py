
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Project
from .serializers import ProjectSerializer
from users.validators import sanitize_dict
from notifications.signals import notify_project_created, notify_project_deadline
from notifications.models import Notification


def _role_name(user):
    
    if not user or not user.is_authenticated:
        return ''
    role = getattr(user, 'role', None)
    if isinstance(role, str):
        return role.upper()
    return getattr(role, 'name', '').upper() if role else ''


def _is_admin(user):
    return _role_name(user) == 'ADMIN'


def _is_manager_or_admin(user):
    return _role_name(user) in ('ADMIN', 'MANAGER')


class ProjectListCreateView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # All authenticated users can view all projects
        projects = Project.objects.all()

        # Optional filters
        status_filter = request.query_params.get('status')
        if status_filter:
            status_filter = sanitize_dict({'status': status_filter})['status']
            projects = projects.filter(status=status_filter)

        owner_id = request.query_params.get('owner_id')
        if owner_id and _is_admin(user):
            try:
                projects = projects.filter(owner_id=int(owner_id))
            except (ValueError, TypeError):
                pass

        search_query = request.query_params.get('search')
        if search_query:
            search_query = sanitize_dict({'search': search_query})['search']
            projects = projects.filter(name__icontains=search_query)

        # Ordering
        order_by = request.query_params.get('order_by', 'created_at')
        order_dir = request.query_params.get('order_dir', 'desc')
        valid_order_fields = ['name', 'created_at', 'status', 'priority']
        if order_by not in valid_order_fields:
            order_by = 'created_at'
        projects = projects.order_by(order_by if order_dir == 'asc' else f'-{order_by}')

        serializer = ProjectSerializer(projects, many=True)
        # Log audit
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'PROJECT', None, 'Project List', 'Viewed project list')
        except Exception:
            pass
        return Response({
            'success': True,
            'count': projects.count(),
            'projects': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        if not _is_manager_or_admin(request.user):
            return Response({
                'success': False,
                'error': 'Permission denied. Manager or Admin role required.',
            }, status=status.HTTP_403_FORBIDDEN)

        data = sanitize_dict(request.data)
        data['owner'] = request.user.id

        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            project = serializer.save()
            # Log project creation
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'CREATE', 'PROJECT', project.id, project.name, f'Created project: {project.name}')
            except Exception:
                pass

            # Create notification for project creation
            notify_project_created(project)
            return Response({
                'success': True,
                'message': 'Project created successfully',
                'project': ProjectSerializer(project).data,
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def _get_object(self, pk, user):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return None, Response({
                'success': False,
                'error': 'Project not found',
            }, status=status.HTTP_404_NOT_FOUND)

        if project.owner != user and not _is_admin(user):
            return None, Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)
        return project, None

    def get(self, request, pk):
        project, err = self._get_object(pk, request.user)
        if err:
            return err
        return Response({
            'success': True,
            'project': ProjectSerializer(project).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        project, err = self._get_object(pk, request.user)
        if err:
            return err

        data = sanitize_dict(request.data)
        serializer = ProjectSerializer(project, data=data, partial=True)
        if serializer.is_valid():
            project = serializer.save()
            # Log project update
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'UPDATE', 'PROJECT', project.id, project.name, f'Updated project: {project.name}')
            except Exception:
                pass
            return Response({
                'success': True,
                'message': 'Project updated successfully',
                'project': ProjectSerializer(project).data,
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    # Treat PUT as partial update too — frontend uses PATCH but PUT is a sensible fallback
    put = patch

    def delete(self, request, pk):
        project, err = self._get_object(pk, request.user)
        if err:
            return err

        # Only ADMIN or MANAGER can delete projects
        if not _is_manager_or_admin(request.user):
            return Response({
                'success': False,
                'error': 'Permission denied. Manager or Admin role required to delete projects.',
            }, status=status.HTTP_403_FORBIDDEN)

        # Log project deletion
        project_name = project.name
        project_id = project.id
        project.delete()
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'DELETE', 'PROJECT', project_id, project_name, f'Deleted project: {project_name}')
        except Exception:
            pass
        return Response({
            'success': True,
            'message': 'Project deleted successfully',
        }, status=status.HTTP_204_NO_CONTENT)


class ProjectDeadlineCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Trigger deadline notification check for all projects."""
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        three_days = today + timedelta(days=3)

        projects = Project.objects.filter(
            owner__isnull=False,
            status__ne='COMPLETED',
            end_date__isnull=False,
        ).select_related('owner')

        notifications_created = 0

        for project in projects:
            # Skip if already has a deadline notification created recently
            existing = Notification.objects.filter(
                user=project.owner,
                project_id=project.id,
                type__in=['PROJECT_DUE_SOON', 'PROJECT_OVERDUE'],
            ).exists()
            if existing:
                continue

            end_date = project.end_date

            if end_date < today:
                # Overdue
                Notification.objects.create(
                    user=project.owner,
                    type='PROJECT_OVERDUE',
                    title=f'Project Overdue: {project.name}',
                    message=f'Your project "{project.name}" was due on {end_date}.',
                    project_id=project.id,
                )
                notifications_created += 1
            elif end_date <= three_days:
                # Due soon
                days_left = (end_date - today).days
                if days_left == 0:
                    msg = f'Your project "{project.name}" is due today.'
                elif days_left == 1:
                    msg = f'Your project "{project.name}" is due tomorrow.'
                else:
                    msg = f'Your project "{project.name}" is due in {days_left} days.'

                Notification.objects.create(
                    user=project.owner,
                    type='PROJECT_DUE_SOON',
                    title=f'Project Due Soon: {project.name}',
                    message=msg,
                    project_id=project.id,
                )
                notifications_created += 1

        return Response({
            'success': True,
            'message': f'Created {notifications_created} project deadline notifications',
        }, status=status.HTTP_200_OK)
