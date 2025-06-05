#!/usr/bin/env python
# docker_debug_notifications.py
"""
This script helps debug notification issues in the Docker environment.
It checks signal registration, creates test notifications, and verifies that they're received.
"""
import os
import sys
import django
import logging
import inspect
import traceback
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_import_status():
    """Check if all modules are correctly imported"""
    from notifications.signals import (
        REFERRALS_ENABLED, PRESCRIPTIONS_ENABLED, APPOINTMENTS_ENABLED,
        MEDICAL_RECORDS_ENABLED, ISSUES_ENABLED, CHAT_ENABLED
    )
    
    logger.info("=== Module Import Status ===")
    logger.info(f"Referrals module: {'✅ Enabled' if REFERRALS_ENABLED else '❌ Not imported'}")
    logger.info(f"Prescriptions module: {'✅ Enabled' if PRESCRIPTIONS_ENABLED else '❌ Not imported'}")
    logger.info(f"Appointments module: {'✅ Enabled' if APPOINTMENTS_ENABLED else '❌ Not imported'}")
    logger.info(f"Medical Records module: {'✅ Enabled' if MEDICAL_RECORDS_ENABLED else '❌ Not imported'}")
    logger.info(f"Issues module: {'✅ Enabled' if ISSUES_ENABLED else '❌ Not imported'}")
    logger.info(f"Chat module: {'✅ Enabled' if CHAT_ENABLED else '❌ Not imported'}")

def check_signal_registration():
    """Check if signal handlers are properly registered"""
    from django.db.models.signals import post_save
    from django.dispatch.dispatcher import _live_receivers
    
    try:
        # Check referral signals
        from referrals.models import Referral
        referral_receivers = _live_receivers(post_save, Referral)
        logger.info(f"Referral signal receivers: {len(referral_receivers)} found")
        for receiver in referral_receivers:
            logger.info(f"  - {receiver.__module__}.{receiver.__name__ if hasattr(receiver, '__name__') else str(receiver)}")
        
        # Check prescription signals
        from prescriptions.models import Prescription
        prescription_receivers = _live_receivers(post_save, Prescription)
        logger.info(f"Prescription signal receivers: {len(prescription_receivers)} found")
        for receiver in prescription_receivers:
            logger.info(f"  - {receiver.__module__}.{receiver.__name__ if hasattr(receiver, '__name__') else str(receiver)}")
    
    except ImportError as e:
        logger.error(f"Error importing models: {e}")
    except Exception as e:
        logger.error(f"Error checking signal registration: {e}")
        traceback.print_exc()

def test_notification_service():
    """Test if the notification service is working directly"""
    from notifications.services import NotificationService
    from notifications.models import NotificationType, Notification
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        # Find a test user
        test_user = User.objects.first()
        if not test_user:
            logger.error("No users found in the database")
            return False
        
        # Create a direct test notification
        test_message = f"Test notification from debug script - {datetime.now().strftime('%H:%M:%S')}"
        notification = NotificationService.send_notification(
            user_id=test_user.id,
            message=test_message,
            notification_type=NotificationType.SYSTEM,
            related_object_type="debug_test"
        )
        
        if notification:
            logger.info(f"✅ Test notification created successfully for user {test_user.id}")
            return True
        else:
            logger.error("❌ Failed to create test notification")
            return False
    
    except Exception as e:
        logger.error(f"Error testing notification service: {e}")
        traceback.print_exc()
        return False

