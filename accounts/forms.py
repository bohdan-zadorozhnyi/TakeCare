from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, PatientProfile, DoctorProfile, AdminProfile, DoctorCategory
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
import re
import datetime

class CustomLoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class CustomUserCreationForm(UserCreationForm):
    """ Custom sign-up form for the User model """

    email = forms.EmailField(label='Email Address', max_length=75)
    name = forms.CharField(label='Full Name', max_length=255)
    phone_number = forms.CharField(label='Phone Number', max_length=15)
    personal_id = forms.CharField(label='Personal ID', max_length=50)
    birth_date = forms.DateField(
        label='Birth Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'birthdate-picker'})
    )
    gender = forms.ChoiceField(label='Gender', choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    address = forms.CharField(label='Address',  max_length=255, min_length=5)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_number', 'address', 'birth_date', 'gender', 'password1', 'password2', 'personal_id')

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean_name(self):
        name = self.cleaned_data['name']
        if not re.match(r"^[A-Za-z\s'-]{2,}$", name):
            raise ValidationError("Name must be at least 2 characters long and contain only letters, spaces, hyphens, or apostrophes.")
        return name

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if not re.match(r"^\+?\d{7,15}$", phone_number):
            raise ValidationError("Enter a valid international phone number (e.g., +1234567890).")
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("This phone number is already registered.")
        return phone_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = datetime.date.today()
        if birth_date >= today:
            raise ValidationError("Birth date cannot be today or in the future.")
        if (today.year - birth_date.year) < 14:
            raise ValidationError("You must be at least 14 years old to register.")
        return birth_date

    def clean_personal_id(self):
        personal_id = self.cleaned_data['personal_id']
        if not re.match(r"^[A-Za-z0-9\-]{5,50}$", personal_id):
            raise ValidationError("Personal ID must be alphanumeric and 5–50 characters long.")
        if User.objects.filter(personal_id=personal_id).exists():
            raise ValidationError("This personal ID is already in registered.")
        return personal_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data["email"]
        user.role = 'PATIENT'
        user.is_active = True  # Set this to False if you use email verification
        user.name = self.cleaned_data["name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.personal_id = self.cleaned_data["personal_id"]
        user.birth_date = self.cleaned_data["birth_date"]
        user.gender = self.cleaned_data["gender"]
        user.address = self.cleaned_data["address"]

        if commit:
            user.save()
            group = Group.objects.get(name=user.role)
            user.groups.add(group)

        return user

class AdminCreateUserForm(CustomUserCreationForm):
    role = forms.ChoiceField(choices=[
        ('DOCTOR', 'Doctor'),
        ('PATIENT', 'Patient'),
        ('ADMIN', 'Administrator'),
    ])
    license_uri = forms.URLField(required=False)
    specialization = forms.ChoiceField(
        choices=DoctorCategory.choices,
        required=False
    )
    work_address = forms.CharField(max_length=100, required=False)

    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + ('role',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if user.role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
        if commit:
            user.save()
            group = Group.objects.get(name=user.role)
            user.groups.add(group)

            if user.role == 'DOCTOR':
                DoctorProfile.objects.create(
                    user=user,
                    license_uri=self.cleaned_data['license_uri'],
                    specialization=self.cleaned_data['specialization'],
                    work_address=self.cleaned_data['work_address']
                )
            elif user.role == 'PATIENT':
                PatientProfile.objects.create(user=user)
            elif user.role == 'ADMIN':
                AdminProfile.objects.create(user=user)

        return user

class EditUserProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email Address', max_length=75)
    name = forms.CharField(label='Full Name', max_length=255)
    phone_number = forms.CharField(label='Phone Number', max_length=15)
    personal_id = forms.CharField(label='Personal ID', max_length=50)
    birth_date = forms.DateField(
        label='Birth Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'birthdate-picker'})
    )
    gender = forms.ChoiceField(label='Gender', choices=[('MALE', 'Male'), ('FEMALE', 'Female'), ('OTHER', 'Other')])
    address = forms.CharField(label='Address', max_length=255, min_length=5)

    specialization = forms.ChoiceField(
        choices=DoctorCategory.choices,
        required=False
    )
    license_uri = forms.URLField(max_length=100, required=False)
    work_address = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone_number', 'personal_id', 'birth_date', 'gender', 'address', 'personal_id']

        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)

        if self.profile and isinstance(self.profile, DoctorProfile):
            self.fields['specialization'].initial = self.profile.specialization
            self.fields['license_uri'].initial = self.profile.license_uri
            self.fields['work_address'].initial = self.profile.work_address

    def save(self, commit=True):

        if self.profile and isinstance(self.profile, DoctorProfile):
            self.profile.specialization = self.cleaned_data['specialization']
            self.profile.license_uri = self.cleaned_data['license_uri']
            self.profile.work_address = self.cleaned_data['work_address']
            if commit:
                self.profile.save()

        user = super().save(commit=commit)

        return user