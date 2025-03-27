from django.db import models
import uuid

# Create your models here.
# Category enum
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

# Status enum
class AppointmentStatus(models.TextChoices):
    CANCELLED = "Cancelled"
    BOOKED = "Booked"
    FINISHED = "Finished"

# Abstract User Model
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    personal_id = models.CharField(max_length=50, unique=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Doctor(User):
    category = models.CharField(max_length=50, choices=DoctorCategory.choices)
    license_number = models.CharField(max_length=100, unique=True)
    work_address = models.TextField()

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"

class Patient(User):
    medical_history = models.ManyToManyField("MedicalRecord", blank=True)
    appointments = models.ManyToManyField("Appointment", blank=True)
    prescriptions = models.ManyToManyField("Prescription", blank=True)
    referrals = models.ManyToManyField("Referral", blank=True)

    def __str__(self):
        return f"Patient: {self.name}"

class Administrator(User):
    def __str__(self):
        return f"Admin: {self.name}"

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.receiver.name}"

class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    referral = models.UUIDField(null=True, blank=True)  # Assuming a UUID reference
    description = models.TextField()
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices)

    def __str__(self):
        return f"Appointment with {self.doctor} on {self.date}"

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    notes = models.TextField()
    issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return f"Prescription for {self.patient.name}"

class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    specialist_type = models.CharField(max_length=50, choices=DoctorCategory.choices)
    issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return f"Referral for {self.patient.name} to {self.get_specialist_type_display()}"

class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    condition = models.TextField()
    treatment = models.TextField()
    notes = models.TextField()
    file = models.FileField(upload_to="medical_records/")

    def __str__(self):
        return f"Medical Record for {self.patient.name}"

class Issue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Issue reported by {self.user.name}"