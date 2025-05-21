from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
import uuid
import json
from .models import Notification, NotificationType, NotificationStatus
import time

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for creating and sending notifications
    """
    
    @classmethod
    def send_notification(cls, user_id, message, notification_type=NotificationType.SYSTEM, 
                         related_object_id=None, related_object_type=None, sensitive_data=None):
        """
        Create a new notification and send it to the user
        
        Args:
            user_id: The ID of the user to send the notification to
            message: The text content of the notification
            notification_type: The type of notification (from NotificationType choices)
            related_object_id: ID of related object (e.g. appointment ID)
            related_object_type: Type of related object (e.g. "appointment")
            sensitive_data: Optional sensitive data to encrypt
        
        Returns:
            The created notification object or None if failed
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Create notification in database
            notification = Notification.objects.create(
                receiver=user,
                message=message,
                type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type,
                status=NotificationStatus.UNREAD
            )
            
            # If there's sensitive data, encrypt it
            if sensitive_data:
                notification.encrypt_data(sensitive_data)
                
            # Send to the user's notification channel group if they're online
            channel_layer = get_channel_layer()
            notification_group_name = f"notifications_{user_id}"
            
            try:
                async_to_sync(channel_layer.group_send)(
                    notification_group_name,
                    {
                        "type": "notification_message",
                        "message": message,
                        "notification_id": str(notification.id),
                        "type": notification_type
                    }
                )
                logger.info(f"Notification {notification.id} sent to user {user.id}")
            except Exception as e:
                logger.error(f"Channel layer error sending notification to user {user.id}: {str(e)}")
                notification.record_delivery_attempt()
            
            return notification
        
        except User.DoesNotExist:
            logger.error(f"Cannot send notification to non-existent user with ID {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def send_bulk_notification(cls, user_ids, message, notification_type=NotificationType.SYSTEM):
        """
        Send the same notification to multiple users
        
        Args:
            user_ids: List of user IDs to send to
            message: The notification message
            notification_type: Type of notification
            
        Returns:
            List of created notification objects
        """
        notifications = []
        
        for user_id in user_ids:
            notification = cls.send_notification(
                user_id=user_id,
                message=message,
                notification_type=notification_type
            )
            if notification:
                notifications.append(notification)
        
        return notifications
            
    @classmethod
    def send_referral_notification(cls, patient_id, doctor_name, specialty):
        """
        Send a notification for a new referral
        """
        message = f"You've received a referral to {doctor_name} ({specialty})"
        return cls.send_notification(
            user_id=patient_id,
            message=message,
            notification_type=NotificationType.REFERRAL
        )
    
    @classmethod
    def send_prescription_notification(cls, patient_id, medication_name):
        """
        Send a notification for a new prescription
        """
        message = f"New prescription created: {medication_name}"
        return cls.send_notification(
            user_id=patient_id,
            message=message,
            notification_type=NotificationType.PRESCRIPTION
        )
    
    @classmethod
    def send_appointment_notification(cls, user_id, appointment_date, doctor_name=None, patient_name=None, action="scheduled"):
        """
        Send a notification about an appointment
        """
        if doctor_name:
            # This is for a patient notification
            message = f"Your appointment with Dr. {doctor_name} on {appointment_date} has been {action}"
        elif patient_name:
            # This is for a doctor notification
            message = f"Your appointment with {patient_name} on {appointment_date} has been {action}"
        else:
            message = f"Your appointment on {appointment_date} has been {action}"
            
        return cls.send_notification(
            user_id=user_id,
            message=message,
            notification_type=NotificationType.APPOINTMENT
        )
    
    @classmethod
    def retry_failed_deliveries(cls, max_retries=3, max_age_hours=24):
        """
        Retry sending notifications that failed to deliver
        
        Args:
            max_retries: Maximum number of delivery attempts
            max_age_hours: Only retry notifications younger than this many hours
        """
        min_date = timezone.now() - timezone.timedelta(hours=max_age_hours)
        
        # Get notifications that aren't delivered but have been attempted less than max_retries times
        pending_notifications = Notification.objects.filter(
            is_delivered=False,
            delivery_attempts__lt=max_retries,
            date__gt=min_date
        )
        
        channel_layer = get_channel_layer()
        count = 0
        
        for notification in pending_notifications:
            notification_group_name = f"notifications_{notification.receiver.id}"
            
            try:
                async_to_sync(channel_layer.group_send)(
                    notification_group_name,
                    {
                        "type": "notification_message",
                        "message": notification.message,
                        "notification_id": str(notification.id),
                        "type": notification.type
                    }
                )
                count += 1
            except Exception as e:
                logger.error(f"Retry failed for notification {notification.id}: {str(e)}")
                notification.record_delivery_attempt()
        
        return count
