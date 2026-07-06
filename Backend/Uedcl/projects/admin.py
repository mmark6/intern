from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'priority', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'priority', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    ordering = ('-created_at',)
    readonly_fields = ('task_count', 'completed_task_count', 'progress_percentage')
