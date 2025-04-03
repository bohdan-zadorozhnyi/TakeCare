from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'date')
    list_filter = ('date',)
    search_fields = ('receiver__name', 'message')
    ordering = ('-date',)