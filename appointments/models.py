from django.db import models
from accounts.models import User
import uuid


class AppointmentStatus(models.TextChoices):
    CANCELLED = "Cancelled"
    BOOKED = "Booked"
    FINISHED = "Finished"


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(User, related_name="appointments_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, related_name="appointments_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    referral = models.UUIDField(null=True, blank=True)  # Can be ForeignKey later
    description = models.TextField()
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices)

    def __str__(self):
        return f"Appointment with {self.doctor.name} on {self.date}"
