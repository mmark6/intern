"""
Dashboard views — aggregate statistics for the UI.

Two important bug fixes vs the previous version:

1. `Task.objects.filter(is_overdue=True)` was a FieldError because `is_overdue`
   is a computed Python property, not a DB column. Overdue is now computed via
   a Q query: due_date < today AND status != 'DONE'.

2. `project.task_count`, `project.completed_task_count`, and
   `project.progress_percentage` are methods on the Project model, not
   properties. The old code accessed them without `()`, so it serialized bound
   methods instead of integers. They're now called as functions.

Also: views moved to DRF APIView so JWT auth runs.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from projects.models import Project
from tasks.models import Task


def home(request):
    """Simple HTML landing page (used by the Django root URL)."""
    return render(request, "home.html")


def _overdue_qs(qs=None):
    """Return a queryset filtered to tasks that are overdue."""
    qs = qs if qs is not None else Task.objects.all()
    return qs.filter(due_date__lt=date.today()).exclude(status='DONE')


class DashboardSummaryView(APIView):
    """GET /api/dashboard/ — top-level counts for the dashboard cards."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='IN_PROGRESS').count()
        completed_projects = Project.objects.filter(status='COMPLETED').count()

        total_tasks = Task.objects.count()
        todo_tasks = Task.objects.filter(status='TODO').count()
        in_progress_tasks = Task.objects.filter(status='IN_PROGRESS').count()
        done_tasks = Task.objects.filter(status='DONE').count()
        overdue_tasks = _overdue_qs().count()

        User = get_user_model()
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        # Keep the same keys the frontend's loadStats() looks for, plus extras.
        return Response({
            'projects': total_projects,
            'tasks': total_tasks,
            'todo': todo_tasks,
            'progress': in_progress_tasks,
            'done': done_tasks,
            # extras (safe to ignore on the frontend)
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'overdue': overdue_tasks,
            'total_users': total_users,
            'active_users': active_users,
        }, status=status.HTTP_200_OK)


class DashboardProjectsBreakdownView(APIView):
    """GET /api/dashboard/projects-breakdown/ — per-project rollup."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        breakdown = []
        for project in Project.objects.all():
            breakdown.append({
                'id': project.id,
                'name': project.name,
                'status': project.status,
                # call methods explicitly — they are not properties on Project
                'task_count': project.task_count(),
                'completed_task_count': project.completed_task_count(),
                'progress_percentage': project.progress_percentage(),
            })
        return Response(breakdown, status=status.HTTP_200_OK)


class DashboardTaskStatisticsView(APIView):
    """GET /api/dashboard/task-statistics/ — per-project task buckets."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        stats = []
        for project in Project.objects.all():
            tasks = project.tasks.all()
            stats.append({
                'project_id': project.id,
                'project_name': project.name,
                'total_tasks': tasks.count(),
                'todo': tasks.filter(status='TODO').count(),
                'in_progress': tasks.filter(status='IN_PROGRESS').count(),
                'done': tasks.filter(status='DONE').count(),
                'overdue': _overdue_qs(tasks).count(),
            })
        return Response(stats, status=status.HTTP_200_OK)


class DashboardUserTasksView(APIView):
 
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        tasks = user.assigned_tasks.all()
        return Response({
            'user_id': user.id,
            'username': user.username,
            'total_tasks': tasks.count(),
            'todo': tasks.filter(status='TODO').count(),
            'in_progress': tasks.filter(status='IN_PROGRESS').count(),
            'done': tasks.filter(status='DONE').count(),
            'overdue': _overdue_qs(tasks).count(),
        }, status=status.HTTP_200_OK)
