from django.db import models
from appointments.models import Appointment

class Payment(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    stripe_payment_session_id = models.CharField(max_length=255)
    price = models.IntegerField(default=0) #cents
    currency = models.CharField(max_length=10, default='usd')
    status = models.CharField(max_length=20, default='pending')  # pending, succeeded, failed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.appointment}"
