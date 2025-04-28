from django.contrib import admin
from .models import Prescription, PrescriptionMedication

class PrescriptionMedicationInline(admin.TabularInline):
    model = PrescriptionMedication
    extra = 1

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'issue_date', 'expiration_date')
    list_filter = ('issue_date', 'expiration_date')
    search_fields = ('patient__name', 'doctor__name')
    ordering = ('-issue_date',)
    inlines = [PrescriptionMedicationInline]