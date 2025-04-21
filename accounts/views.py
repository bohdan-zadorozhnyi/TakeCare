from datetime import timezone

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from .models import PatientProfile, DoctorProfile, AdminProfile
from appointments.models import Appointment
from prescriptions.models import Prescription
from .forms import CustomLoginForm, CustomUserCreationForm, EditUserProfileForm, AdminCreateUserForm
from TakeCare.backends import EmailAuthBackend
from django.contrib.auth.views import PasswordResetView
from referrals.models import DoctorCategory
from django.urls import reverse_lazy
User = get_user_model()

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            backend = EmailAuthBackend()
            user = backend.authenticate(request=request, username=email, password=password)
            print(f"DEBUG: Found user - {user}")
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Email or Password is incorrect.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset/password_reset_form.html'
    email_template_name = 'accounts/password_reset/password_reset_email.html'
    # subject_template_name = 'accounts/password_reset/password_reset_subject.txt'
    from_email = 'support@takecare.local'

@login_required
def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    viewer = request.user

    is_own_profile = viewer.id == user.id

    return render(request, 'accounts/view_profile.html', {
        'user': user,
        'viewer': viewer,
        'is_own_profile': is_own_profile
    })

@login_required
def admin_create_user_view(request):
    user: User = request.user
    if user.role != 'ADMIN':
        return HttpResponseForbidden("You are not allowed to create users.")

    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect('dashboard')
    else:
        form = AdminCreateUserForm()

    return render(request, 'accounts/admin_create_user.html', {'form': form})

@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user != user and request.user.role != 'ADMIN':
        return HttpResponseForbidden("You are not allowed to edit this profile.")

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()  # Save the updated user data
            return redirect('view_profile', user_id=user.id)  # Redirect back to the view profile page
    else:
        form = EditUserProfileForm(instance=user)

    return render(request, 'accounts/edit_profile.html', {'form': form, 'user': user})


@login_required
def dashboard_view(request):
    user: User = request.user
    if user.role == 'PATIENT':
        patient_profile = request.user.patient_profile
        appointments = Appointment.objects.filter(patient=patient_profile)
        subscriptions = Prescription.objects.filter(patient=patient_profile)
        return render(request, 'accounts/dashboard/patient_dashboard.html', {
            'appointments': appointments,
            'subscriptions': subscriptions,
        })

    elif user.role == 'DOCTOR':
        doctor_profile = request.user.doctor_profile
        appointments = Appointment.objects.filter(doctor=doctor_profile)
        subscriptions = Prescription.objects.filter(doctor=doctor_profile)
        return render(request, 'accounts/dashboard/doctor_dashboard.html', {
            'appointments': appointments,
        })
    elif user.role == 'ADMIN':
        return render(request, 'accounts/dashboard/admin_dashboard.html')

    return redirect('home')

