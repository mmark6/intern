from django.db import models
from django.contrib.auth import get_user_model


class Notification(models.Model):

    TYPE_CHOICES = [
        ('PROJECT_CREATED', 'Project Created'),
        ('PROJECT_DUE_SOON', 'Project Due Soon'),
        ('PROJECT_OVERDUE', 'Project Overdue'),
        ('TASK_CREATED', 'Task Created'),
        ('TASK_DONE', 'Task Completed'),
        ('TASK_DUE_SOON', 'Task Due Soon'),
        ('TASK_OVERDUE', 'Task Overdue'),
    ]

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Reference to the related object (optional)
    project_id = models.IntegerField(null=True, blank=True)
    task_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type}: {self.title}"