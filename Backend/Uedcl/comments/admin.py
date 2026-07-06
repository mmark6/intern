from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at', 'updated_at')
    search_fields = ('task__title', 'author__username', 'content')
    ordering = ('-created_at',)
