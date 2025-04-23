from datetime import timezone

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages

from appointments.models import Appointment
from prescriptions.models import Prescription
from .forms import CustomLoginForm, SignUpForm, EditUserProfileForm
from TakeCare.backends import EmailAuthBackend
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.utils import timezone

User = get_user_model()


# Login view
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
# Registration view
def register_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            return redirect('login')
    else:
        form = SignUpForm()
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
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user != user and request.user.role != 'ADMIN':
        return HttpResponseForbidden("You are not allowed to edit this profile.")

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST,request.FILES, instance=user)
        if form.is_valid():
            form.save()  # Save the updated user data
            return redirect('view_profile', user_id=user.id)  # Redirect back to the view profile page
    else:
        form = EditUserProfileForm(instance=user)

    return render(request, 'accounts/edit_profile.html', {'form': form, 'user': user})


@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'PATIENT':
        upcoming_appointments = Appointment.objects.filter(
            patient=user,
            appointment_slot__date__gte=timezone.now()
        ).order_by('appointment_slot__date')
        active_prescriptions = Prescription.objects.filter(
            patient=user,
            expiration_date__gte=timezone.now()
        ).order_by('-issue_date')
        return render(request, 'accounts/dashboard/patient_dashboard.html', {
            'appointments': upcoming_appointments,
            'prescriptions': active_prescriptions,
        })


    elif user.role == 'DOCTOR':

        appointments = Appointment.objects.filter(appointment_slot__doctor=user, appointment_slot__status="Booked")
        return render(request, 'accounts/dashboard/doctor_dashboard.html', {
            'appointments': appointments,
        })
    elif user.role == 'ADMIN':
        return render(request, 'accounts/dashboard/admin_dashboard.html')

    return redirect('home')

