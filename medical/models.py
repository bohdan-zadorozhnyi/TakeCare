from django.db import models
import uuid

class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('accounts.PatientProfile', on_delete=models.CASCADE, related_name='medical_records_as_patient')
    doctor = models.ForeignKey('accounts.DoctorProfile', on_delete=models.CASCADE, related_name='medical_records_as_doctor')
    date = models.DateTimeField(auto_now_add=True)
    condition = models.TextField()
    treatment = models.TextField()
    notes = models.TextField()
    file = models.FileField(upload_to="medical_records/")

    def __str__(self):
        return f"Medical Record for {self.patient.user.name}"