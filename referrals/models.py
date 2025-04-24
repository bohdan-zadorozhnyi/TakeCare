from django.db import models
from accounts.models import User
import uuid

class DoctorCategory(models.TextChoices):
    DERMATOLOGIST = "Dermatologist"
    NEUROLOGIST = "Neurologist"
    PEDIATRICIAN = "Pediatrician"
    CARDIOLOGIST = "Cardiologist"
    GASTROENTEROLOGIST = "Gastroenterologist"
    OPHTHALMOLOGIST = "Ophthalmologist"
    ENDOCRINOLOGIST = "Endocrinologist"
    FAMILY_MEDICINE = "Family medicine"
    GENERAL_SURGERY = "General surgery"
    NEPHROLOGIST = "Nephrologist"


class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, related_name="referrals_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    referring_doctor = models.ForeignKey(User, related_name="referrals_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE, null=True, blank=True)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    description = models.TextField(blank=True, null=True)
    issue_date = models.DateField()
    expiration_date = models.DateField()
    is_used = models.BooleanField(default=False)
    expiry_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"Referral for {self.patient.name} to {self.get_specialist_type_display()}"
