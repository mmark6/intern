from django.db import models

# Create your models here.
"""
Comment models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from tasks.models import Task


class Comment(models.Model):
    """Comment model for task discussions."""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"