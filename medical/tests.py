from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from medical.models import MedicalRecord
from accounts.models import User, DoctorProfile
from medical.forms import MedicalRecordForm, EditMedicalRecordForm
from django.core.files.uploadedfile import SimpleUploadedFile
from referrals.models import DoctorCategory
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

User = get_user_model()

class MedicalRecordTests(TestCase):
    def setUp(self):
        self.client = Client()
        doctor_group = Group.objects.get(name='DOCTOR')
        patient_group = Group.objects.get(name='PATIENT')

        self.doctor = User.objects.create_user(
            email='doc@example.com',
            password='password123',
            role='DOCTOR',
            name='Dr. Andrei',
            birth_date='1980-05-05',
            phone_number='1234567890',
            personal_id='id001',
            gender='Male',
            address='123 Doctor St, Clinic City',
        )

        self.doctor.groups.add(doctor_group)

        self.patient = User.objects.create_user(
            email='patient@example.com',
            password='password123',
            role='PATIENT',
            name='John Doe',
            birth_date='1990-06-06',
            phone_number='0987654321',
            personal_id='id002',
            gender='Male',
            address='456 Patient Rd, Health City',
        )

        self.other_patient = User.objects.create_user(
            email='patient2@example.com',
            password='password1234',
            role='PATIENT',
            name='Andrei',
            birth_date='1990-06-06',
            phone_number='098734321',
            personal_id='id003',
            gender='Male',
            address='2 Patient Rd, Unhealthy City',
        )

        self.patient.groups.add(patient_group)

        self.record = MedicalRecord.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            condition='Flu',
            treatment='Rest, sleep and hydration',
            notes='Follow up in 1 week.'
        )

        perms_doc = [
            'add_medicalrecord', 'view_medicalrecord', 'change_medicalrecord',
            'delete_medicalrecord', 'search_medicalrecord', 'list_medicalrecord',
            'searchPatient_user'
        ]
        for codename in perms_doc:
            perm = Permission.objects.get(codename=codename)
            self.doctor.user_permissions.add(perm)

        perms_patient = [
            'view_medicalrecord', 'search_medicalrecord', 'list_medicalrecord'
        ]

        for codename in perms_patient:
            perm = Permission.objects.get(codename=codename)
            self.patient.user_permissions.add(perm)
            self.other_patient.user_permissions.add(perm)

        #self.doctor_profile = DoctorProfile.objects.create(user=self.doctor, specialization=DoctorCategory.OPHTHALMOLOGIST,
        #                             license_uri="https://example.com/license", work_address="Clinic Address")

    def test_medical_record_list_view_for_doctor(self):
        self.client.login(email='doc@example.com', password='password123')
        response = self.client.get(reverse('medical:medical_record_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Flu')

    def test_medical_record_detail_view_permission(self):
        self.client.login(email='patient@example.com', password='password123')
        response = self.client.get(reverse('medical:medical_record_detail', kwargs={'pk': self.record.pk}))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='patient2@example.com', password='password1234')
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

    def test_delete_requires_post_and_owner(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:delete_medical_record', args=[self.record.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(url)
        self.assertRedirects(response, reverse('medical:medical_record_list'))
        self.assertFalse(MedicalRecord.objects.filter(pk=self.record.pk).exists())

    def test_search_medical_record_requires_permission(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:search_medical_record')
        response = self.client.get(url, {'term': 'Flu'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Flu')

    def test_search_patients(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:search_patients')
        response = self.client.get(url, {'term': 'Andrei'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Andrei')

    def test_search_users_ajax(self):
        self.client.login(email='doc@example.com', password='password123')
        url = reverse('medical:search_users')
        response = self.client.get(url, {'term': 'John', 'role': 'PATIENT'})
        self.assertEqual(response.status_code, 200)
