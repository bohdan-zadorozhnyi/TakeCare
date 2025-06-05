from django.db import models
from appointments.models import Appointment
from referrals.models import DoctorCategory

class SpecializationPrice(models.Model):
    specialization = models.CharField(
        max_length=50,
        choices=DoctorCategory.choices,
        unique=True
    )
    price = models.IntegerField(default=10000)

    def __str__(self):
        return f"{self.get_specialization_display()}: {self.price} cents"

    @property
    def formatted_price(self):
        return f"{self.price / 100:.2f}"

class Payment(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    stripe_payment_session_id = models.CharField(max_length=255)
    price = models.IntegerField(default=0) #cents
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=20, default='pending')  # pending, succeeded, failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.appointment}"
