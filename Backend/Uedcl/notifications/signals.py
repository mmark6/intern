from django.db.models.signals import post_save
from django.dispatch import receiver
from projects.models import Project
from tasks.models import Task
from .models import Notification


def create_notification(user, notification_type, title, message, project_id=None, task_id=None):
    if user and user.is_authenticated:
        Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            project_id=project_id,
            task_id=task_id,
        )


def notify_project_created(project):
    owner_name = project.owner.username or f"{project.owner.first_name} {project.owner.last_name}"
    title = f"New Project: {project.name}"
    message = f"A new project '{project.name}' has been created by {owner_name}."
    create_notification(
        user=project.owner,
        notification_type='PROJECT_CREATED',
        title=title,
        message=message,
        project_id=project.id,
    )


def notify_project_deadline(project):
    """Notify project owner of project deadline."""
    if not project.owner or not project.end_date or project.status == 'COMPLETED':
        return

    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    end_date = project.end_date

    if end_date < today:
        title = f'Project Overdue: {project.name}'
        message = f'Your project "{project.name}" was due on {end_date}.'
        notification_type = 'PROJECT_OVERDUE'
    elif end_date <= today + timedelta(days=3):
        days_left = (end_date - today).days
        title = f'Project Due Soon: {project.name}'
        if days_left == 0:
            message = f'Your project "{project.name}" is due today.'
        elif days_left == 1:
            message = f'Your project "{project.name}" is due tomorrow.'
        else:
            message = f'Your project "{project.name}" is due in {days_left} days.'
        notification_type = 'PROJECT_DUE_SOON'
    else:
        return  # Not within notification window

    create_notification(
        user=project.owner,
        notification_type=notification_type,
        title=title,
        message=message,
        project_id=project.id,
    )


def notify_task_created(task):
    """Create notification when a task is created."""
    from .email_utils import send_task_assignment_email
    
    # Notify the assignee if there's one
    if task.assignee:
        title = f"New Task Assigned: {task.title}"
        message = f"You have been assigned to task '{task.title}' in project '{task.project.name}'."
        create_notification(
            user=task.assignee,
            notification_type='TASK_CREATED',
            title=title,
            message=message,
            project_id=task.project_id,
            task_id=task.id,
        )
        # Send email notification
        send_task_assignment_email(task.assignee, task)
    else:
        # Notify the project owner
        title = f"New Task: {task.title}"
        message = f"A new task '{task.title}' has been created in project '{task.project.name}'."
        create_notification(
            user=task.project.owner,
            notification_type='TASK_CREATED',
            title=title,
            message=message,
            project_id=task.project_id,
            task_id=task.id,
        )


def notify_task_done(task):
    from .email_utils import send_task_completion_email
    
    title = f"Task Completed: {task.title}"
    message = f"Task '{task.title}' in project '{task.project.name}' has been marked as done."
    create_notification(
        user=task.project.owner,
        notification_type='TASK_DONE',
        title=title,
        message=message,
        project_id=task.project_id,
        task_id=task.id,
    )

    if task.assignee and task.assignee != task.project.owner:
        title = f"Your Task Completed: {task.title}"
        message = f"Your task '{task.title}' has been marked as done."
        create_notification(
            user=task.assignee,
            notification_type='TASK_DONE',
            title=title,
            message=message,
            project_id=task.project_id,
            task_id=task.id,
        )
        # Send email notification to assignee
        send_task_completion_email(task.assignee, task)


def notify_deadline(task, old_due_date=None):
    """Notify assignee of task deadline changes."""
    from .email_utils import send_deadline_notification_email
    
    if not task.assignee or not task.due_date or task.status == 'DONE':
        return

    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    due_date = task.due_date

    # New task with due date, or due date changed
    if due_date <= today:
        # Already overdue or due today
        title = f"Task Due Today: {task.title}"
        message = f"Your task '{task.title}' is due {'today' if due_date == today else 'as of today'}."
        days_until_due = (due_date - today).days
        is_overdue = days_until_due < 0
    elif due_date <= today + timedelta(days=1):
        title = f"Task Due Tomorrow: {task.title}"
        message = f"Your task '{task.title}' is due tomorrow ({due_date})."
        days_until_due = 1
        is_overdue = False
    elif due_date <= today + timedelta(days=3):
        days_left = (due_date - today).days
        title = f"Task Due Soon: {task.title}"
        message = f"Your task '{task.title}' is due in {days_left} days ({due_date})."
        days_until_due = days_left
        is_overdue = False
    else:
        return  # Not within notification window

    create_notification(
        user=task.assignee,
        notification_type='TASK_DUE_SOON',
        title=title,
        message=message,
        project_id=task.project_id,
        task_id=task.id,
    )
    
    # Send email notification
    send_deadline_notification_email(task.assignee, task, days_until_due, is_overdue)
