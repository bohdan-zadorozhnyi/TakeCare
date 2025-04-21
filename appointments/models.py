from django.db import models
from accounts.models import User
from referrals.models import Referral
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()


class AppointmentStatus(models.TextChoices):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"
    CANCELLED = "Cancelled"
    BOOKED = "Booked"
    FINISHED = "Finished"

class AppointmentSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('accounts.DoctorProfile', related_name="appointments_as_doctor", on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    duration = models.IntegerField()
    status = models.CharField(choices=AppointmentStatus.choices)

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('accounts.PatientProfile', related_name="appointments_as_patient", on_delete=models.CASCADE)
    appointment_slot = models.ForeignKey(AppointmentSlot, on_delete=models.CASCADE)
    referral = models.ForeignKey(Referral, on_delete=models.PROTECT)

    def __str__(self):
        return f"Appointment with {self.appointment_slot.doctor.user} on {self.appointment_slot.date}"


