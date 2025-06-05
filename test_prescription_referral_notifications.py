#!/usr/bin/env python
# test_prescription_referral_notifications.py
"""
This script tests the creation of prescriptions and referrals
and verifies that notifications are properly sent.
"""
import os
import sys
import django
import logging
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models
from django.contrib.auth import get_user_model
from prescriptions.models import Prescription, PrescriptionMedication
from referrals.models import Referral
from notifications.models import Notification, NotificationType

User = get_user_model()

def test_prescription_notification():
    """Test that a prescription creation sends a notification"""
    logger.info("Testing prescription notification...")
    
    # Find a doctor and patient
    try:
        doctor = User.objects.filter(role='DOCTOR').first()
        patient = User.objects.filter(role='PATIENT').first()
        
        if not doctor or not patient:
            logger.error("Could not find a doctor and patient. Please ensure they exist in the database.")
            return False
            
        # Create a prescription
        today = datetime.now().date()
        expiry = today + timedelta(days=30)
        
        prescription = Prescription.objects.create(
            doctor=doctor,
            patient=patient,
            notes="Test prescription for notification testing",
            issue_date=today,
            expiration_date=expiry
        )
        
        # Add a medication to the prescription
        PrescriptionMedication.objects.create(
            prescription=prescription,
            medication_name="Test Medication",
            dosage="10mg daily"
        )
        
        # Check if notification was created
        notification = Notification.objects.filter(
            receiver=patient,
            notification_type=NotificationType.PRESCRIPTION,
            object_id=prescription.id
        ).first()
        
        if notification:
            logger.info(f"✅ SUCCESS: Prescription notification created: {notification.message}")
            return True
        else:
            logger.error("❌ FAILED: No prescription notification was created")
            return False
            
    except Exception as e:
        logger.error(f"Error testing prescription notification: {e}")
        return False

def test_referral_notification():
    """Test that a referral creation sends a notification"""
    logger.info("Testing referral notification...")
    
    # Find a doctor and patient
    try:
        doctor = User.objects.filter(role='DOCTOR').first()
        patient = User.objects.filter(role='PATIENT').first()
        
        if not doctor or not patient:
            logger.error("Could not find a doctor and patient. Please ensure they exist in the database.")
            return False
            
        # Create a referral
        today = datetime.now().date()
        expiry = today + timedelta(days=90)
        
        referral = Referral.objects.create(
            issuing_doctor=doctor,
            patient=patient,
            specialist_type='DERMATOLOGIST',
            notes="Test referral for notification testing",
            issue_date=today,
            expiration_date=expiry,
            is_used=False
        )
        
        # Check if notification was created
        notification = Notification.objects.filter(
            receiver=patient,
            notification_type=NotificationType.REFERRAL,
            object_id=referral.id
        ).first()
        
        if notification:
            logger.info(f"✅ SUCCESS: Referral notification created: {notification.message}")
            return True
        else:
            logger.error("❌ FAILED: No referral notification was created")
            return False
            
    except Exception as e:
        logger.error(f"Error testing referral notification: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting prescription and referral notification tests...")
    
    # Test both notification types
    prescription_success = test_prescription_notification()
    referral_success = test_referral_notification()
    
    # Print summary
    logger.info("==== TEST RESULTS ====")
    logger.info(f"Prescription notification: {'✅ Success' if prescription_success else '❌ Failed'}")
    logger.info(f"Referral notification: {'✅ Success' if referral_success else '❌ Failed'}")
    
    # Exit with appropriate status code
    sys.exit(0 if prescription_success and referral_success else 1)
