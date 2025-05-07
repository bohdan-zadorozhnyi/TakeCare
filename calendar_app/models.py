from django.db import models
from appointments.models import Appointment, AppointmentSlot
from accounts.models import User

class CalendarSettings(models.Model):
    """Model to store user-specific calendar settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_settings')
    default_view = models.CharField(
        max_length=20, 
        choices=[('month', 'Month'), ('week', 'Week'), ('day', 'Day')],
        default='month'
    )
    reminder_before = models.IntegerField(default=24)  # Hours before appointment
    show_past_appointments = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Calendar settings for {self.user.name}"

class AppointmentNote(models.Model):
    """Model to store notes associated with appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Note for {self.appointment} by {self.created_by.name}"

class AppointmentReminder(models.Model):
    """Model to store custom reminders for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reminder_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reminder for {self.appointment} at {self.reminder_time}"
