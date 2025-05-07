from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone  # Import timezone utility
from .models import CalendarSettings, AppointmentNote, AppointmentReminder
from appointments.models import AppointmentSlot, Appointment, AppointmentStatus
from referrals.models import DoctorCategory
from .templatetags.calendar_extras import add_minutes

User = get_user_model()

class CalendarModelTest(TestCase):
    def setUp(self):
        # Create users
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='patientpass123',
            name='Patient Test',
            phone_number='1234567890',
            personal_id='PAT123456',
            birth_date='1990-01-01',
            gender='FEMALE',
            address='123 Patient St',
            role='PATIENT'
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@example.com',
            password='doctorpass123',
            name='Doctor Test',
            phone_number='2345678901',
            personal_id='DOC123456',
            birth_date='1980-01-01',
            gender='MALE',
            address='123 Doctor St',
            role='DOCTOR'
        )
        
        # Create appointment slot with timezone-aware datetime
        self.appointment_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            location='Test Clinic',
            description='General checkup',
            date=timezone.now() + timedelta(days=7),  # Use timezone.now() instead of datetime.now()
            duration=30,
            status=AppointmentStatus.BOOKED,
            referal_type=DoctorCategory.FAMILY_MEDICINE
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            appointment_slot=self.appointment_slot
        )
        
        # Create calendar settings
        self.calendar_settings = CalendarSettings.objects.create(
            user=self.patient,
            default_view='month',
            reminder_before=24,
            show_past_appointments=True
        )
        
        # Create appointment note
        self.note = AppointmentNote.objects.create(
            appointment=self.appointment,
            created_by=self.doctor,
            content="Test note for appointment"
        )
        
        # Create appointment reminder with timezone-aware datetime
        reminder_time = timezone.now() + timedelta(days=6)  # Use timezone.now()
        self.reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            user=self.patient,
            reminder_time=reminder_time,
            sent=False
        )
    
    def test_calendar_settings_creation(self):
        """Test calendar settings creation and attributes"""
        self.assertEqual(self.calendar_settings.user, self.patient)
        self.assertEqual(self.calendar_settings.default_view, 'month')
        self.assertEqual(self.calendar_settings.reminder_before, 24)
        self.assertTrue(self.calendar_settings.show_past_appointments)
    
    def test_calendar_settings_str(self):
        """Test calendar settings string representation"""
        expected_str = f"Calendar settings for {self.patient.name}"
        self.assertEqual(str(self.calendar_settings), expected_str)
    
    def test_appointment_note_creation(self):
        """Test appointment note creation and attributes"""
        self.assertEqual(self.note.appointment, self.appointment)
        self.assertEqual(self.note.created_by, self.doctor)
        self.assertEqual(self.note.content, "Test note for appointment")
    
    def test_appointment_reminder_creation(self):
        """Test appointment reminder creation and attributes"""
        self.assertEqual(self.reminder.appointment, self.appointment)
        self.assertEqual(self.reminder.user, self.patient)
        self.assertFalse(self.reminder.sent)


class CalendarViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='patientpass123',
            name='Patient Test',
            phone_number='1234567890',
            personal_id='PAT123456',
            birth_date='1990-01-01',
            gender='FEMALE',
            address='123 Patient St',
            role='PATIENT'
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@example.com',
            password='doctorpass123',
            name='Doctor Test',
            phone_number='2345678901',
            personal_id='DOC123456',
            birth_date='1980-01-01',
            gender='MALE',
            address='123 Doctor St',
            role='DOCTOR'
        )
        
        # Create calendar settings
        self.calendar_settings = CalendarSettings.objects.create(
            user=self.patient,
            default_view='month',
            reminder_before=24,
            show_past_appointments=True
        )
        
        # Create appointment slots with timezone-aware datetime
        self.future_date = timezone.now() + timedelta(days=7)  # Use timezone.now()
        self.appointment_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            location='Test Clinic',
            description='General checkup',
            date=self.future_date,
            duration=30,
            status=AppointmentStatus.BOOKED,
            referal_type=DoctorCategory.FAMILY_MEDICINE
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            appointment_slot=self.appointment_slot
        )
    
    def test_calendar_view(self):
        """Test main calendar view"""
        self.client.login(username='patient@example.com', password='patientpass123')
        response = self.client.get(reverse('calendar_view'))
        self.assertEqual(response.status_code, 200)
    
    def test_get_appointments_json(self):
        """Test getting appointments as JSON"""
        self.client.login(username='patient@example.com', password='patientpass123')
        # Add required date parameters with timezone-aware dates
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')  # Use timezone.now()
        end_date = (timezone.now() + timedelta(days=30)).strftime('%Y-%m-%d')  # Use timezone.now()
        
        response = self.client.get(
            reverse('get_appointments_json'),
            {'start': start_date, 'end': end_date}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_appointment_detail_view(self):
        """Test appointment detail view"""
        self.client.login(username='patient@example.com', password='patientpass123')
        response = self.client.get(reverse('appointment_detail', args=[str(self.appointment.id)]))
        self.assertEqual(response.status_code, 200)
    
    def test_update_calendar_settings(self):
        """Test updating calendar settings"""
        self.client.login(username='patient@example.com', password='patientpass123')
        response = self.client.post(reverse('update_calendar_settings'), {
            'default_view': 'week',
            'reminder_before': 12,
            'show_past_appointments': False
        })
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Verify settings were updated
        self.calendar_settings.refresh_from_db()
        self.assertEqual(self.calendar_settings.default_view, 'week')
        self.assertEqual(self.calendar_settings.reminder_before, 12)
        self.assertFalse(self.calendar_settings.show_past_appointments)


class CalendarTemplateTagsTest(TestCase):
    def test_add_minutes(self):
        """Test add_minutes template tag"""
        # Test adding minutes within the same hour
        self.assertEqual(add_minutes("9:30 AM", 15), "9:45 AM")
        
        # Test adding minutes crossing the hour
        self.assertEqual(add_minutes("9:45 AM", 30), "10:15 AM")
        
        # Test adding minutes crossing from AM to PM
        self.assertEqual(add_minutes("11:45 AM", 30), "12:15 PM")
        
        # Test adding minutes in PM
        self.assertEqual(add_minutes("1:30 PM", 45), "2:15 PM")
