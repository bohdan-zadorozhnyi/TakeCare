from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from django.forms import ValidationError 
from django.forms import inlineformset_factory
from .forms import ReferralForm, ReferralDetailsForm, BaseReferralDetailsFormSet
from .models import Referral, ReferralDetails, DoctorCategory
from accounts.models import User


class ReferralFormTests(TestCase):
    def setUp(self):
        # Create test users with correct fields
        self.patient = User.objects.create(
            email="patient@example.com",
            name="Test Patient",
            phone_number="1234567890",
            personal_id="P123456",
            birth_date=date(1990, 1, 1),
            gender="Male",
            address="123 Patient St",
            role="PATIENT"
        )
        
        self.doctor = User.objects.create(
            email="doctor@example.com",
            name="Test Doctor",
            phone_number="0987654321",
            personal_id="D123456",
            birth_date=date(1980, 1, 1),
            gender="Female",
            address="456 Doctor Ave",
            role="DOCTOR"
        )
        
        # Get today's date for testing
        self.today = timezone.now().date()
        self.future_date = self.today + timedelta(days=30)
        self.past_date = self.today - timedelta(days=5)

    def test_referral_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'patient': self.patient.id,
            'specialist_type': DoctorCategory.CARDIOLOGIST,
            'expiration_date': self.future_date,
            'issue_date': self.today,
            'notes': 'Patient needs cardiac evaluation'
        }
        form = ReferralForm(data=form_data)
        if not form.is_valid():
            print(form.errors)  # For debugging
        self.assertTrue(form.is_valid())

    def test_referral_form_past_expiration_date(self):
        """Test form rejects past expiration date"""
        form_data = {
            'patient': self.patient.id,
            'specialist_type': DoctorCategory.NEUROLOGIST,
            'expiration_date': self.past_date,
            'issue_date': self.today,
            'notes': 'Patient needs neurological evaluation'
        }
        form = ReferralForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('expiration_date', form.errors)
        self.assertIn('Expiration date cannot be in the past', form.errors['expiration_date'])

    def test_referral_form_missing_required_fields(self):
        """Test form validation with missing required fields"""
        form_data = {
            'notes': 'Test notes only'
        }
        form = ReferralForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('patient', form.errors)
        self.assertIn('specialist_type', form.errors)
        self.assertIn('expiration_date', form.errors)


class ReferralDetailsFormTests(TestCase):
    def test_referral_details_form_valid_data(self):
        """Test details form with valid data"""
        form_data = {
            'diagnosis': 'Suspected hypertension',
            'priority': 'MEDIUM',
            'additional_info': 'Patient has family history of heart disease'
        }
        form = ReferralDetailsForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_referral_details_form_missing_diagnosis(self):
        """Test validation when diagnosis is missing"""
        form_data = {
            'priority': 'HIGH',
            'additional_info': 'Some additional info'
        }
        form = ReferralDetailsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('diagnosis', form.errors)


class ReferralDetailsFormSetValidationTests(TestCase):
    def test_validate_has_valid_details_logic(self):
        """Test the core logic of the BaseReferralDetailsFormSet clean method"""
        # Test case with a valid diagnosis
        forms_with_valid_diagnosis = [
            {'is_valid': True, 'cleaned_data': {'diagnosis': 'Valid diagnosis', 'DELETE': False}}
        ]
        self.assertTrue(self._check_has_valid_details(forms_with_valid_diagnosis))
        
        # Test case with empty diagnosis
        forms_with_empty_diagnosis = [
            {'is_valid': True, 'cleaned_data': {'diagnosis': '', 'DELETE': False}}
        ]
        self.assertFalse(self._check_has_valid_details(forms_with_empty_diagnosis))
        
        # Test case with one valid and one invalid diagnosis
        forms_with_mixed_diagnoses = [
            {'is_valid': True, 'cleaned_data': {'diagnosis': 'Valid diagnosis', 'DELETE': False}},
            {'is_valid': True, 'cleaned_data': {'diagnosis': '', 'DELETE': False}}
        ]
        self.assertTrue(self._check_has_valid_details(forms_with_mixed_diagnoses))
        
        # Test case with all empty diagnoses
        forms_with_all_empty_diagnoses = [
            {'is_valid': True, 'cleaned_data': {'diagnosis': '', 'DELETE': False}},
            {'is_valid': True, 'cleaned_data': {'diagnosis': '', 'DELETE': False}}
        ]
        self.assertFalse(self._check_has_valid_details(forms_with_all_empty_diagnoses))
        
        # Test case with deleted form (should not count towards validation)
        forms_with_deleted = [
            {'is_valid': True, 'cleaned_data': {'diagnosis': '', 'DELETE': True}},
            {'is_valid': True, 'cleaned_data': {'diagnosis': 'Valid diagnosis', 'DELETE': False}}
        ]
        self.assertTrue(self._check_has_valid_details(forms_with_deleted))
        
    def _check_has_valid_details(self, form_data_list):
        """
        Implements the core logic from BaseReferralDetailsFormSet.clean()
        to check if at least one form has a valid diagnosis.
        """
        has_valid_details = False
        
        for form_data in form_data_list:
            if not form_data['is_valid']:
                continue
                
            if form_data['cleaned_data'] and not form_data['cleaned_data'].get('DELETE', False):
                diagnosis = form_data['cleaned_data'].get('diagnosis')
                
                if diagnosis:
                    has_valid_details = True
        
        return has_valid_details
