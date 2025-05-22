#!/usr/bin/env python
"""
Script to create specific test notifications in TakeCare
"""
import os
import sys
import django
import uuid

# Add the project path to the sys.path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

from django.utils import timezone
from accounts.models import User
from notifications.models import Notification, NotificationType, NotificationStatus

def create_test_notifications():
    # Try to get admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"Found admin user with ID: {admin_user.id}")
    except User.DoesNotExist:
        # Try to get any user
        try:
            admin_user = User.objects.first()
            print(f"Using first user found: {admin_user.username}")
        except:
            print("No users found in the system")
            return
    
    # Create one notification of each type
    for type_code, type_label in NotificationType.choices:
        notification_id = uuid.uuid4()
        print(f"Creating {type_label} notification with ID: {notification_id}")
        
        notification = Notification.objects.create(
            id=notification_id,
            receiver=admin_user,
            message=f"This is a test {type_label} notification",
            subject=f"Test {type_label}",
            notification_type=type_code,
            status=NotificationStatus.UNREAD,
            date=timezone.now()
        )
        print(f"Created notification: {notification}")

if __name__ == "__main__":
    print("Creating test notifications...")
    create_test_notifications()
    print("Done!")
