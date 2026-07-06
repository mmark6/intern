"""
Task serializers.

Fix: `projectId = serializers.IntegerField(source='project', ...)` was passing
the Project model instance to int(), which crashed. Use source='project_id'
so DRF reads the FK column value directly. Same fix applied to assignee alias.
"""
from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Task serializer."""

    # Display-only joined fields
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    assignee_email = serializers.EmailField(source='assignee.email', read_only=True)
    assignee_role = serializers.CharField(source='assignee.role.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    # Computed property on the model
    is_overdue = serializers.BooleanField(read_only=True)

    # camelCase aliases the frontend expects — pulled from FK *_id columns,
    # not from the Python attribute that returns a model instance.
    projectId = serializers.IntegerField(source='project_id', read_only=True)
    dueDate = serializers.DateField(source='due_date', read_only=True)

    # Input field: allow frontend to pass projectId (the FK integer)
    # which maps to the project FK for creation
    project_id = serializers.IntegerField(write_only=True, required=False)
    assignee_id = serializers.IntegerField(write_only=True, required=False)
    due_date = serializers.DateField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'project', 'project_name', 'projectId', 'project_id',
            'assignee', 'assignee_id', 'assignee_username', 'assignee_email', 'assignee_role',
            'status', 'priority',
            'due_date', 'dueDate',
            'estimated_hours', 'actual_hours',
            'is_overdue',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'project': {'required': False},
            'assignee': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        """If no assignee was given, default to the requesting user."""
        # Convert project_id input to project ForeignKey
        if 'project_id' in validated_data:
            from projects.models import Project
            project_pk = validated_data.pop('project_id')
            try:
                validated_data['project'] = Project.objects.get(pk=project_pk)
            except Project.DoesNotExist:
                raise serializers.ValidationError({'project': 'Project not found.'})

        # Convert assignee_id input to assignee ForeignKey
        if 'assignee_id' in validated_data:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assignee_pk = validated_data.pop('assignee_id')
            if assignee_pk:
                try:
                    validated_data['assignee'] = User.objects.get(pk=assignee_pk)
                except User.DoesNotExist:
                    raise serializers.ValidationError({'assignee': 'User not found.'})

        # Default assignee to requesting user if not provided
        if 'assignee' not in validated_data or validated_data['assignee'] is None:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                validated_data['assignee'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Handle updates with project_id conversion."""
        if 'project_id' in validated_data:
            from projects.models import Project
            project_pk = validated_data.pop('project_id')
            try:
                validated_data['project'] = Project.objects.get(pk=project_pk)
            except Project.DoesNotExist:
                raise serializers.ValidationError({'project': 'Project not found.'})
        return super().update(instance, validated_data)
