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
    patient = models.ForeignKey(User, limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    issue_date = models.DateField()
    expiration_date = models.DateField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Referral for {self.patient.name} to {self.get_specialist_type_display()}"
