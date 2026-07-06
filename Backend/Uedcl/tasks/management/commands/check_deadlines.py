from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from notifications.models import Notification
from users.models import User


class Command(BaseCommand):
    help = 'Check task deadlines and create notifications for upcoming/overdue tasks'

    def handle(self, *args, **options):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        three_days = today + timedelta(days=3)

        tasks = Task.objects.filter(
            assignee__isnull=False,
            status__ne='DONE'
        ).select_related('assignee', 'project')

        notified_count = 0

        for task in tasks:
            if not task.due_date:
                continue

            due_date = task.due_date
            assignee = task.assignee

            # Skip if no assignee
            if not assignee:
                continue

            # Check if overdue (due date is in the past and not DONE)
            if due_date < today:
                # Check if notification already exists for overdue
                existing_overdue = Notification.objects.filter(
                    user=assignee,
                    task_id=task.id,
                    type='TASK_OVERDUE'
                ).exists()

                if not existing_overdue:
                    Notification.objects.create(
                        user=assignee,
                        type='TASK_OVERDUE',
                        title=f'Overdue Task: {task.title}',
                        message=f'Your task "{task.title}" was due on {task.due_date}. Please update the status or request an extension.',
                        project_id=task.project_id,
                        task_id=task.id
                    )
                    notified_count += 1
                    self.stdout.write(f'Notified {assignee.username}: Overdue - {task.title}')

            # Check if due tomorrow
            elif due_date == tomorrow:
                existing_tomorrow = Notification.objects.filter(
                    user=assignee,
                    task_id=task.id,
                    type='TASK_DUE_SOON'
                ).exists()

                if not existing_tomorrow:
                    Notification.objects.create(
                        user=assignee,
                        type='TASK_DUE_SOON',
                        title=f'Task Due Tomorrow: {task.title}',
                        message=f'Your task "{task.title}" is due tomorrow ({task.due_date}). Please complete it on time.',
                        project_id=task.project_id,
                        task_id=task.id
                    )
                    notified_count += 1
                    self.stdout.write(f'Notified {assignee.username}: Due tomorrow - {task.title}')

            # Check if due within 3 days
            elif due_date <= three_days and due_date > tomorrow:
                existing_soon = Notification.objects.filter(
                    user=assignee,
                    task_id=task.id,
                    type='TASK_DUE_SOON'
                ).exists()

                if not existing_soon:
                    days_left = (due_date - today).days
                    Notification.objects.create(
                        user=assignee,
                        type='TASK_DUE_SOON',
                        title=f'Task Due Soon: {task.title}',
                        message=f'Your task "{task.title}" is due in {days_left} days ({task.due_date}).',
                        project_id=task.project_id,
                        task_id=task.id
                    )
                    notified_count += 1
                    self.stdout.write(f'Notified {assignee.username}: Due in {days_left} days - {task.title}')

        self.stdout.write(self.style.SUCCESS(f'Created {notified_count} deadline notifications'))