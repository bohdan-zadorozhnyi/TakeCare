from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
from TakeCare.settings import ENCRYPTION_KEY
import json

class NotificationType(models.TextChoices):
    APPOINTMENT = 'APPOINTMENT', _('Appointment')
    PRESCRIPTION = 'PRESCRIPTION', _('Prescription')
    REFERRAL = 'REFERRAL', _('Referral')
    ISSUE = 'ISSUE', _('Issue')
    SYSTEM = 'SYSTEM', _('System')
    ADMIN = 'ADMIN', _('Admin')

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    message = models.TextField()
    encrypted_data = models.TextField(blank=True, null=True)
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    related_object_id = models.CharField(max_length=255, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"Notification for {self.receiver.name}"
    
    def mark_as_read(self):
        self.read = True
        self.save(update_fields=['read'])
    
    def mark_as_delivered(self):
        self.delivered = True
        self.delivered_at = timezone.now()
        self.save(update_fields=['delivered', 'delivered_at'])
    
    def encrypt_data(self, data):
        """Encrypt sensitive data using Fernet symmetric encryption"""
        if not isinstance(data, str):
            data = json.dumps(data)
        
        cipher_suite = Fernet(ENCRYPTION_KEY)
        encrypted_data = cipher_suite.encrypt(data.encode())
        self.encrypted_data = encrypted_data.decode()
        self.save(update_fields=['encrypted_data'])
    
    def decrypt_data(self):
        """Decrypt the encrypted data"""
        if not self.encrypted_data:
            return None
        
        cipher_suite = Fernet(ENCRYPTION_KEY)
        decrypted_data = cipher_suite.decrypt(self.encrypted_data.encode()).decode()
        
        try:
            return json.loads(decrypted_data)
        except json.JSONDecodeError:
            return decrypted_data
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['receiver', '-date']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['read']),
        ]


class NotificationLog(models.Model):
    """Model to log all notification activities for auditing purposes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)  # e.g., "created", "delivered", "read"
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']