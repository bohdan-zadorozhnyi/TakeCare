from django.contrib import admin
from .models import Appointment, AppointmentSlot

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'get_doctor', 'get_date', 'get_status']
    
    def get_doctor(self, obj):
        return obj.appointment_slot.doctor
    get_doctor.short_description = 'Doctor'
    
    def get_date(self, obj):
        return obj.appointment_slot.date
    get_date.short_description = 'Date'
    
    def get_status(self, obj):
        return obj.appointment_slot.status
    get_status.short_description = 'Status'

@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'duration', 'status']