def test_prescription_creation():
    """Test creating a prescription to check if notification is triggered"""
    from prescriptions.models import Prescription, PrescriptionMedication
    from notifications.models import Notification, NotificationType
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        # Find a doctor and patient
        doctor = User.objects.filter(role='DOCTOR').first()
        patient = User.objects.filter(role='PATIENT').first()
        
        if not doctor or not patient:
            logger.error("Doctor or patient not found")
            return False
        
        # Create a prescription
        today = datetime.now().date()
        expiry = today + timedelta(days=30)
        
        prescription = Prescription.objects.create(
            doctor=doctor,
            patient=patient,
            notes=f"Debug test prescription - {datetime.now().strftime('%H:%M:%S')}",
            issue_date=today,
            expiration_date=expiry
        )
        
        # Add medication to the prescription
        PrescriptionMedication.objects.create(
            prescription=prescription,
            medication_name="Debug Test Medication",
            dosage="10mg daily"
        )
        
        logger.info(f"Created test prescription {prescription.id}")
        
        # Check if notification was created (with a small delay)
        import time
        time.sleep(1)  # Give the signal time to process
        
        notification = Notification.objects.filter(
            receiver=patient,
            notification_type=NotificationType.PRESCRIPTION,
            object_id=prescription.id
        ).first()
        
        if notification:
            logger.info(f"✅ Prescription notification created: {notification.message}")
            return True
        else:
            logger.error("❌ No prescription notification was created")
            return False
    
    except Exception as e:
        logger.error(f"Error testing prescription creation: {e}")
        traceback.print_exc()
        return False

def test_referral_creation():
    """Test creating a referral to check if notification is triggered"""
    from referrals.models import Referral
    from notifications.models import Notification, NotificationType
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        # Find a doctor and patient
        doctor = User.objects.filter(role='DOCTOR').first()
        patient = User.objects.filter(role='PATIENT').first()
        
        if not doctor or not patient:
            logger.error("Doctor or patient not found")
            return False
        
        # Create a referral
        today = datetime.now().date()
        expiry = today + timedelta(days=90)
        
        referral = Referral.objects.create(
            issuing_doctor=doctor,
            patient=patient,
            specialist_type='DERMATOLOGIST',
            notes=f"Debug test referral - {datetime.now().strftime('%H:%M:%S')}",
            issue_date=today,
            expiration_date=expiry,
            is_used=False
        )
        
        logger.info(f"Created test referral {referral.id}")
        
        # Check if notification was created (with a small delay)
        import time
        time.sleep(1)  # Give the signal time to process
        
        notification = Notification.objects.filter(
            receiver=patient,
            notification_type=NotificationType.REFERRAL,
            object_id=referral.id
        ).first()
        
        if notification:
            logger.info(f"✅ Referral notification created: {notification.message}")
            return True
        else:
            logger.error("❌ No referral notification was created")
            return False
    
    except Exception as e:
        logger.error(f"Error testing referral creation: {e}")
        traceback.print_exc()
        return False

def inspect_models():
    """Inspect relevant models to check fields"""
    try:
        from referrals.models import Referral
        from prescriptions.models import Prescription
        
        logger.info("=== Model Inspection ===")
        
        # Inspect Referral model
        logger.info("Referral model fields:")
        for field in Referral._meta.get_fields():
            logger.info(f"  - {field.name} ({type(field).__name__})")
        
        # Inspect Prescription model
        logger.info("Prescription model fields:")
        for field in Prescription._meta.get_fields():
            logger.info(f"  - {field.name} ({type(field).__name__})")
    
    except ImportError as e:
        logger.error(f"Error importing models for inspection: {e}")
    except Exception as e:
        logger.error(f"Error during model inspection: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("=== Starting Notification System Debug ===")
    
    # Check environment
    logger.info(f"Django Settings Module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Run tests
    check_import_status()
    logger.info("\n=== Signal Registration Check ===")
    check_signal_registration()
    
    logger.info("\n=== Model Inspection ===")
    inspect_models()
    
    logger.info("\n=== Notification Service Test ===")
    notification_service_ok = test_notification_service()
    
    logger.info("\n=== Prescription Notification Test ===")
    prescription_ok = test_prescription_creation()
    
    logger.info("\n=== Referral Notification Test ===")
    referral_ok = test_referral_creation()
    
    # Print summary
    logger.info("\n=== Debug Summary ===")
    logger.info(f"Notification service test: {'✅ Success' if notification_service_ok else '❌ Failed'}")
    logger.info(f"Prescription notification test: {'✅ Success' if prescription_ok else '❌ Failed'}")
    logger.info(f"Referral notification test: {'✅ Success' if referral_ok else '❌ Failed'}")
    
    if all([notification_service_ok, prescription_ok, referral_ok]):
        logger.info("\n✅ All tests passed! The notification system appears to be working correctly.")
        sys.exit(0)
    else:
        logger.info("\n❌ Some tests failed. See logs above for details.")
        sys.exit(1)
