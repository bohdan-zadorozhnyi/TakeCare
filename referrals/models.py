from django.db import models
import uuid

class DoctorCategory(models.TextChoices):
    DERMATOLOGIST = 'DERMATOLOGIST', 'Dermatologist'
    NEUROLOGIST = 'NEUROLOGIST', 'Neurologist'
    PEDIATRICIAN = 'PEDIATRICIAN', 'Pediatrician'
    CARDIOLOGIST = 'CARDIOLOGIST', 'Cardiologist'
    GASTROENTEROLOGIST = 'GASTROENTEROLOGIST', 'Gastroenterologist'
    OPHTHALMOLOGIST = 'OPHTHALMOLOGIST', 'Ophthalmologist'
    ENDOCRINOLOGIST = 'ENDOCRINOLOGIST', 'Endocrinologist'
    FAMILY_MEDICINE = 'FAMILY_MEDICINE', 'Family Medicine'
    GENERAL_SURGERY = 'GENERAL_SURGERY', 'General Surgery'
    NEPHROLOGIST = 'NEPHROLOGIST', 'Nephrologist'


class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('accounts.User', limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    issue_date = models.DateField()
    expiration_date = models.DateField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Referral for {self.patient.name} to {self.get_specialist_type_display()}"
