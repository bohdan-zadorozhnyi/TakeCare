from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from medical.models import MedicalRecord
from accounts.models import User
from medical.forms import MedicalRecordForm, EditMedicalRecordForm
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class MedicalRecordTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.doctor = User.objects.create_user(
            email='doc@example.com',
            password='password123',
            role='DOCTOR',
            name='Dr. Andrei'
        )
        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='password123',
            role='PATIENT',
            name='John Doe'
        )
        self.record = MedicalRecord.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            condition='Flu',
            treatment='Rest, sleep and hydration',
            notes='Follow up in 1 week.'
        )

    def test_medical_record_list_view_for_doctor(self):
        self.client.login(email='doc@example.com', password='password123')
        response = self.client.get(reverse('medical:medical_record_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Flu')

    def test_medical_record_detail_view_permission(self):
        self.client.login(email='patient@example.com', password='password123')
        response = self.client.get(reverse('medical:medical_record_detail', kwargs={'pk': self.record.pk}))
        self.assertEqual(response.status_code, 200)

        other_user = User.objects.create_user(email='other@example.com', password='password123', role='PATIENT')
        self.client.login(email='other@example.com', password='password123')
        response = self.client.get(reverse('medical:medical_record_detail', kwargs={'pk': self.record.pk}))
        self.assertEqual(response.status_code, 302)

    def test_create_medical_record(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:create_medical_record')
        file = SimpleUploadedFile('test.txt', b'Test file content')
        data = {
            'patient': self.patient.pk,
            'condition': 'Cold',
            'treatment': 'Vitamin C',
            'notes': 'Check if improves',
            'file': file
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MedicalRecord.objects.filter(condition='Cold').exists())

    def test_edit_medical_record(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:edit_medical_record', kwargs={'pk': self.record.pk})
        response = self.client.post(url, {
            'condition': 'Updated Flu',
            'treatment': 'Updated Treatment',
            'notes': 'Updated Notes'
        })
        self.assertEqual(response.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.condition, 'Updated Flu')

    def test_medical_record_form_validation(self):
        form_data = {
            'patient': self.patient.pk,
            'condition': '',
            'treatment': 'Treatment',
            'notes': 'Some notes'
        }
        form = MedicalRecordForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_edit_medical_record_form(self):
        form_data = {
            'condition': 'Headache',
            'treatment': 'Painkillers',
            'notes': 'Observe',
        }
        form = EditMedicalRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
