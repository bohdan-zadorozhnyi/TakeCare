from django.contrib import admin
from .models import Issue

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'date', 'is_resolved')
    list_filter = ('status', 'is_resolved', 'date')
    search_fields = ('user__name', 'title', 'message', 'admin_response')
    ordering = ('-date',)
    readonly_fields = ('date',)
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'date')
        }),
        ('Issue Details', {
            'fields': ('title', 'message', 'status', 'is_resolved', 'resolved_date')
        }),
        ('Admin Response', {
            'fields': ('admin_notes', 'admin_response')
        }),
    )
