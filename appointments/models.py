from django.db import models
from accounts.models import User
from referrals.models import Referral, DoctorCategory
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()


class AppointmentStatus(models.TextChoices):
    AVAILABLE = "Available"
    CANCELLED = "Cancelled"
    BOOKED = "Booked"

class AppointmentSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(User, related_name="appointments_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    duration = models.IntegerField()
    status = models.CharField(choices=AppointmentStatus.choices)
    referal_type = models.CharField(choices=DoctorCategory.choices, null=True, blank=True)
    
    def __str__(self):
        return f"Appointment with Dr. {self.doctor.name} on {self.date}"
        
    def get_referal_type_display_safe(self):
        """Return the display value of referal_type or None if not set"""
        if self.referal_type:
            return dict(DoctorCategory.choices).get(self.referal_type, "Unknown")
        return None

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, related_name="appointments_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    appointment_slot = models.ForeignKey(AppointmentSlot, on_delete=models.CASCADE)
    referral = models.ForeignKey(Referral, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return f"Appointment with {self.appointment_slot.doctor} on {self.appointment_slot.date}"


