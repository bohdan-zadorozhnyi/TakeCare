from django.db import models
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(User, related_name="prescriptions_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, related_name="prescriptions_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    notes = models.TextField(blank=False, null=False)
    issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return f"Prescription for {self.patient.name}"

class PrescriptionMedication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, related_name='medications', on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"
