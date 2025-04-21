from django.db import models
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
    patient = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return f"Referral for {self.patient.user.name} to {self.get_specialist_type_display()}"
