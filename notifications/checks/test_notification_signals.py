#!/usr/bin/env python
"""
Script to create real model events that should trigger notification signals
"""
import os
import django
import uuid
import random
from datetime import datetime

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

# Import Django models
from django.contrib.auth import get_user_model
from notifications.models import NotificationType, Notification

User = get_user_model()

def create_test_model_events():
    """Create real model instances that should trigger notifications via signals"""
    print("Creating test model events to trigger notification signals...")
    
    # Get some test users
    try:
        patients = User.objects.filter(role='PATIENT')
        doctors = User.objects.filter(role='DOCTOR')
        
        if not patients.exists() or not doctors.exists():
            print("Need at least one patient and one doctor user. Skipping model events.")
            return
        
        # Select test users
        test_patient = patients.first()
        test_doctor = doctors.first()
        
        print(f"Using test users: Patient {test_patient.id}, Doctor {test_doctor.id}")
        
        # Clear existing notifications for these users for cleaner testing
        Notification.objects.filter(receiver__in=[test_patient, test_doctor]).delete()
        print("Cleared existing notifications for test users")
        
        # 1. Create a Medical Record - should trigger medical_record notification
        from medical.models import MedicalRecord
        
        medical_record = MedicalRecord.objects.create(
            patient=test_patient,
            doctor=test_doctor,
            condition="Seasonal Allergies Test",
            treatment="Antihistamines and nasal spray",
            notes="Patient reported significant improvement with current treatment"
        )
        print(f"Created Medical Record #{medical_record.id}")
        
        # 2. Create an Issue - should trigger issue notification
        from issues.models import Issue
        
        issue = Issue.objects.create(
            user=test_patient,
            message="Test issue: Cannot access my prescription history",
            is_resolved=False
        )
        print(f"Created Issue #{issue.id}")
        
        # Update the issue to resolved - should trigger issue resolved notification
        issue.is_resolved = True
        issue.save()
        print(f"Resolved Issue #{issue.id}")
        
        # 3. Create a Chat Message - should trigger message notification
        from chat.models import ChatRoom, Message
        
        # Find or create a chat room for these users
        chat_room, created = ChatRoom.objects.get_or_create(name=f"Chat {test_doctor.id} - {test_patient.id}")
        if created:
            chat_room.participants.add(test_doctor, test_patient)
            print(f"Created new ChatRoom #{chat_room.id}")
        else:
            print(f"Using existing ChatRoom #{chat_room.id}")
        
        # Create a message from doctor to patient
        message = Message.objects.create(
            chatroom=chat_room,
            sender=test_doctor,
            content="Hello, this is a test message about your recent appointment."
        )
        print(f"Created Message #{message.id} from doctor to patient")
        
        # Wait a moment to verify notifications were created
        print("\nChecking for notifications...")
        
        # Get notifications created by the signals
        medical_record_notifications = Notification.objects.filter(
            receiver=test_patient,
            notification_type=NotificationType.MEDICAL_RECORD
        ).count()
        
        issue_notifications = Notification.objects.filter(
            notification_type=NotificationType.ISSUE
        ).count()
        
        message_notifications = Notification.objects.filter(
            notification_type=NotificationType.MESSAGE
        ).count()
        
        print(f"Medical Record notifications found: {medical_record_notifications}")
        print(f"Issue notifications found: {issue_notifications}")
        print(f"Message notifications found: {message_notifications}")
        
        if medical_record_notifications > 0 and issue_notifications > 0 and message_notifications > 0:
            print("\nSUCCESS: All signal-based notifications are working correctly!")
        else:
            print("\nWARNING: Some signal-based notifications may not be working properly.")
    
    except Exception as e:
        print(f"Error creating model events: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_model_events()
