#!/usr/bin/env python
"""
Script to create test notifications in TakeCare
"""
import os
import sys
import django

# Add the project path to the sys.path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

from django.utils import timezone
from accounts.models import User
from notifications.models import Notification, NotificationType, NotificationStatus

def create_test_notifications():
    """Create test notifications for all users"""
    users = User.objects.all()
    notification_types = list(NotificationType.choices)
    
    if not users.exists():
        print("No users found in the system")
        return
    
    # Create notifications for all users
    for user in users:
        print(f"Creating test notifications for {user.username}...")
        
        # Create one notification of each type
        for i, (type_code, type_label) in enumerate(notification_types):
            Notification.objects.create(
                receiver=user,
                message=f"This is a test {type_label} notification #{i+1}",
                subject=f"Test {type_label} Notification",
                notification_type=type_code,
                status=NotificationStatus.UNREAD if i % 2 == 0 else NotificationStatus.READ,
                date=timezone.now()
            )
            
        print(f"Created {len(notification_types)} notifications for {user.username}")

if __name__ == "__main__":
    print("Creating test notifications...")
    create_test_notifications()
    print("Done!")
