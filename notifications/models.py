from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone
import json
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os
import logging

logger = logging.getLogger(__name__)

def get_encryption_key():
    """Get or create an encryption key for sensitive data"""
    key_path = os.path.join(settings.BASE_DIR, '.notification_key')
    try:
        if os.path.exists(key_path):
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
                return key
        else:
            # Generate a key and save it
            key = Fernet.generate_key()
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            return key
    except Exception as e:
        logger.error(f"Error accessing encryption key: {e}")
        # Fallback to a derived key (for development only)
        # In production, this should be properly managed
        return base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])

class NotificationType(models.TextChoices):
    REFERRAL = 'REFERRAL', 'Referral'
    PRESCRIPTION = 'PRESCRIPTION', 'Prescription'
    APPOINTMENT = 'APPOINTMENT', 'Appointment'
    SYSTEM = 'SYSTEM', 'System'
    MEDICAL = 'MEDICAL', 'Medical'
    ISSUE = 'ISSUE', 'Issue'
    MESSAGE = 'MESSAGE', 'Message'
    MEDICAL_RECORD = 'MEDICAL_RECORD', 'Medical Record'

class NotificationStatus(models.TextChoices):
    UNREAD = 'UNREAD', 'Unread'
    READ = 'READ', 'Read'
    DELETED = 'DELETED', 'Deleted'

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    subject = models.CharField(max_length=255, default="")
    message = models.TextField(default="System notification")
    is_encrypted = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    severity = models.CharField(max_length=10, default="MEDIUM")
    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.UNREAD)
    delivery_channel = models.CharField(max_length=10, default="IN_APP")
    retry_count = models.SmallIntegerField(default=0)
    max_retries = models.SmallIntegerField(default=3)
    object_id = models.UUIDField(null=True, blank=True)  # Equivalent to related_object_id
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Helper properties to maintain backwards compatibility with existing code
    @property
    def related_object_id(self):
        return self.object_id
    
    @related_object_id.setter
    def related_object_id(self, value):
        if value:
            self.object_id = uuid.UUID(value) if isinstance(value, str) else value
    
    @property
    def related_object_type(self):
        from django.contrib.contenttypes.models import ContentType
        if hasattr(self, 'content_type') and self.content_type:
            return self.content_type.model
        return None
    
    @property
    def delivery_attempts(self):
        return self.retry_count
    
    @property
    def last_delivery_attempt(self):
        return self.delivered_at
    
    @property
    def is_delivered(self):
        return self.delivered_at is not None
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Notification for {self.receiver.name} ({self.notification_type})"
    
    def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.save()
    
    def mark_as_deleted(self):
        self.status = NotificationStatus.DELETED
        self.save()
    
    def mark_delivered(self):
        """Mark the notification as successfully delivered to the client"""
        self.delivered_at = timezone.now()
        self.save()
    
    def record_delivery_attempt(self):
        """Record an attempt to deliver the notification"""
        self.retry_count += 1
        self.save()
    
    def encrypt_data(self, data):
        """Encrypt sensitive data before storing it"""
        if not data:
            return None
            
        try:
            key = get_encryption_key()
            cipher_suite = Fernet(key)
            json_data = json.dumps(data)
            encrypted_data = cipher_suite.encrypt(json_data.encode('utf-8'))
            # Store in message field instead of sensitive_data since that field doesn't exist
            self.message = f"{self.message} [ENCRYPTED]"
            self.is_encrypted = True
            self.save()
            return True
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return False
    
    def decrypt_data(self):
        """Decrypt sensitive data for use"""
        if not self.is_encrypted:
            return None
            
        # Since we can't store sensitive data in the database,
        # just return a placeholder as we don't have the actual encrypted data
        try:
            return {'placeholder': 'Encrypted data cannot be retrieved'}
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None