from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'created_at', 'project_id', 'task_id']
        read_only_fields = ['id', 'type', 'title', 'message', 'created_at', 'project_id', 'task_id']