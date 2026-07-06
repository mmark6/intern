from rest_framework import serializers
from .models import Project
from users.validators import sanitize_string, validate_field_length


class ProjectSerializer(serializers.ModelSerializer):
   
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_role = serializers.CharField(source='owner.role.name', read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_task_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description',
            'owner', 'owner_username', 'owner_role',
            'status', 'priority',
            'start_date', 'end_date',
            'task_count', 'completed_task_count', 'progress_percentage',
            'created_at',
        ]
        extra_kwargs = {
            'name': {'required': True, 'min_length': 3, 'max_length': 200},
            'description': {'required': False, 'max_length': 5000},
            # `owner` is writeable on create — the view supplies it from request.user.
            # It is the FK PK, not a username string.
            'owner': {'required': False, 'allow_null': True},
        }


    def get_task_count(self, obj):
        return obj.task_count()

    def get_completed_task_count(self, obj):
        return obj.completed_task_count()

    def get_progress_percentage(self, obj):
        return obj.progress_percentage()



    def validate_name(self, value):
        value = sanitize_string(value, max_length=200)
        validate_field_length(value, min_length=3, max_length=200)
        return value

    def validate_description(self, value):
        if value:
            value = sanitize_string(value, max_length=5000)
            validate_field_length(value, max_length=5000)
        return value

    def validate_status(self, value):
        valid = ['PLANNING', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
        if value not in valid:
            raise serializers.ValidationError(f"Invalid status. Choose from {valid}")
        return value

    def validate_priority(self, value):
        valid = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if value not in valid:
            raise serializers.ValidationError(f"Invalid priority. Choose from {valid}")
        return value
