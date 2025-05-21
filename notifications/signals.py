from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .services import NotificationService
from .models import NotificationType
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Attempt to import models from other apps
# We use try/except to avoid creating hard dependencies
try:
    from referrals.models import Referral
    REFERRALS_ENABLED = True
except ImportError:
    REFERRALS_ENABLED = False

try:
    from prescriptions.models import Prescription
    PRESCRIPTIONS_ENABLED = True
except ImportError:
    PRESCRIPTIONS_ENABLED = False

try:
    from appointments.models import Appointment
    APPOINTMENTS_ENABLED = True
except ImportError:
    APPOINTMENTS_ENABLED = False

# Define signals if the related apps are available
if REFERRALS_ENABLED:
    @receiver(post_save, sender=Referral)
    def send_referral_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new referral is created
        """
        if created and instance.patient:
            try:
                referring_doctor = instance.referring_doctor.name if instance.referring_doctor else "Your doctor"
                specialist = instance.specialist.name if instance.specialist else "a specialist"
                specialty = instance.specialist.specialty if instance.specialist else "specialist consultation"
                
                message = f"You have been referred by {referring_doctor} to see {specialist} for {specialty}"
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=message,
                    notification_type=NotificationType.REFERRAL,
                    related_object_id=str(instance.id),
                    related_object_type="referral"
                )
                logger.info(f"Referral notification sent to patient {instance.patient.id} for referral {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send referral notification: {e}")

if PRESCRIPTIONS_ENABLED:
    @receiver(post_save, sender=Prescription)
    def send_prescription_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new prescription is created
        """
        if created and instance.patient:
            try:
                medication = instance.medication_name
                doctor = instance.doctor.name if instance.doctor else "Your doctor"
                
                message = f"A new prescription for {medication} has been created by {doctor}"
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=message,
                    notification_type=NotificationType.PRESCRIPTION,
                    related_object_id=str(instance.id),
                    related_object_type="prescription"
                )
                logger.info(f"Prescription notification sent to patient {instance.patient.id} for prescription {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send prescription notification: {e}")

if APPOINTMENTS_ENABLED:
    @receiver(post_save, sender=Appointment)
    def send_appointment_notification(sender, instance, created, **kwargs):
        """
        Send notification for appointment creation and updates
        """
        try:
            # Format the date for the notification
            appt_date = instance.start_time.strftime("%d %b %Y at %H:%M") if instance.start_time else "scheduled date"
            
            # Determine if this is a create or update action
            action = "scheduled" if created else "updated"
            
            # Notification for the patient
            if instance.patient:
                doctor_name = instance.doctor.name if instance.doctor else "your doctor"
                patient_message = f"Your appointment with {doctor_name} on {appt_date} has been {action}"
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=patient_message,
                    notification_type=NotificationType.APPOINTMENT,
                    related_object_id=str(instance.id),
                    related_object_type="appointment"
                )
                
            # Notification for the doctor
            if instance.doctor:
                patient_name = instance.patient.name if instance.patient else "a patient"
                doctor_message = f"Your appointment with {patient_name} on {appt_date} has been {action}"
                
                NotificationService.send_notification(
                    user_id=instance.doctor.id,
                    message=doctor_message,
                    notification_type=NotificationType.APPOINTMENT,
                    related_object_id=str(instance.id),
                    related_object_type="appointment"
                )
                
            logger.info(f"Appointment notifications sent for appointment {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send appointment notification: {e}")

# Register these signals in the appropriate app configs
def ready():
    """
    Import signals when the app is ready
    (This function should be called from apps.py)
    """
    logger.info("Notification signals registered")
