from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

from calendar_app.models import CalendarSettings, AppointmentNote, AppointmentReminder
from appointments.models import AppointmentSlot, Appointment, AppointmentStatus
from accounts.models import User

class CalendarSettingsModelTest(TestCase):
    """Tests for the CalendarSettings model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            role='PATIENT'
        )
        
    def test_calendar_settings_creation(self):
        """Test creating a calendar setting"""
        settings = CalendarSettings.objects.create(
            user=self.user,
            default_view='week',
            reminder_before=12,
            show_past_appointments=False
        )
        
        self.assertEqual(settings.user, self.user)
        self.assertEqual(settings.default_view, 'week')
        self.assertEqual(settings.reminder_before, 12)
        self.assertEqual(settings.show_past_appointments, False)
        
    def test_settings_str_representation(self):
        """Test the string representation of calendar settings"""
        settings = CalendarSettings.objects.create(
            user=self.user,
            default_view='month'
        )
        
        self.assertEqual(str(settings), f"Calendar settings for {self.user.name}")
        
    def test_default_values(self):
        """Test default values for calendar settings"""
        settings = CalendarSettings.objects.create(user=self.user)
        
        self.assertEqual(settings.default_view, 'month')
        self.assertEqual(settings.reminder_before, 24)
        self.assertTrue(settings.show_past_appointments)


class AppointmentNoteModelTest(TestCase):
    """Tests for the AppointmentNote model"""
    
    def setUp(self):
        # Create users
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='patientpass',
            name='Patient User',
            role='PATIENT'
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@example.com',
            password='doctorpass',
            name='Doctor User',
            role='DOCTOR'
        )
        
        # Create an appointment slot
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            duration=30,
            status=AppointmentStatus.BOOKED,
            location='Main Office'
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            appointment_slot=self.slot
        )
        
    def test_note_creation(self):
        """Test creating an appointment note"""
        note = AppointmentNote.objects.create(
            appointment=self.appointment,
            created_by=self.doctor,
            content='Patient reported feeling better'
        )
        
        self.assertEqual(note.appointment, self.appointment)
        self.assertEqual(note.created_by, self.doctor)
        self.assertEqual(note.content, 'Patient reported feeling better')
        
    def test_note_str_representation(self):
        """Test string representation of appointment note"""
        note = AppointmentNote.objects.create(
            appointment=self.appointment,
            created_by=self.doctor,
            content='Follow-up required'
        )
        
        expected_str = f"Note for {self.appointment} by {self.doctor.name}"
        self.assertEqual(str(note), expected_str)


class AppointmentReminderModelTest(TestCase):
    """Tests for the AppointmentReminder model"""
    
    def setUp(self):
        # Create users
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='patientpass',
            name='Patient User',
            role='PATIENT'
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@example.com',
            password='doctorpass',
            name='Doctor User',
            role='DOCTOR'
        )
        
        # Create an appointment slot
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=timezone.now() + timedelta(days=1),
            duration=30,
            status=AppointmentStatus.BOOKED,
            location='Main Office'
        )
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            appointment_slot=self.slot
        )
        
    def test_reminder_creation(self):
        """Test creating an appointment reminder"""
        reminder_time = timezone.now() + timedelta(hours=12)
        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            user=self.patient,
            reminder_time=reminder_time
        )
        
        self.assertEqual(reminder.appointment, self.appointment)
        self.assertEqual(reminder.user, self.patient)
        self.assertEqual(reminder.reminder_time, reminder_time)
        self.assertFalse(reminder.sent)
        
    def test_reminder_str_representation(self):
        """Test string representation of appointment reminder"""
        reminder_time = timezone.now() + timedelta(hours=12)
        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            user=self.patient,
            reminder_time=reminder_time
        )
        
        expected_str = f"Reminder for {self.appointment} at {reminder_time}"
        self.assertEqual(str(reminder), expected_str)


class CalendarViewTest(TestCase):
    """Tests for the calendar views"""
    
    def setUp(self):
        # Create users
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='patientpass',
            name='Patient User',
            role='PATIENT'
        )
        
        self.doctor = User.objects.create_user(
            email='doctor@example.com',
            password='doctorpass',
            name='Doctor User',
            role='DOCTOR'
        )
        
        # Create appointment slots
        self.today = timezone.now()
        self.tomorrow = self.today + timedelta(days=1)
        
        # Available slot
        self.available_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=self.tomorrow,
            duration=30,
            status=AppointmentStatus.AVAILABLE,
            location='Main Office'
        )
        
        # Booked slot
        self.booked_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=self.tomorrow + timedelta(hours=2),
            duration=30,
            status=AppointmentStatus.BOOKED,
            location='Main Office'
        )
        
        # Create appointment for booked slot
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            appointment_slot=self.booked_slot
        )
        
        # Login credentials
        self.patient_client = Client()
        self.patient_client.force_login(self.patient)
        
        self.doctor_client = Client()
        self.doctor_client.force_login(self.doctor)
        
    def test_calendar_view_patient(self):
        """Test calendar view as patient"""
        response = self.patient_client.get(reverse('calendar_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar_app/calendar.html')
        self.assertEqual(response.context['user_role'], 'PATIENT')
        
        # Check that settings are created automatically
        settings = CalendarSettings.objects.filter(user=self.patient).first()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.default_view, 'month')
        
    def test_calendar_view_doctor(self):
        """Test calendar view as doctor"""
        response = self.doctor_client.get(reverse('calendar_view'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar_app/calendar.html')
        self.assertEqual(response.context['user_role'], 'DOCTOR')
        
        # Verify doctor-specific context data
        self.assertIn('doctor_locations', response.context)
        self.assertIn('patients', response.context)
        
    def test_get_appointments_json_doctor(self):
        """Test get_appointments_json for doctor"""
        url = reverse('get_appointments_json')
        response = self.doctor_client.get(
            url, 
            {'start': self.today.date().isoformat(), 'end': (self.today.date() + timedelta(days=7)).isoformat()}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # One available slot and one booked slot
        
    def test_get_appointments_json_patient(self):
        """Test get_appointments_json for patient"""
        url = reverse('get_appointments_json')
        response = self.patient_client.get(
            url, 
            {'start': self.today.date().isoformat(), 'end': (self.today.date() + timedelta(days=7)).isoformat()}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)  # Only the booked appointment for this patient
        
    def test_update_calendar_settings(self):
        """Test updating calendar settings"""
        settings_url = reverse('update_calendar_settings')
        
        # Create initial settings
        initial_settings = CalendarSettings.objects.create(
            user=self.patient,
            default_view='month',
            reminder_before=24,
            show_past_appointments=True
        )
        
        # Update settings through the view
        response = self.patient_client.post(settings_url, {
            'default_view': 'week',
            'reminder_before': '12',
            'show_past_appointments': 'on'
        })
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify settings were updated
        updated_settings = CalendarSettings.objects.get(user=self.patient)
        self.assertEqual(updated_settings.default_view, 'week')
        self.assertEqual(updated_settings.reminder_before, 12)
        self.assertTrue(updated_settings.show_past_appointments)
        
    def test_add_appointment_note(self):
        """Test adding a note to an appointment"""
        url = reverse('add_appointment_note', args=[self.appointment.id])
        
        # Add note as doctor
        response = self.doctor_client.post(url, {'content': 'Test note from doctor'})
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify note was added
        note = AppointmentNote.objects.filter(appointment=self.appointment).first()
        self.assertIsNotNone(note)
        self.assertEqual(note.content, 'Test note from doctor')
        self.assertEqual(note.created_by, self.doctor)
        
    def test_cancel_appointment(self):
        """Test canceling an appointment"""
        url = reverse('cancel_appointment', args=[self.appointment.id])
        
        # Cancel as patient
        response = self.patient_client.post(url)
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify appointment was deleted and slot status updated
        self.assertFalse(Appointment.objects.filter(id=self.appointment.id).exists())
        updated_slot = AppointmentSlot.objects.get(id=self.booked_slot.id)
        self.assertEqual(updated_slot.status, AppointmentStatus.AVAILABLE)
        
    def test_add_calendar_slot_doctor(self):
        """Test adding a calendar slot as doctor"""
        url = reverse('add_calendar_slot')
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        time_str = "14:00"
        
        # Add slot as doctor
        response = self.doctor_client.post(url, {
            'date': tomorrow.isoformat(),
            'time': time_str,
            'duration': '30',
            'location': 'Test Location',
            'description': 'Test slot'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify slot was created
        slot = AppointmentSlot.objects.filter(
            doctor=self.doctor,
            location='Test Location'
        ).first()
        
        self.assertIsNotNone(slot)
        self.assertEqual(slot.duration, 30)
        self.assertEqual(slot.description, 'Test slot')
        self.assertEqual(slot.status, AppointmentStatus.AVAILABLE)
        
    def test_add_calendar_slot_with_patient(self):
        """Test adding a calendar slot with a specific patient"""
        url = reverse('add_calendar_slot')
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        time_str = "15:00"
        
        # Add slot with patient as doctor
        response = self.doctor_client.post(url, {
            'date': tomorrow.isoformat(),
            'time': time_str,
            'duration': '45',
            'location': 'Virtual Visit',
            'description': 'Follow-up appointment',
            'patient': str(self.patient.id)
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify slot was created
        slot = AppointmentSlot.objects.filter(
            doctor=self.doctor,
            location='Virtual Visit',
            duration=45
        ).first()
        
        self.assertIsNotNone(slot)
        self.assertEqual(slot.status, AppointmentStatus.BOOKED)
        
        # Verify appointment was created for the patient
        appointment = Appointment.objects.filter(
            patient=self.patient,
            appointment_slot=slot
        ).first()
        
        self.assertIsNotNone(appointment)
        
    def test_add_recurring_calendar_slots(self):
        """Test adding recurring calendar slots"""
        url = reverse('add_calendar_slot')
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        time_str = "16:00"
        
        # Add recurring slots as doctor
        response = self.doctor_client.post(url, {
            'date': tomorrow.isoformat(),
            'time': time_str,
            'duration': '30',
            'location': 'Clinic A',
            'description': 'Weekly checkup',
            'is_recurring': 'on',
            'recurring_type': 'weekly',
            'recurring_count': '3'
        })
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify slots were created (3 slots: original + 2 recurring)
        slots = AppointmentSlot.objects.filter(
            doctor=self.doctor,
            location='Clinic A',
            description='Weekly checkup'
        )
        
        self.assertEqual(slots.count(), 3)
        
        # Check that dates are one week apart
        dates = sorted([slot.date.date() for slot in slots])
        self.assertEqual(dates[0], tomorrow)
        self.assertEqual(dates[1], tomorrow + timedelta(weeks=1))
        self.assertEqual(dates[2], tomorrow + timedelta(weeks=2))
