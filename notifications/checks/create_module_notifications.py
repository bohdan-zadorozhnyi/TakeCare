#!/usr/bin/env python
"""
Test script to create notifications for the newly integrated modules:
- Medical Records
- Issues
- Chat Messages

Run this script from the Django shell:
python manage.py shell < create_module_notifications.py

Or run directly:
python create_module_notifications.py
"""

import os
import sys
import django
import uuid
import random
from datetime import datetime, timedelta

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

# Import the notification service
from notifications.services import NotificationService
from notifications.models import NotificationType
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_notifications():
    """Create test notifications for different modules"""
    
    # Get a list of users
    users = list(User.objects.all())
    
    if not users:
        print("No users found in the database. Aborting.")
        return
    
    # Get doctors and patients
    doctors = list(User.objects.filter(role='DOCTOR'))
    patients = list(User.objects.filter(role='PATIENT'))
    
    print(f"Found {len(users)} users, {len(doctors)} doctors, {len(patients)} patients")
    
    if not doctors or not patients:
        print("Either no doctors or patients found. Using random users instead.")
        
    # Medical Record notifications
    print("\nCreating Medical Record notifications...")
    for i in range(3):
        patient = random.choice(patients) if patients else random.choice(users)
        doctor = random.choice(doctors) if doctors else random.choice(users)
        
        doctor_name = getattr(doctor, 'name', f"Dr. User {doctor.id}")
        condition = random.choice([
            "Hypertension", 
            "Type 2 Diabetes", 
            "Seasonal Allergies", 
            "Lower Back Pain", 
            "Anxiety"
        ])
        
        message = f"{doctor_name} has created a new medical record about your condition: {condition}..."
        
        notification = NotificationService.send_notification(
            user_id=patient.id,
            message=message,
            notification_type=NotificationType.MEDICAL_RECORD,
            related_object_id=str(uuid.uuid4()),
            related_object_type="medical_record"
        )
        
        if notification:
            print(f"Created Medical Record notification for User {patient.id}: {message[:40]}...")
    
    # Issue notifications
    print("\nCreating Issue notifications...")
    admin_users = list(User.objects.filter(role__in=['ADMIN', 'STAFF']))
    if not admin_users:
        admin_users = users
    
    for i in range(3):
        user = random.choice(users)
        admin = random.choice(admin_users)
        
        user_name = getattr(user, 'name', f"User {user.id}")
        
        issues = [
            "The appointment scheduling is not working correctly",
            "I can't access my prescription history",
            "The notification bell is showing the wrong count",
            "My medical records show incorrect information",
            "I can't update my profile information"
        ]
        
        issue_text = random.choice(issues)
        message = f"{user_name} has reported a new issue: {issue_text}"
        
        notification = NotificationService.send_notification(
            user_id=admin.id,
            message=message,
            notification_type=NotificationType.ISSUE,
            related_object_id=str(uuid.uuid4()),
            related_object_type="issue"
        )
        
        if notification:
            print(f"Created Issue notification for admin User {admin.id}: {message[:40]}...")
            
        # Also create a "resolved issue" notification
        if i % 2 == 0:  # For every other issue
            resolved_message = f"Your reported issue has been resolved: {issue_text[:50]}..."
            
            resolution_notification = NotificationService.send_notification(
                user_id=user.id,
                message=resolved_message,
                notification_type=NotificationType.ISSUE,
                related_object_id=str(uuid.uuid4()),
                related_object_type="issue"
            )
            
            if resolution_notification:
                print(f"Created Issue Resolution notification for User {user.id}: {resolved_message[:40]}...")
    
    # Chat Message notifications
    print("\nCreating Chat Message notifications...")
    for i in range(5):
        sender = random.choice(users)
        recipient = random.choice([u for u in users if u.id != sender.id])
        
        sender_name = getattr(sender, 'name', f"User {sender.id}")
        
        messages = [
            "Hi there! Just checking in to see how you're feeling today.",
            "I wanted to follow up on your latest prescription. Any side effects?",
            "Your test results came back, and everything looks normal.",
            "Could we reschedule our appointment for next week?",
            "I have a question about the medication you prescribed."
        ]
        
        message_text = random.choice(messages)
        chat_message = f"{sender_name} sent you a message: {message_text}"
        
        notification = NotificationService.send_notification(
            user_id=recipient.id,
            message=chat_message,
            notification_type=NotificationType.MESSAGE,
            related_object_id=str(uuid.uuid4()),
            related_object_type="chat"
        )
        
        if notification:
            print(f"Created Chat Message notification for User {recipient.id}: {chat_message[:40]}...")
    
    print("\nNotification creation completed!")

if __name__ == "__main__":
    create_test_notifications()
