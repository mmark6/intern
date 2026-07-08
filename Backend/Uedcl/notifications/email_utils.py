"""
Email utility functions for sending notifications.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_deadline_notification_email(user, task, days_until_due, is_overdue=False):
    """
    Send email notification for task deadline.
    
    Args:
        user: User instance (task assignee)
        task: Task instance
        days_until_due: Number of days until due date (negative if overdue)
        is_overdue: Boolean indicating if task is overdue
    """
    if not user.email_notifications_enabled or not user.email:
        return False
    
    try:
        # Determine email subject and context
        if is_overdue:
            subject = f" Task Overdue: {task.title}"
            if days_until_due == 0:
                deadline_text = "is due today"
            elif days_until_due == -1:
                deadline_text = "was due yesterday"
            else:
                deadline_text = f"is {abs(days_until_due)} day(s) overdue"
        elif days_until_due == 0:
            subject = f" Task Due Today: {task.title}"
            deadline_text = "is due today"
        elif days_until_due == 1:
            subject = f" Task Due Tomorrow: {task.title}"
            deadline_text = "is due tomorrow"
        else:
            subject = f" Task Due Soon: {task.title}"
            deadline_text = f"is due in {days_until_due} days"
        
        # Email context
        context = {
            'user': user,
            'task': task,
            'project': task.project,
            'days_until_due': days_until_due,
            'deadline_text': deadline_text,
            'is_overdue': is_overdue,
            'task_url': f"{settings.FRONTEND_URL}/tasks/{task.id}" if hasattr(settings, 'FRONTEND_URL') else None,
        }
        
        # Render email body
        html_message = render_to_string('emails/task_deadline_notification.html', context)
        plain_message = render_to_string('emails/task_deadline_notification.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Deadline notification email sent to {user.email} for task '{task.title}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send deadline notification email to {user.email}: {str(e)}")
        return False


def send_task_assignment_email(user, task):
    """
    Send email notification when a task is assigned to a user.
    
    Args:
        user: User instance (assignee)
        task: Task instance
    """
    if not user.email_notifications_enabled or not user.email:
        return False
    
    try:
        subject = f" New Task Assigned: {task.title}"
        
        context = {
            'user': user,
            'task': task,
            'project': task.project,
            'task_url': f"{settings.FRONTEND_URL}/tasks/{task.id}" if hasattr(settings, 'FRONTEND_URL') else None,
        }
        
        html_message = render_to_string('emails/task_assignment.html', context)
        plain_message = render_to_string('emails/task_assignment.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Task assignment email sent to {user.email} for task '{task.title}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send task assignment email to {user.email}: {str(e)}")
        return False


def send_task_completion_email(user, task):
    """
    Send email notification when a task is marked as done.
    
    Args:
        user: User instance (task owner or assignee)
        task: Task instance
    """
    if not user.email_notifications_enabled or not user.email:
        return False
    
    try:
        subject = f"Task Completed: {task.title}"
        
        context = {
            'user': user,
            'task': task,
            'project': task.project,
            'task_url': f"{settings.FRONTEND_URL}/tasks/{task.id}" if hasattr(settings, 'FRONTEND_URL') else None,
        }
        
        html_message = render_to_string('emails/task_completion.html', context)
        plain_message = render_to_string('emails/task_completion.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Task completion email sent to {user.email} for task '{task.title}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send task completion email to {user.email}: {str(e)}")
        return False