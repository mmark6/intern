
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .models import Task
from notifications.models import Notification
from .serializers import TaskSerializer
from users.permissions import IsAssigneeOrManager
from notifications.signals import notify_task_created, notify_task_done, notify_deadline


def _role_name(user):
    if not user or not user.is_authenticated:
        return ''
    role = getattr(user, 'role', None)
    if isinstance(role, str):
        return role.upper()
    return getattr(role, 'name', '').upper() if role else ''


class TaskListCreateView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.all()

        # Filters
        project_id = request.query_params.get('project_id')
        if project_id:
            tasks = tasks.filter(project_id=project_id)

        status_filter = request.query_params.get('status')
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        assignee_id = request.query_params.get('assignee_id')
        if assignee_id:
            tasks = tasks.filter(assignee_id=assignee_id)

        priority_filter = request.query_params.get('priority')
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)

        # Search
        search_query = request.query_params.get('search')
        if search_query:
            tasks = tasks.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        # Ordering — only allow safe fields
        order_by = request.query_params.get('order_by', 'created_at')
        order_dir = request.query_params.get('order_dir', 'desc')
        valid_order_fields = ['title', 'created_at', 'status', 'priority', 'due_date']
        if order_by not in valid_order_fields:
            order_by = 'created_at'
        tasks = tasks.order_by(order_by if order_dir == 'asc' else f'-{order_by}')

        # Simple pagination
        try:
            page = max(1, int(request.query_params.get('page', 1)))
            page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
        except (TypeError, ValueError):
            page, page_size = 1, 20

        total = tasks.count()
        tasks = tasks[(page - 1) * page_size: page * page_size]

        serializer = TaskSerializer(tasks, many=True)
        # Log task list view
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'TASK', None, 'Task List', f'Viewed task list ({total} tasks)')
        except Exception:
            pass
        return Response({
            'success': True,
            'count': total,
            'tasks': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        # Any authenticated user can create tasks (staff can add tasks to existing projects)
        serializer = TaskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            task = serializer.save()
            # Log task creation
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'CREATE', 'TASK', task.id, task.title, f'Created task: {task.title}')
            except Exception:
                pass

            # Create notification for task creation
            notify_task_created(task)
            return Response({
                'success': True,
                'message': 'Task created successfully',
                'task': TaskSerializer(task).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def _get_task(self, pk):
        try:
            return Task.objects.get(pk=pk), None
        except Task.DoesNotExist:
            return None, Response({
                'success': False,
                'error': 'Task not found',
            }, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        task, err = self._get_task(pk)
        if err:
            return err
        # Log task view
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'TASK', task.id, task.title, f'Viewed task: {task.title}')
        except Exception:
            pass
        return Response({
            'success': True,
            'task': TaskSerializer(task).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        task, err = self._get_task(pk)
        if err:
            return err

        if not IsAssigneeOrManager().has_object_permission(request, self, task):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            old_status = task.status
            task = serializer.save()
            # Log task update
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'UPDATE', 'TASK', task.id, task.title, f'Updated task: {task.title}')
            except Exception:
                pass
            # Create notification when task is marked as done
            if request.data.get('status') == 'DONE' and old_status != 'DONE':
                notify_task_done(task)
            return Response({
                'success': True,
                'message': 'Task updated successfully',
                'task': TaskSerializer(task).data,
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    put = patch

    def delete(self, request, pk):
        task, err = self._get_task(pk)
        if err:
            return err

        # Assignee, manager, or admin may delete
        role = _role_name(request.user)
        if request.user != task.assignee and role not in ('ADMIN', 'MANAGER'):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)

        # Log task deletion
        task_title = task.title
        task_id = task.id
        task.delete()
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'DELETE', 'TASK', task_id, task_title, f'Deleted task: {task_title}')
        except Exception:
            pass
        return Response({
            'success': True,
            'message': 'Task deleted successfully',
        }, status=status.HTTP_204_NO_CONTENT)


class TaskStatusView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Task not found',
            }, status=status.HTTP_404_NOT_FOUND)

        if not IsAssigneeOrManager().has_object_permission(request, self, task):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if not new_status:
            return Response({
                'success': False,
                'error': 'Status is required',
            }, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = dict(Task.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response({
                'success': False,
                'error': f'Invalid status. Allowed: {list(valid_statuses)}',
            }, status=status.HTTP_400_BAD_REQUEST)

        task.status = new_status
        task.save(update_fields=['status', 'updated_at'])

        # Log task status update
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'STATUS', 'TASK', task.id, task.title, f'Changed task status to: {new_status}')
        except Exception:
            pass

        # Create notification when task is marked as done
        if new_status == 'DONE':
            notify_task_done(task)

        return Response({
            'success': True,
            'message': 'Task status updated successfully',
            'task': TaskSerializer(task).data,
        }, status=status.HTTP_200_OK)


class TaskDeadlineCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Trigger deadline notification check for all tasks."""
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        three_days = today + timedelta(days=3)

        tasks = Task.objects.filter(
            assignee__isnull=False,
            status__ne='DONE',
            due_date__isnull=False,
        ).select_related('assignee', 'project')

        notifications_created = 0

        for task in tasks:
            # Skip if already has a due soon notification created recently
            existing = Notification.objects.filter(
                user=task.assignee,
                task_id=task.id,
                type__in=['TASK_DUE_SOON', 'TASK_OVERDUE'],
            ).exists()
            if existing:
                continue

            due_date = task.due_date

            if due_date < today:
                # Overdue
                Notification.objects.create(
                    user=task.assignee,
                    type='TASK_OVERDUE',
                    title=f'Overdue Task: {task.title}',
                    message=f'Your task "{task.title}" was due on {due_date}. Please update the status.',
                    project_id=task.project_id,
                    task_id=task.id,
                )
                notifications_created += 1
            elif due_date <= three_days:
                # Due soon
                days_left = (due_date - today).days
                if days_left == 0:
                    msg = f"Your task \"{task.title}\" is due today."
                elif days_left == 1:
                    msg = f"Your task \"{task.title}\" is due tomorrow."
                else:
                    msg = f"Your task \"{task.title}\" is due in {days_left} days."

                Notification.objects.create(
                    user=task.assignee,
                    type='TASK_DUE_SOON',
                    title=f'Task Due Soon: {task.title}',
                    message=msg,
                    project_id=task.project_id,
                    task_id=task.id,
                )
                notifications_created += 1

        return Response({
            'success': True,
            'message': f'Created {notifications_created} deadline notifications',
        }, status=status.HTTP_200_OK)
