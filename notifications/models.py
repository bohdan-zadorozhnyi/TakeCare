from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from accounts.models import User
import uuid
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

def get_encryption_key():
    """Generate a key for encryption based on the Django secret key"""
    password = settings.SECRET_KEY.encode()
    salt = b'takecare_notification_salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

class NotificationSeverity(models.TextChoices):
    LOW = 'LOW', _('Low')
    MEDIUM = 'MEDIUM', _('Medium')
    HIGH = 'HIGH', _('High')
    CRITICAL = 'CRITICAL', _('Critical')

class NotificationStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    DELIVERED = 'DELIVERED', _('Delivered')
    READ = 'READ', _('Read')
    FAILED = 'FAILED', _('Failed')

class NotificationType(models.TextChoices):
    TECHNICAL_ISSUE = 'TECHNICAL_ISSUE', _('Technical Issue')
    SYSTEM = 'SYSTEM', _('System Notification')
    APPOINTMENT = 'APPOINTMENT', _('Appointment')
    PRESCRIPTION = 'PRESCRIPTION', _('Prescription')
    MESSAGE = 'MESSAGE', _('New Message')
    ADMIN = 'ADMIN', _('Admin Notification')

class DeliveryChannel(models.TextChoices):
    IN_APP = 'IN_APP', _('In-app')
    EMAIL = 'EMAIL', _('Email')
    SMS = 'SMS', _('SMS')
    ALL = 'ALL', _('All Channels')

class Notification(models.Model):
    """Enhanced notification model to support the requirements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.SET_NULL, null=True, blank=True)
    receiver = models.ForeignKey(User, related_name='received_notifications', on_delete=models.CASCADE)
    
    # Message content - encrypted if contains sensitive data
    subject = models.CharField(max_length=255, blank=True)
    _message = models.TextField(db_column='message')  # Encrypted message storage
    is_encrypted = models.BooleanField(default=False)
    
    # Timestamps for tracking
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Classification and status
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    severity = models.CharField(max_length=10, choices=NotificationSeverity.choices, default=NotificationSeverity.MEDIUM)
    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    
    # Delivery settings
    delivery_channel = models.CharField(max_length=10, choices=DeliveryChannel.choices, default=DeliveryChannel.IN_APP)
    retry_count = models.PositiveSmallIntegerField(default=0)
    max_retries = models.PositiveSmallIntegerField(default=3)
    
    # For linking to related objects (like a specific appointment or issue)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Admin specific fields
    is_resolved = models.BooleanField(default=False)  # For technical issue tracking
    resolved_by = models.ForeignKey(User, related_name='resolved_notifications', on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receiver', 'status', 'created_at']),
            models.Index(fields=['notification_type', 'severity']),
        ]
    
    @property
    def message(self):
        """Get the message, decrypting if necessary"""
        if self.is_encrypted:
            try:
                key = get_encryption_key()
                cipher = Fernet(key)
                decrypted = cipher.decrypt(self._message.encode()).decode()
                return decrypted
            except Exception:
                return "***Encrypted Content***"
        return self._message
    
    @message.setter
    def message(self, value):
        """Set the message, encrypting if needed"""
        if self.is_encrypted or (hasattr(self, 'has_sensitive_data') and self.has_sensitive_data):
            key = get_encryption_key()
            cipher = Fernet(key)
            self._message = cipher.encrypt(value.encode()).decode()
            self.is_encrypted = True
        else:
            self._message = value
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.status = NotificationStatus.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_resolved(self, user):
        """Mark technical issue as resolved"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_by', 'resolved_at'])
    
    def retry_delivery(self):
        """Attempt to redeliver a failed notification"""
        if self.status == NotificationStatus.FAILED and self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = NotificationStatus.PENDING
            self.save(update_fields=['retry_count', 'status'])
            return True
        return False
    
    @property
    def has_sensitive_data(self):
        """Check if notification likely contains sensitive data"""
        sensitive_keywords = ['medical', 'health', 'diagnosis', 'prescription', 'treatment', 'patient', 'doctor']
        if self.subject:
            if any(keyword in self.subject.lower() for keyword in sensitive_keywords):
                return True
        if self._message and not self.is_encrypted:
            if any(keyword in self._message.lower() for keyword in sensitive_keywords):
                return True
        return False
    
    def __str__(self):
        if self.subject:
            return f"{self.get_notification_type_display()}: {self.subject} for {self.receiver.name}"
        return f"{self.get_notification_type_display()} for {self.receiver.name}"


class TechnicalIssueReport(models.Model):
    """Model for storing technical issue reports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, related_name='reported_issues', on_delete=models.CASCADE)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=NotificationSeverity.choices, default=NotificationSeverity.MEDIUM)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, related_name='resolved_issues', null=True, blank=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Optional metadata for more context
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=255, blank=True)
    stacktrace = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', 'resolved']),
            models.Index(fields=['reporter', 'created_at']),
        ]
    
    def __str__(self):
        return f"Issue reported by {self.reporter.name} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def resolve(self, user, notes=""):
        """Mark issue as resolved"""
        self.resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=['resolved', 'resolved_by', 'resolved_at', 'resolution_notes'])
        
        # Create notification for reporter that issue was resolved
        Notification.objects.create(
            sender=user,
            receiver=self.reporter,
            subject=f"Your reported issue has been resolved",
            _message=f"The technical issue you reported on {self.created_at.strftime('%Y-%m-%d %H:%M')} has been resolved.",
            notification_type=NotificationType.SYSTEM,
            severity=NotificationSeverity.LOW,
        )


class NotificationLog(models.Model):
    """For logging notification activity"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    @classmethod
    def log_action(cls, notification, action, details=""):
        """Create a log entry for notification actions"""
        return cls.objects.create(
            notification=notification,
            action=action,
            details=details
        )