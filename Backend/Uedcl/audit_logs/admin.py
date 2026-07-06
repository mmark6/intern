from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'action', 'target_type', 'target_name', 'ip_address', 'timestamp']
    list_filter = ['action', 'target_type', 'timestamp']
    search_fields = ['username', 'target_name', 'ip_address']
    readonly_fields = ['user', 'username', 'action', 'target_type', 'target_id', 'target_name', 'description', 'ip_address', 'user_agent', 'timestamp']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False