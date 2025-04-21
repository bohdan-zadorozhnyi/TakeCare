from django.contrib import admin
from .models import MedicalRecord

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date')
    list_filter = ('date',)
    search_fields = ('patient__user__name', 'doctor__user__name', 'condition')
    ordering = ('-date',)