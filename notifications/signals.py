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

try:
    from medical.models import MedicalRecord
    MEDICAL_RECORDS_ENABLED = True
except ImportError:
    MEDICAL_RECORDS_ENABLED = False

try:
    from issues.models import Issue
    ISSUES_ENABLED = True
except ImportError:
    ISSUES_ENABLED = False

try:
    from chat.models import Message
    CHAT_ENABLED = True
except ImportError:
    CHAT_ENABLED = False

# Define signals if the related apps are available
if REFERRALS_ENABLED:
    @receiver(post_save, sender=Referral)
    def send_referral_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new referral is created
        """
        if created and instance.patient:
            try:
                issuing_doctor = instance.issuing_doctor.name if instance.issuing_doctor else "Your doctor"
                specialist_type = instance.get_specialist_type_display() if hasattr(instance, 'get_specialist_type_display') else instance.specialist_type
                
                message = f"You have been referred by {issuing_doctor} to see a {specialist_type}"
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=message,
                    notification_type=NotificationType.REFERRAL,
                    related_object_id=str(instance.id),
                    related_object_type="referral"
                )
                logger.info(f"Referral notification sent to patient {instance.patient.id} for referral {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send referral notification: {e}", exc_info=True)

if PRESCRIPTIONS_ENABLED:
    @receiver(post_save, sender=Prescription)
    def send_prescription_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new prescription is created
        """
        if created and instance.patient:
            try:
                # Get medications from the prescription
                medications = instance.medications.all()
                med_names = []
                
                # Try to get medication names
                if medications.exists():
                    med_names = [med.medication_name for med in medications[:3]]
                    if len(medications) > 3:
                        med_names.append("and others")
                
                # Create medication text
                medication_text = ", ".join(med_names) if med_names else "medications"
                doctor = instance.doctor.name if instance.doctor else "Your doctor"
                
                message = f"A new prescription for {medication_text} has been created by {doctor}"
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=message,
                    notification_type=NotificationType.PRESCRIPTION,
                    related_object_id=str(instance.id),
                    related_object_type="prescription"
                )
                logger.info(f"Prescription notification sent to patient {instance.patient.id} for prescription {instance.id}")
            except Exception as e:
                logger.error(f"Failed to send prescription notification: {e}", exc_info=True)

if APPOINTMENTS_ENABLED:
    @receiver(post_save, sender=Appointment)
    def send_appointment_notification(sender, instance, created, **kwargs):
        """
        Send notification for appointment creation and updates
        """
        try:
            # Format the date for the notification - using a more user-friendly format
            appt_date = instance.start_time.strftime("%A, %d %B %Y at %H:%M") if instance.start_time else "scheduled date"
            
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

if MEDICAL_RECORDS_ENABLED:
    @receiver(post_save, sender=MedicalRecord)
    def send_medical_record_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new medical record is created or updated
        """
        try:
            # Notification for the patient
            if instance.patient:
                doctor_name = instance.doctor.name if instance.doctor else "Your doctor"
                
                # Different messages for creation and updates
                if created:
                    patient_message = f"{doctor_name} has created a new medical record about your condition: {instance.condition[:30]}..."
                else:
                    patient_message = f"{doctor_name} has updated your medical record about: {instance.condition[:30]}..."
                
                NotificationService.send_notification(
                    user_id=instance.patient.id,
                    message=patient_message,
                    notification_type=NotificationType.MEDICAL_RECORD,
                    related_object_id=str(instance.id),
                    related_object_type="medical_record"
                )
                logger.info(f"Medical record notification sent to patient {instance.patient.id} for record {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send medical record notification: {e}")

if ISSUES_ENABLED:
    @receiver(post_save, sender=Issue)
    def send_issue_notification(sender, instance, created, updated_fields=None, **kwargs):
        """
        Send notification when a new issue is created or resolved
        """
        try:
            # Determine if the issue was just resolved
            just_resolved = not created and instance.is_resolved and updated_fields and 'is_resolved' in updated_fields
            
            # For new issues, notify admin users
            if created:
                # Find admin users to notify about the new issue
                admin_users = User.objects.filter(role__in=['ADMIN', 'STAFF'])
                user_name = instance.user.name if instance.user and hasattr(instance.user, 'name') else "A user"
                
                for admin in admin_users:
                    admin_message = f"{user_name} has reported a new issue: {instance.message[:50]}..."
                    
                    NotificationService.send_notification(
                        user_id=admin.id,
                        message=admin_message,
                        notification_type=NotificationType.ISSUE,
                        related_object_id=str(instance.id),
                        related_object_type="issue"
                    )
                logger.info(f"Issue notification sent to admin users for issue {instance.id}")
            
            # For resolved issues, notify the reporting user
            elif just_resolved:
                user_message = f"Your reported issue has been resolved: {instance.message[:50]}..."
                
                NotificationService.send_notification(
                    user_id=instance.user.id,
                    message=user_message,
                    notification_type=NotificationType.ISSUE,
                    related_object_id=str(instance.id),
                    related_object_type="issue"
                )
                logger.info(f"Issue resolution notification sent to user {instance.user.id} for issue {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send issue notification: {e}")

if CHAT_ENABLED:
    @receiver(post_save, sender=Message)
    def send_chat_message_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new chat message is received
        """
        if created:
            try:
                # Get the other participant in the chat
                chatroom = instance.chatroom
                sender = instance.sender
                
                # Find the recipient(s) - all participants except the sender
                recipients = chatroom.participants.exclude(id=sender.id)
                
                for recipient in recipients:
                    # Create notification for the recipient
                    sender_name = sender.name if hasattr(sender, 'name') else "Someone"
                    
                    # Truncate the message content if it's too long
                    content_preview = instance.content[:50] + "..." if len(instance.content) > 50 else instance.content
                    
                    notification_message = f"{sender_name} sent you a message: {content_preview}"
                    
                    NotificationService.send_notification(
                        user_id=recipient.id,
                        message=notification_message,
                        notification_type=NotificationType.MESSAGE,
                        related_object_id=str(chatroom.id),
                        related_object_type="chat"
                    )
                    logger.info(f"Chat message notification sent to user {recipient.id} for message in chatroom {chatroom.id}")
            except Exception as e:
                logger.error(f"Failed to send chat message notification: {e}")

# Register these signals in the appropriate app configs
def ready():
    """
    Import signals when the app is ready
    (This function should be called from apps.py)
    """
    logger.info("Notification signals registered for enabled modules:")
    if REFERRALS_ENABLED:
        logger.info("- Referrals module")
    if PRESCRIPTIONS_ENABLED:
        logger.info("- Prescriptions module")
    if APPOINTMENTS_ENABLED:
        logger.info("- Appointments module")
    if MEDICAL_RECORDS_ENABLED:
        logger.info("- Medical Records module")
    if ISSUES_ENABLED:
        logger.info("- Issues module")
    if CHAT_ENABLED:
        logger.info("- Chat module")
