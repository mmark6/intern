from django.db import models
from django.db.models import Count, Q
from users.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='PLANNING')
    priority = models.CharField(max_length=20, default='LOW')
    created_at = models.DateTimeField(auto_now_add=True)

    # Add start/end date fields (optional but recommended)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def task_count(self):
        
        return self.tasks.count()

    def completed_task_count(self):

        return self.tasks.filter(status='COMPLETED').count()

    def progress_percentage(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status='COMPLETED').count()
        return round((completed / total) * 100, 1)