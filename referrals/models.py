from django.db import models
import uuid
# Remove direct user model import that creates circular dependency
# from django.contrib.auth import get_user_model
# User = get_user_model()

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
    # Use string references to break circular dependency
    issuing_doctor = models.ForeignKey('accounts.User', related_name="referrals_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE, null=True)
    patient = models.ForeignKey('accounts.User', related_name="referrals_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    notes = models.TextField(blank=True, null=True)
    issue_date = models.DateField()
    expiration_date = models.DateField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Referral for {self.patient.name} to {self.get_specialist_type_display()}"

    class Meta:
        permissions = [
            ("list_referral", "Can list referrals"),
            ("search_referral", "Can search referrals"),
        ]

class ReferralDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referral = models.ForeignKey(Referral, related_name='details', on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent')
    ], default='MEDIUM')
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Details for {self.referral.get_specialist_type_display()} referral"
