from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_preview', 'receiver', 'notification_type', 'status', 'date', 'delivered_at', 'retry_count')
    list_filter = ('notification_type', 'status', 'date')
    search_fields = ('receiver__email', 'receiver__username', 'message', 'object_id')
    readonly_fields = ('id', 'date', 'delivered_at', 'retry_count')
    ordering = ('-date',)
    list_per_page = 25
    
    def message_preview(self, obj):
        """Truncate long messages for display in admin list view"""
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    message_preview.short_description = 'Message'
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion of notifications that have been delivered or failed
        if obj and (obj.delivered_at or obj.retry_count >= 3):
            return True
        return request.user.is_superuser
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('receiver',)
        return self.readonly_fields
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'receiver', 'subject', 'message', 'date', 'notification_type', 'status')
        }),
        ('Delivery Information', {
            'fields': ('delivered_at', 'retry_count', 'max_retries')
        }),
        ('Related Object', {
            'fields': ('object_id',)
        }),
        ('Additional Details', {
            'classes': ('collapse',),
            'fields': ('severity', 'is_resolved', 'resolved_at'),
        }),
    )