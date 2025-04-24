from django.db import transaction
from django.utils import timezone
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging
from .models import Notification, NotificationType, NotificationLog

logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for handling notification operations"""
    
    @staticmethod
    def create_notification(
        receiver,
        message,
        notification_type=NotificationType.SYSTEM,
        sender=None,
        related_object_id=None,
        related_object_type=None,
        sensitive_data=None
    ):
        """
        Create a notification and send it to the receiver
        """
        with transaction.atomic():
            # Create notification
            notification = Notification.objects.create(
                receiver=receiver,
                sender=sender,
                message=message,
                notification_type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type
            )
            
            # Log notification creation
            NotificationLog.objects.create(
                notification=notification,
                action='created',
                details=f"Notification created for {receiver.name}"
            )
            
            # Encrypt sensitive data if provided
            if sensitive_data:
                notification.encrypt_data(sensitive_data)
            
            # Send notification via websocket if possible
            NotificationService.send_realtime_notification(notification)
            
            return notification
    
    @staticmethod
    def send_realtime_notification(notification):
        """
        Send the notification to the user in real-time via websocket
        """
        channel_layer = get_channel_layer()
        
        try:
            # Send to user's notification channel group
            async_to_sync(channel_layer.group_send)(
                f"notifications_{notification.receiver.id}",
                {
                    'type': 'notification_message',
                    'message': {
                        'id': str(notification.id),
                        'message': notification.message,
                        'type': notification.notification_type,
                        'date': notification.date.isoformat(),
                        'sender': notification.sender.name if notification.sender else None,
                        'related_object_id': notification.related_object_id,
                        'related_object_type': notification.related_object_type,
                    }
                }
            )
            
            # Mark as delivered
            notification.mark_as_delivered()
            
            # Log successful delivery
            NotificationLog.objects.create(
                notification=notification,
                action='delivered',
                success=True,
                details=f"Notification delivered to {notification.receiver.name} via websocket"
            )
            
            return True
        except Exception as e:
            # Log error
            logger.error(f"Error sending real-time notification: {str(e)}")
            
            NotificationLog.objects.create(
                notification=notification,
                action='delivery_failed',
                success=False,
                details=f"Notification delivery failed: {str(e)}"
            )
            
            return False
    
    @staticmethod
    def mark_as_read(notification_id, user):
        """
        Mark a notification as read
        """
        try:
            notification = Notification.objects.get(id=notification_id, receiver=user)
            notification.mark_as_read()
            
            # Log notification read
            NotificationLog.objects.create(
                notification=notification,
                action='read',
                details=f"Notification marked as read by {user.name}"
            )
            
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Mark all notifications as read for a user
        """
        with transaction.atomic():
            notifications = Notification.objects.filter(receiver=user, read=False)
            
            count = notifications.count()
            if count > 0:
                notifications.update(read=True)
                
                # Log bulk read action
                NotificationLog.objects.create(
                    notification=notifications.first(),
                    action='bulk_read',
                    details=f"{count} notifications marked as read by {user.name}"
                )
            
            return count
    
    @staticmethod
    def get_unread_count(user):
        """
        Get count of unread notifications for a user
        """
        return Notification.objects.filter(receiver=user, read=False).count()
    
    @staticmethod
    def send_notifications_to_role(message, role, notification_type=NotificationType.ADMIN, sender=None, exclude_users=None):
        """
        Send notifications to all users with a specific role
        """
        from accounts.models import User
        
        users = User.objects.filter(role=role)
        if exclude_users:
            users = users.exclude(id__in=[user.id for user in exclude_users])
        
        notifications = []
        for user in users:
            notification = NotificationService.create_notification(
                receiver=user,
                message=message,
                notification_type=notification_type,
                sender=sender
            )
            notifications.append(notification)
        
        # Log bulk notification
        NotificationLog.objects.create(
            notification=notifications[0] if notifications else None,
            action='bulk_sent',
            details=f"Sent notifications to {len(notifications)} users with role {role}"
        )
        
        return notifications
    
    @staticmethod
    def notify_about_referral(referral):
        """
        Send notification to patient about a new referral
        """
        return NotificationService.create_notification(
            receiver=referral.patient,
            message=f"You have received a new referral to a {referral.specialist_type} from Dr. {referral.referring_doctor.name}",
            notification_type=NotificationType.REFERRAL,
            sender=referral.referring_doctor,
            related_object_id=str(referral.id),
            related_object_type='referral',
            sensitive_data={
                'referral_id': str(referral.id),
                'specialist_type': referral.specialist_type,
                'expiration_date': referral.expiration_date.isoformat() if referral.expiration_date else None,
                'description': referral.description
            }
        )
    
    @staticmethod
    def notify_about_prescription(prescription):
        """
        Send notification to patient about a new prescription
        """
        return NotificationService.create_notification(
            receiver=prescription.patient,
            message=f"Dr. {prescription.doctor.name} has written you a new prescription",
            notification_type=NotificationType.PRESCRIPTION,
            sender=prescription.doctor,
            related_object_id=str(prescription.id),
            related_object_type='prescription',
            sensitive_data={
                'prescription_id': str(prescription.id),
                'medications': [m.medication_name for m in prescription.medications.all()],
                'expiration_date': prescription.expiration_date.isoformat() if prescription.expiration_date else None,
            }
        )
    
    @staticmethod
    def notify_about_appointment_booking(appointment):
        """
        Send notifications about an appointment booking to both doctor and patient
        """
        # Notify patient
        patient_notification = NotificationService.create_notification(
            receiver=appointment.patient,
            message=f"Your appointment with Dr. {appointment.appointment_slot.doctor.name} on {appointment.appointment_slot.date.strftime('%b %d, %Y at %I:%M %p')} has been confirmed",
            notification_type=NotificationType.APPOINTMENT,
            sender=None,
            related_object_id=str(appointment.id),
            related_object_type='appointment'
        )
        
        # Notify doctor
        doctor_notification = NotificationService.create_notification(
            receiver=appointment.appointment_slot.doctor,
            message=f"Patient {appointment.patient.name} has booked an appointment for {appointment.appointment_slot.date.strftime('%b %d, %Y at %I:%M %p')}",
            notification_type=NotificationType.APPOINTMENT,
            sender=None,
            related_object_id=str(appointment.id),
            related_object_type='appointment'
        )
        
        return patient_notification, doctor_notification
    
    @staticmethod
    def notify_about_appointment_cancellation(appointment):
        """
        Send notifications about an appointment cancellation to both doctor and patient
        """
        # Notify patient (if cancelled by doctor)
        if appointment.cancelled_by == 'doctor':
            patient_notification = NotificationService.create_notification(
                receiver=appointment.patient,
                message=f"Your appointment with Dr. {appointment.appointment_slot.doctor.name} on {appointment.appointment_slot.date.strftime('%b %d, %Y at %I:%M %p')} has been cancelled",
                notification_type=NotificationType.APPOINTMENT,
                sender=appointment.appointment_slot.doctor,
                related_object_id=str(appointment.id),
                related_object_type='appointment'
            )
        
        # Notify doctor (if cancelled by patient)
        if appointment.cancelled_by == 'patient':
            doctor_notification = NotificationService.create_notification(
                receiver=appointment.appointment_slot.doctor,
                message=f"Patient {appointment.patient.name} has cancelled their appointment for {appointment.appointment_slot.date.strftime('%b %d, %Y at %I:%M %p')}",
                notification_type=NotificationType.APPOINTMENT,
                sender=appointment.patient,
                related_object_id=str(appointment.id),
                related_object_type='appointment'
            )
            
        return True
    
    @staticmethod
    def notify_about_expiring_referrals():
        """
        Check for referrals that are about to expire and notify patients
        """
        from referrals.models import Referral
        from datetime import timedelta
        
        # Find referrals expiring in the next 3 days
        expiring_soon = timezone.now().date() + timedelta(days=3)
        referrals = Referral.objects.filter(
            expiration_date__lte=expiring_soon,
            expiration_date__gte=timezone.now().date(),
            is_used=False,
            expiry_notified=False
        )
        
        notifications_sent = 0
        for referral in referrals:
            days_left = (referral.expiration_date - timezone.now().date()).days
            
            notification = NotificationService.create_notification(
                receiver=referral.patient,
                message=f"Your referral to {referral.specialist_type} will expire in {days_left} days",
                notification_type=NotificationType.REFERRAL,
                related_object_id=str(referral.id),
                related_object_type='referral'
            )
            
            # Mark as notified
            referral.expiry_notified = True
            referral.save(update_fields=['expiry_notified'])
            notifications_sent += 1
            
        return notifications_sent
    
    @staticmethod
    def notify_admin_about_issue(issue):
        """
        Notify admin about a new issue report
        """
        from accounts.models import User
        
        # Find all admin users
        admins = User.objects.filter(role='ADMIN')
        
        notifications = []
        for admin in admins:
            notification = NotificationService.create_notification(
                receiver=admin,
                message=f"New issue reported: {issue.title}",
                notification_type=NotificationType.ISSUE,
                sender=issue.reported_by,
                related_object_id=str(issue.id),
                related_object_type='issue'
            )
            notifications.append(notification)
            
        return notifications