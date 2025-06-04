from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from .models import Payment, SpecializationPrice
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from referrals.models import DoctorCategory

@receiver(post_migrate)
def create_specialization_prices(sender, **kwargs):
    if sender.name != 'payments':
        return

    for spec_value, spec_label in DoctorCategory.choices:
        SpecializationPrice.objects.get_or_create(
            specialization=spec_value,
            defaults={'price': 10000}
        )


@receiver(post_save, sender=Appointment)
def create_payment_for_appointment(sender, instance, created, **kwargs):
    if created:
        specialization = instance.appointment_slot.doctor.doctor_profile.specialization  # assuming this is how you get the specialization
        try:
            price_entry = SpecializationPrice.objects.get(specialization=specialization)
            price = price_entry.price
        except SpecializationPrice.DoesNotExist:
            price = 100  # fallback price if not configured

        Payment.objects.create(
            appointment=instance,
            price=price,
            currency='pln',
            status='pending',
            stripe_payment_session_id=''
        )