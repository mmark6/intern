from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Role, User
from audit_logs.models import AuditLog


class AuditLogAccessTests(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='ADMIN')
        self.member_role = Role.objects.create(name='MEMBER')

        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.admin_user.role = self.admin_role
        self.admin_user.save()

        self.member_user = User.objects.create_user(
            username='memberuser',
            email='member@example.com',
            password='MemberPass123!'
        )
        self.member_user.role = self.member_role
        self.member_user.save()

        AuditLog.objects.create(
            user=self.admin_user,
            username=self.admin_user.username,
            action='LOGIN',
            target_type='USER',
            target_id=self.admin_user.id,
            target_name=self.admin_user.username,
            description='Admin login event',
            ip_address='127.0.0.1',
        )

    def test_admin_can_view_audit_logs(self):
        url = reverse('audit-log-list')
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data['logs'][0]['username'], 'adminuser')

    def test_member_cannot_view_audit_logs(self):
        url = reverse('audit-log-list')
        self.client.force_authenticate(user=self.member_user)

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_view_audit_logs(self):
        url = reverse('audit-log-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
