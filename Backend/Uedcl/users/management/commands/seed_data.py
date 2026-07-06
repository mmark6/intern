from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from projects.models import Project
from tasks.models import Task
from users.models import Role
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with sample data...')

        # Create roles
        admin_role, created = Role.objects.get_or_create(
            name='ADMIN',
            defaults={'name': 'ADMIN'}
        )
        if created:
            self.stdout.write('Created ADMIN role')

        manager_role, created = Role.objects.get_or_create(
            name='MANAGER',
            defaults={'name': 'MANAGER'}
        )
        if created:
            self.stdout.write('Created MANAGER role')

        staff_role, created = Role.objects.get_or_create(
            name='STAFF',
            defaults={'name': 'STAFF'}
        )
        if created:
            self.stdout.write('Created STAFF role')

        # Create users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@uedcl.co.ug',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'role': admin_role,
            }
        )
        # Always set password to ensure older seeded DB rows remain loginable
        admin_user.email = admin_user.email or 'admin@uedcl.co.ug'
        admin_user.role = admin_role
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('Admin123!')
        admin_user.save()
        if created:
            self.stdout.write('Created admin user')
        else:
            self.stdout.write('Updated admin user role + reset password')

        manager_user, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@uedcl.co.ug',
                'first_name': 'Project',
                'last_name': 'Manager',
                'role': manager_role,
            }
        )
        manager_user.email = manager_user.email or 'manager@uedcl.co.ug'
        manager_user.role = manager_role
        manager_user.set_password('Manager123!')
        manager_user.save()
        if created:
            self.stdout.write('Created manager user')
        else:
            self.stdout.write('Updated manager user role + reset password')

        staff_user, created = User.objects.get_or_create(
            username='staff',
            defaults={
                'email': 'staff@uedcl.co.ug',
                'first_name': 'Staff',
                'last_name': 'Member',
                'role': staff_role,
            }
        )
        staff_user.email = staff_user.email or 'staff@uedcl.co.ug'
        staff_user.role = staff_role
        staff_user.set_password('Staff123!')
        staff_user.save()
        if created:
            self.stdout.write('Created staff user')
        else:
            self.stdout.write('Updated staff user role + reset password')

        # Create projects
        project1, created = Project.objects.get_or_create(
            name='Grid Maintenance',
            defaults={
                'description': 'Maintenance of electrical grid infrastructure',
                'owner': manager_user,
                'status': 'IN_PROGRESS',
                'priority': 'HIGH',
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=60),
            }
        )
        if created:
            self.stdout.write('Created project: Grid Maintenance')

        project2, created = Project.objects.get_or_create(
            name='Meter Replacement',
            defaults={
                'description': 'Replacement of old electricity meters',
                'owner': admin_user,
                'status': 'PLANNING',
                'priority': 'MEDIUM',
                'start_date': date.today() + timedelta(days=7),
                'end_date': date.today() + timedelta(days=90),
            }
        )
        if created:
            self.stdout.write('Created project: Meter Replacement')

        project3, created = Project.objects.get_or_create(
            name='Customer Service Portal',
            defaults={
                'description': 'Development of new customer service portal',
                'owner': manager_user,
                'status': 'COMPLETED',
                'priority': 'HIGH',
                'start_date': date.today() - timedelta(days=60),
                'end_date': date.today() - timedelta(days=10),
            }
        )
        if created:
            self.stdout.write('Created project: Customer Service Portal')

        # Create tasks
        task1, created = Task.objects.get_or_create(
            title='Inspect feeder line',
            defaults={
                'description': 'Inspect main feeder line for damages',
                'project': project1,
                'assignee': staff_user,
                'status': 'IN_PROGRESS',
                'priority': 'HIGH',
                'due_date': date.today() + timedelta(days=2),
            }
        )
        if created:
            self.stdout.write('Created task: Inspect feeder line')

        task2, created = Task.objects.get_or_create(
            title='Approve contractor list',
            defaults={
                'description': 'Review and approve contractor list for meter replacement',
                'project': project2,
                'assignee': manager_user,
                'status': 'TODO',
                'priority': 'MEDIUM',
                'due_date': date.today() + timedelta(days=5),
            }
        )
        if created:
            self.stdout.write('Created task: Approve contractor list')

        task3, created = Task.objects.get_or_create(
            title='Deploy portal update',
            defaults={
                'description': 'Deploy latest update to customer service portal',
                'project': project3,
                'assignee': admin_user,
                'status': 'DONE',
                'priority': 'HIGH',
                'due_date': date.today() - timedelta(days=8),
            }
        )
        if created:
            self.stdout.write('Created task: Deploy portal update')

        task4, created = Task.objects.get_or_create(
            title='Review safety protocols',
            defaults={
                'description': 'Review and update safety protocols for grid maintenance',
                'project': project1,
                'assignee': manager_user,
                'status': 'REVIEW',
                'priority': 'CRITICAL',
                'due_date': date.today() + timedelta(days=1),
            }
        )
        if created:
            self.stdout.write('Created task: Review safety protocols')

        task5, created = Task.objects.get_or_create(
            title='Order replacement meters',
            defaults={
                'description': 'Place order for new electricity meters',
                'project': project2,
                'assignee': staff_user,
                'status': 'BLOCKED',
                'priority': 'HIGH',
                'due_date': date.today() + timedelta(days=10),
            }
        )
        if created:
            self.stdout.write('Created task: Order replacement meters')

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully!'))
