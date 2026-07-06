"""
Comment serializers.
"""
from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer."""
    author_username = serializers.CharField(source='author.username', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'task', 'task_title', 'author', 'author_username',
            'content', 'created_at', 'updated_at'
        ]