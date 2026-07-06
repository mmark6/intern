from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import Role, User


class LoginAppTests(APITestCase):
    def setUp(self):
        self.role = Role.objects.create(name='MEMBER')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.role = self.role
        self.user.save()

    def test_register(self):
        url = reverse('login-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password2': 'NewPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

    def test_login(self):
        url = reverse('login-login')
        data = {'username': 'testuser', 'password': 'TestPass123!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data)

    def test_me_requires_authentication(self):
        url = reverse('login-me')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        DEBUG=False,
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.gmail.com',
        EMAIL_PORT=587,
        EMAIL_USE_TLS=True,
        EMAIL_HOST_USER='user@example.com',
        EMAIL_HOST_PASSWORD='secret',
        DEFAULT_FROM_EMAIL='user@example.com',
    )
    def test_password_reset_request_recovers_when_email_send_fails(self):
        url = reverse('password-reset-request')
        with patch('login.views.send_mail', side_effect=Exception('SMTP auth failed')):
            response = self.client.post(url, {'email': 'test@example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('code', response.data)
