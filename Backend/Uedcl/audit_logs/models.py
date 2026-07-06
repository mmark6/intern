from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """Audit log model to track user activities."""

    ACTION_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('STATUS', 'Status Change'),
    ]

    TARGET_TYPES = [
        ('USER', 'User'),
        ('PROJECT', 'Project'),
        ('TASK', 'Task'),
        ('COMMENT', 'Comment'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    target_id = models.IntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.CharField(max_length=50, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f"{self.user} - {self.action} {self.target_type} at {self.timestamp}"