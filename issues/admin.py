from django.contrib import admin
from .models import Issue

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_resolved', 'date')
    list_filter = ('is_resolved', 'date')
    search_fields = ('user__name', 'message')
    ordering = ('-date',)
