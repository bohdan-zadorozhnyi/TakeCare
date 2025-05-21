from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_preview', 'receiver', 'notification_type', 'status', 'date', 'is_delivered', 'delivery_attempts')
    list_filter = ('notification_type', 'status', 'is_delivered', 'date')
    search_fields = ('receiver__email', 'receiver__username', 'message', 'related_object_id')
    readonly_fields = ('id', 'date', 'last_delivery_attempt', 'delivery_attempts', 'is_delivered')
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
        if obj and (obj.is_delivered or obj.delivery_attempts >= 3):
            return True
        return request.user.is_superuser
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('receiver',)
        return self.readonly_fields
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'receiver', 'message', 'date', 'type', 'status')
        }),
        ('Delivery Information', {
            'fields': ('is_delivered', 'delivery_attempts', 'last_delivery_attempt')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': ('sensitive_data',),
        }),
    )