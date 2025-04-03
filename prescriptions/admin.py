from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'medication_name', 'issue_date', 'expiration_date')
    list_filter = ('issue_date', 'expiration_date')
    search_fields = ('patient__name', 'doctor__name', 'medication_name')
    ordering = ('-issue_date',)