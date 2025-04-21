from django.db import models
import uuid

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('accounts.DoctorProfile', related_name="prescriptions_as_doctor", on_delete=models.CASCADE)
    patient = models.ForeignKey('accounts.PatientProfile', related_name="prescriptions_as_patient", on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    notes = models.TextField()
    issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return f"Prescription for {self.patient.user.name}"