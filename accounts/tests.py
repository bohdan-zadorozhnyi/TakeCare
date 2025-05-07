from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from .models import DoctorProfile, PatientProfile, AdminProfile
from .forms import CustomLoginForm, CustomUserCreationForm
import uuid

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            name='Test User',
            phone_number='1234567890',
            personal_id='ABC123456',
            birth_date='2000-01-01',
            gender='MALE',
            address='123 Test St',
            role='PATIENT'
        )
        
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword123',
            name='Admin User',
            phone_number='0987654321',
            personal_id='XYZ987654',
            birth_date='1990-01-01',
            gender='FEMALE',
            address='456 Admin St',
            role='ADMIN'
        )
    
    def test_user_creation(self):
        """Test user creation and attributes"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.name, 'Test User')
        self.assertEqual(self.user.role, 'PATIENT')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
    
    def test_superuser_creation(self):
        """Test superuser creation and attributes"""
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
        self.assertEqual(self.admin_user.role, 'ADMIN')
    
    def test_user_string_representation(self):
        """Test string representation of user"""
        self.assertEqual(str(self.user), 'Test User')
    
    def test_create_user_without_email(self):
        """Test creating a user without email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass')


class UserProfilesTest(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            email='patient@example.com',
            password='testpassword123',
            name='Patient User',
            phone_number='1234567890',
            personal_id='PAT123456',
            birth_date='2000-01-01',
            gender='MALE',
            address='123 Patient St',
            role='PATIENT'
        )
        
        self.doctor_user = User.objects.create_user(
            email='doctor@example.com',
            password='testpassword123',
            name='Doctor User',
            phone_number='2345678901',
            personal_id='DOC123456',
            birth_date='1980-01-01',
            gender='FEMALE',
            address='123 Doctor St',
            role='DOCTOR'
        )
        
        self.admin_user = User.objects.create_user(
            email='admin2@example.com',
            password='testpassword123',
            name='Admin User',
            phone_number='3456789012',
            personal_id='ADM123456',
            birth_date='1990-01-01',
            gender='OTHER',
            address='123 Admin St',
            role='ADMIN'
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user
        )
        
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            license_uri='https://license.example.com/doc123',
            specialization='PEDIATRICIAN',
            work_address='123 Hospital St'
        )
        
        self.admin_profile = AdminProfile.objects.create(
            user=self.admin_user
        )
    
    def test_patient_profile_relationship(self):
        """Test patient profile relationship with user"""
        self.assertEqual(self.patient_user.patient_profile, self.patient_profile)
        self.assertEqual(self.patient_profile.user, self.patient_user)
    
    def test_doctor_profile_relationship(self):
        """Test doctor profile relationship with user"""
        self.assertEqual(self.doctor_user.doctor_profile, self.doctor_profile)
        self.assertEqual(self.doctor_profile.user, self.doctor_user)
        self.assertEqual(self.doctor_profile.specialization, 'PEDIATRICIAN')
    
    def test_admin_profile_relationship(self):
        """Test admin profile relationship with user"""
        self.assertEqual(self.admin_user.admin_profile, self.admin_profile)
        self.assertEqual(self.admin_profile.user, self.admin_user)


class FormTests(TestCase):
    def test_login_form_valid(self):
        """Test login form validation with valid data"""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        form = CustomLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_login_form_invalid(self):
        """Test login form validation with invalid data"""
        form_data = {
            'email': 'invalid-email',
            'password': ''
        }
        form = CustomLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)
    
    def test_registration_form_valid(self):
        """Test registration form validation with valid data"""
        form_data = {
            'email': 'new@example.com',
            'password1': 'ComplexPwd123!',
            'password2': 'ComplexPwd123!',
            'name': 'New User',
            'phone_number': '5551234567',
            'personal_id': 'NEW123456',
            'birth_date': '2000-01-01',
            'gender': 'MALE',
            'address': '123 New St',
            'role': 'PATIENT'
        }
        form = CustomUserCreationForm(data=form_data)
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testview@example.com',
            password='viewpassword123',
            name='View Test User',
            phone_number='9876543210',
            personal_id='VIEW123456',
            birth_date='2000-01-01',
            gender='Male',
            address='123 View St',
            role='PATIENT'
        )
        
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.logout_url = reverse('logout')
        
    def test_login_page_GET(self):
        """Test login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_login_post_success(self):
        """Test successful login"""
        response = self.client.post(self.login_url, {
            'email': 'testview@example.com',
            'password': 'viewpassword123'
        })
        # Update to match the actual redirect in the login_view
        self.assertRedirects(response, reverse('home'))
    
    def test_login_post_invalid(self):
        """Test invalid login"""
        response = self.client.post(self.login_url, {
            'email': 'testview@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_register_page_GET(self):
        """Test register page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
    
    def test_logout_redirects(self):
        """Test logout redirects to login page"""
        self.client.login(email='testview@example.com', password='viewpassword123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)
