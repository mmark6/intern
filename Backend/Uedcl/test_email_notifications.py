"""
Simple test script to verify email notification functionality.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Uedcl.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from datetime import date, timedelta
from django.utils import timezone
from users.models import User
from projects.models import Project
from tasks.models import Task
from notifications.signals import notify_deadline, notify_task_created, notify_task_done


def test_email_notifications():
    """Test email notification system."""
    print("=" * 60)
    print("Testing Email Notification System")
    print("=" * 60)
    
    # Get or create a test user
    try:
        user = User.objects.get(username='testuser')
        created = False
        print(f"✓ Using existing test user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create(
            username='testuser',
            email='testuser@example.com',
            email_notifications_enabled=True,
            notify_before_days=3,
        )
        user.set_password('testpass123')
        user.save()
        created = True
        print(f"✓ Created test user: {user.username}")
    
    # Get or create a test project
    project, created = Project.objects.get_or_create(
        name='Test Project',
        defaults={
            'owner': user,
            'description': 'Test project for email notifications',
            'status': 'IN_PROGRESS',
        }
    )
    
    if created:
        print(f"✓ Created test project: {project.name}")
    else:
        print(f"✓ Using existing test project: {project.name}")
    
    # Test 1: Task due tomorrow
    print("\n" + "-" * 60)
    print("Test 1: Task due tomorrow")
    print("-" * 60)
    
    task1 = Task.objects.create(
        title='Test Task - Due Tomorrow',
        description='Testing email notification for task due tomorrow',
        project=project,
        assignee=user,
        due_date=timezone.now().date() + timedelta(days=1),
        status='IN_PROGRESS',
        priority='HIGH',
    )
    
    notify_deadline(task1)
    print(f"✓ Created task: {task1.title}")
    print(f"  Due date: {task1.due_date}")
    print(f"  Notification sent: Check email at {user.email}")
    
    # Test 2: Task due in 3 days
    print("\n" + "-" * 60)
    print("Test 2: Task due in 3 days")
    print("-" * 60)
    
    task2 = Task.objects.create(
        title='Test Task - Due in 3 Days',
        description='Testing email notification for task due in 3 days',
        project=project,
        assignee=user,
        due_date=timezone.now().date() + timedelta(days=3),
        status='TODO',
        priority='MEDIUM',
    )
    
    notify_deadline(task2)
    print(f"✓ Created task: {task2.title}")
    print(f"  Due date: {task2.due_date}")
    print(f"  Notification sent: Check email at {user.email}")
    
    # Test 3: Overdue task
    print("\n" + "-" * 60)
    print("Test 3: Overdue task")
    print("-" * 60)
    
    task3 = Task.objects.create(
        title='Test Task - Overdue',
        description='Testing email notification for overdue task',
        project=project,
        assignee=user,
        due_date=timezone.now().date() - timedelta(days=2),
        status='IN_PROGRESS',
        priority='CRITICAL',
    )
    
    notify_deadline(task3)
    print(f"✓ Created task: {task3.title}")
    print(f"  Due date: {task3.due_date}")
    print(f"  Notification sent: Check email at {user.email}")
    
    # Test 4: Task assignment email
    print("\n" + "-" * 60)
    print("Test 4: Task assignment email")
    print("-" * 60)
    
    task4 = Task.objects.create(
        title='Test Task - New Assignment',
        description='Testing email notification for new task assignment',
        project=project,
        assignee=user,
        due_date=timezone.now().date() + timedelta(days=7),
        status='TODO',
        priority='MEDIUM',
    )
    
    notify_task_created(task4)
    print(f"✓ Created task: {task4.title}")
    print(f"  Assignment email sent: Check email at {user.email}")
    
    # Test 5: Task completion email
    print("\n" + "-" * 60)
    print("Test 5: Task completion email")
    print("-" * 60)
    
    task5 = Task.objects.create(
        title='Test Task - Completion',
        description='Testing email notification for task completion',
        project=project,
        assignee=user,
        due_date=timezone.now().date() + timedelta(days=5),
        status='TODO',
        priority='LOW',
    )
    
    task5.status = 'DONE'
    task5.save()
    notify_task_done(task5)
    print(f"✓ Completed task: {task5.title}")
    print(f"  Completion email sent: Check email at {user.email}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Test user: {user.username} ({user.email})")
    print(f"Email notifications enabled: {user.email_notifications_enabled}")
    print(f"Notify before days: {user.notify_before_days}")
    print(f"\nCreated {5} test tasks")
    print("\nPlease check the email inbox for notifications:")
    print(f"  {user.email}")
    print("\nNote: If emails are not received, check:")
    print("  1. Email configuration in .env file")
    print("  2. Django console email backend (if in DEBUG mode)")
    print("  3. Spam/junk folder")
    print("=" * 60)


if __name__ == '__main__':
    test_email_notifications()