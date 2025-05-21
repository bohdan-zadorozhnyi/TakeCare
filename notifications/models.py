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

class NotificationStatus(models.TextChoices):
    UNREAD = 'UNREAD', 'Unread'
    READ = 'READ', 'Read'
    DELETED = 'DELETED', 'Deleted'

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(default="System notification")
    date = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.UNREAD)
    related_object_id = models.CharField(max_length=50, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    sensitive_data = models.TextField(null=True, blank=True)  # For encrypted payload
    delivery_attempts = models.IntegerField(default=0)
    last_delivery_attempt = models.DateTimeField(null=True, blank=True)
    is_delivered = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Notification for {self.receiver.name} ({self.type})"
    
    def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.save()
    
    def mark_as_deleted(self):
        self.status = NotificationStatus.DELETED
        self.save()
    
    def mark_delivered(self):
        """Mark the notification as successfully delivered to the client"""
        self.is_delivered = True
        self.save()
    
    def record_delivery_attempt(self):
        """Record an attempt to deliver the notification"""
        self.delivery_attempts += 1
        self.last_delivery_attempt = timezone.now()
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
            self.sensitive_data = encrypted_data.decode('utf-8')
            self.save()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
    
    def decrypt_data(self):
        """Decrypt sensitive data for use"""
        if not self.sensitive_data:
            return None
            
        try:
            key = get_encryption_key()
            cipher_suite = Fernet(key)
            decrypted_data = cipher_suite.decrypt(self.sensitive_data.encode('utf-8'))
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None