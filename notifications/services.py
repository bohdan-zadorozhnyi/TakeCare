"""
Notification service module for handling notification delivery
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import (
    Notification, NotificationLog, 
    NotificationStatus, NotificationType, 
    DeliveryChannel, TechnicalIssueReport
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling notifications"""
    
    @classmethod
    def send_notification(cls, receiver, message, **kwargs):
        """
        Create and send a notification to a user
        
        Args:
            receiver: User object of recipient
            message: Text message content
            **kwargs: Additional parameters like subject, notification_type, severity, etc.
        
        Returns:
            Created Notification object
        """
        subject = kwargs.get('subject', '')
        notification_type = kwargs.get('notification_type', NotificationType.SYSTEM)
        severity = kwargs.get('severity', 'MEDIUM')
        delivery_channel = kwargs.get('delivery_channel', DeliveryChannel.IN_APP)
        sender = kwargs.get('sender', None)
        related_object = kwargs.get('related_object', None)
        
        is_encrypted = kwargs.get('is_encrypted', False)
        
        # Create the notification object
        notification = Notification(
            receiver=receiver,
            sender=sender,
            subject=subject,
            is_encrypted=is_encrypted,
            notification_type=notification_type,
            severity=severity,
            delivery_channel=delivery_channel,
        )
        
        # Set message with encryption if needed
        notification.message = message
        
        # Link to related object if provided
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.id
        
        notification.save()
        
        # Log creation
        NotificationLog.log_action(notification, 'CREATED')
        
        # Process delivery based on channel
        try:
            if delivery_channel in [DeliveryChannel.IN_APP, DeliveryChannel.ALL]:
                cls._deliver_in_app(notification)
            
            if delivery_channel in [DeliveryChannel.EMAIL, DeliveryChannel.ALL]:
                cls._deliver_email(notification)
                
            if delivery_channel in [DeliveryChannel.SMS, DeliveryChannel.ALL]:
                cls._deliver_sms(notification)
        
        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {str(e)}")
            notification.status = NotificationStatus.FAILED
            notification.save(update_fields=['status'])
            NotificationLog.log_action(notification, 'DELIVERY_FAILED', str(e))
        
        return notification
    
    @classmethod
    def send_technical_issue_notification(cls, issue):
        """
        Send notifications about a technical issue to all admins
        
        Args:
            issue: TechnicalIssueReport object
        """
        from accounts.models import User
        
        # Get all admins to notify
        admins = User.objects.filter(role='ADMIN')
        
        # Create message content
        subject = f"Technical Issue: {issue.severity} severity"
        message = f"""
        A technical issue was reported by {issue.reporter.name} ({issue.reporter.email}).
        
        Severity: {issue.get_severity_display()}
        Date: {issue.created_at.strftime('%Y-%m-%d %H:%M')}
        
        Description:
        {issue.description}
        
        System info:
        Browser: {issue.browser}
        OS: {issue.operating_system}
        URL: {issue.url}
        """
        
        # Send notification to each admin
        for admin in admins:
            cls.send_notification(
                receiver=admin,
                message=message,
                subject=subject,
                notification_type=NotificationType.TECHNICAL_ISSUE,
                severity=issue.severity,
                related_object=issue
            )
    
    @classmethod
    def send_bulk_notification(cls, receivers, message, **kwargs):
        """
        Send the same notification to multiple users
        
        Args:
            receivers: Queryset or list of User objects
            message: Text message content
            **kwargs: Additional parameters like subject, type, etc.
        
        Returns:
            List of created Notification objects
        """
        notifications = []
        for receiver in receivers:
            notification = cls.send_notification(receiver, message, **kwargs)
            notifications.append(notification)
        return notifications
    
    @classmethod
    def mark_as_read(cls, notification_id, user):
        """
        Mark a notification as read
        
        Args:
            notification_id: UUID of notification
            user: User marking as read
        
        Returns:
            Updated Notification object or None if not found/authorized
        """
        try:
            notification = Notification.objects.get(id=notification_id, receiver=user)
            notification.mark_as_read()
            NotificationLog.log_action(notification, 'MARKED_READ')
            return notification
        except Notification.DoesNotExist:
            return None
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        Mark all unread notifications as read for a user
        
        Args:
            user: User object
        
        Returns:
            Number of notifications updated
        """
        unread = Notification.objects.filter(
            receiver=user, 
            status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
        )
        count = unread.count()
        
        # Bulk update status
        unread.update(
            status=NotificationStatus.READ,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {count} notifications as read for user {user.id}")
        return count
    
    @classmethod
    def retry_failed_deliveries(cls):
        """Retry delivery for all failed notifications"""
        failed = Notification.objects.filter(
            status=NotificationStatus.FAILED,
            created_at__gte=timezone.now() - timezone.timedelta(days=3)  # Only retry recent failures
        )
        retried = 0
        
        for notification in failed:
            if notification.retry_delivery():
                # Process the delivery again
                try:
                    if notification.delivery_channel in [DeliveryChannel.IN_APP, DeliveryChannel.ALL]:
                        cls._deliver_in_app(notification)
                    
                    if notification.delivery_channel in [DeliveryChannel.EMAIL, DeliveryChannel.ALL]:
                        cls._deliver_email(notification)
                        
                    if notification.delivery_channel in [DeliveryChannel.SMS, DeliveryChannel.ALL]:
                        cls._deliver_sms(notification)
                    
                    retried += 1
                except Exception as e:
                    logger.error(f"Retry failed for notification {notification.id}: {str(e)}")
                    notification.status = NotificationStatus.FAILED
                    notification.save(update_fields=['status'])
                    NotificationLog.log_action(notification, 'RETRY_FAILED', str(e))
        
        logger.info(f"Retried {retried} failed notifications")
        return retried
    
    @classmethod
    def _deliver_in_app(cls, notification):
        """Deliver notification in-app via WebSockets"""
        channel_layer = get_channel_layer()
        
        # Send to user's notification group
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.receiver.id}_notifications",
            {
                "type": "notification.message",
                "notification_id": str(notification.id),
                "subject": notification.subject,
                "message": notification.message if not notification.is_encrypted else None,
                "notification_type": notification.notification_type,
                "severity": notification.severity,
                "created_at": notification.created_at.isoformat(),
                "sender": notification.sender.name if notification.sender else None
            }
        )
        
        notification.mark_as_delivered()
        NotificationLog.log_action(notification, 'DELIVERED_IN_APP')
        
    @classmethod
    def _deliver_email(cls, notification):
        """Deliver notification via email"""
        subject = notification.subject or f"{notification.get_notification_type_display()} Notification"
        
        # Render email template
        html_message = render_to_string('notifications/email_notification.html', {
            'notification': notification,
            'user': notification.receiver,
        })
        
        # Send email
        sent = send_mail(
            subject=subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.receiver.email],
            html_message=html_message,
            fail_silently=False
        )
        
        if sent:
            notification.mark_as_delivered()
            NotificationLog.log_action(notification, 'DELIVERED_EMAIL')
        else:
            raise ValueError("Email delivery failed")
    
    @classmethod
    def _deliver_sms(cls, notification):
        """
        Deliver notification via SMS
        Note: Actual SMS delivery would require integration with an SMS provider
        """
        # This is a placeholder - in a real implementation, you would integrate
        # with an SMS provider like Twilio, AWS SNS, etc.
        logger.info(f"Would send SMS to {notification.receiver.phone_number}: {notification.message[:50]}...")
        
        # For now, we'll simulate successful delivery
        notification.mark_as_delivered()
        NotificationLog.log_action(notification, 'DELIVERED_SMS', "Simulated delivery")


class TechnicalIssueService:
    """Service for handling technical issues"""
    
    @classmethod
    def report_issue(cls, user, description, severity='MEDIUM', **kwargs):
        """
        Create a technical issue report and notify admins
        
        Args:
            user: User reporting the issue
            description: Description of the issue
            severity: Issue severity level
            **kwargs: Additional metadata like browser, OS, etc.
        
        Returns:
            Created TechnicalIssueReport object
        """
        # Create the issue report
        issue = TechnicalIssueReport(
            reporter=user,
            description=description,
            severity=severity,
            browser=kwargs.get('browser', ''),
            operating_system=kwargs.get('operating_system', ''),
            url=kwargs.get('url', ''),
            stacktrace=kwargs.get('stacktrace', '')
        )
        issue.save()
        
        # Notify admins
        NotificationService.send_technical_issue_notification(issue)
        
        return issue
    
    @classmethod
    def resolve_issue(cls, issue_id, user, resolution_notes=""):
        """
        Mark a technical issue as resolved
        
        Args:
            issue_id: UUID of the issue
            user: User resolving the issue
            resolution_notes: Notes on the resolution
        
        Returns:
            Updated TechnicalIssueReport object or None if not found
        """
        try:
            issue = TechnicalIssueReport.objects.get(id=issue_id)
            issue.resolve(user, resolution_notes)
            logger.info(f"Issue {issue_id} resolved by user {user.id}")
            return issue
        except TechnicalIssueReport.DoesNotExist:
            logger.error(f"Issue {issue_id} not found")
            return None
    
    @classmethod
    def get_unresolved_issues(cls, order_by='-severity'):
        """
        Get all unresolved issues
        
        Args:
            order_by: Field to order by (default: -severity)
        
        Returns:
            QuerySet of unresolved issues
        """
        return TechnicalIssueReport.objects.filter(resolved=False).order_by(order_by)