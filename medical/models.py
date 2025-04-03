from django.db import models
from accounts.models import User
import uuid

class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, related_name="medical_records_as_patient", limit_choices_to={'role': 'PATIENT'}, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, related_name="medical_records_as_doctor", limit_choices_to={'role': 'DOCTOR'}, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    condition = models.TextField()
    treatment = models.TextField()
    notes = models.TextField()
    file = models.FileField(upload_to="medical_records/")

    def __str__(self):
        return f"Medical Record for {self.patient.name}"