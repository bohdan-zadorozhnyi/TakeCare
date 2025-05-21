from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import Payment

@receiver(post_save, sender=Appointment)
def create_payment_for_appointment(sender, instance, created, **kwargs):
    if created:
        Payment.objects.create(
            appointment=instance,
            price=10000,
            currency='pln',
            status='pending',
            stripe_payment_session_id=''
        )