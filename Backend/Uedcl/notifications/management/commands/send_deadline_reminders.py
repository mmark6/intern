"""
Management command to send deadline reminder emails for tasks.
This command should be run periodically (e.g., daily) via cron or task scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from users.models import User
from notifications.email_utils import send_deadline_notification_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send email reminders for upcoming and overdue task deadlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Override the notification days for all users (ignores user preferences)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails (for testing)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        override_days = options['days']
        
        today = timezone.now().date()
        
        # Get all active tasks with due dates that are not done
        tasks = Task.objects.filter(
            due_date__isnull=False,
            status__in=['TODO', 'IN_PROGRESS', 'REVIEW', 'BLOCKED']
        ).select_related('assignee', 'project', 'project__owner')
        
        self.stdout.write(f"Found {tasks.count()} tasks to check")
        
        emails_sent = 0
        emails_failed = 0
        tasks_skipped = 0
        
        for task in tasks:
            # Skip if no assignee
            if not task.assignee:
                tasks_skipped += 1
                continue
            
            # Check if user has email notifications enabled
            if not task.assignee.email_notifications_enabled:
                tasks_skipped += 1
                continue
            
            # Calculate days until due
            days_until_due = (task.due_date - today).days
            
            # Determine notification window based on user preference or override
            notify_days = override_days if override_days is not None else task.assignee.notify_before_days
            
            # Check if we should send notification
            should_notify = False
            is_overdue = False
            
            if days_until_due < 0:
                # Overdue - always notify
                should_notify = True
                is_overdue = True
            elif days_until_due <= notify_days:
                # Due within notification window
                should_notify = True
                is_overdue = False
            
            if should_notify:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would send email to {task.assignee.email} "
                        f"for task '{task.title}' (due in {days_until_due} days)"
                    )
                    emails_sent += 1
                else:
                    # Send the email
                    success = send_deadline_notification_email(
                        user=task.assignee,
                        task=task,
                        days_until_due=days_until_due,
                        is_overdue=is_overdue
                    )
                    
                    if success:
                        emails_sent += 1
                        self.stdout.write(
                            f"✓ Sent email to {task.assignee.email} for task '{task.title}'"
                        )
                    else:
                        emails_failed += 1
                        self.stdout.write(
                            f"✗ Failed to send email to {task.assignee.email} for task '{task.title}'"
                        )
            else:
                tasks_skipped += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"Summary:"))
        self.stdout.write(self.style.SUCCESS(f"  Emails sent: {emails_sent}"))
        self.stdout.write(self.style.SUCCESS(f"  Emails failed: {emails_failed}"))
        self.stdout.write(self.style.SUCCESS(f"  Tasks skipped: {tasks_skipped}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a DRY RUN - no emails were actually sent"))
        
        logger.info(
            f"Deadline reminder command completed: {emails_sent} sent, "
            f"{emails_failed} failed, {tasks_skipped} skipped"
        )