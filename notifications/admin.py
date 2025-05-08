from django.contrib import admin
from .models import Notification, TechnicalIssueReport, NotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'created_at', 'subject', 'notification_type', 'status')
    list_filter = ('created_at', 'notification_type', 'status', 'severity')
    search_fields = ('receiver__name', '_message', 'subject')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'delivered_at', 'read_at')

@admin.register(TechnicalIssueReport)
class TechnicalIssueReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'created_at', 'severity', 'resolved')
    list_filter = ('severity', 'resolved', 'created_at')
    search_fields = ('reporter__name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'resolved_at')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'timestamp', 'action')
    list_filter = ('action', 'timestamp')
    search_fields = ('notification__subject', 'details')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)