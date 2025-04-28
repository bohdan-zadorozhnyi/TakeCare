from datetime import timezone
from django.contrib.auth.decorators import login_required, permission_required
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
from django.db.models import Q
from referrals.models import DoctorCategory
from django.urls import reverse_lazy
from django.utils import timezone
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
    viewer_is_admin = viewer.role == 'ADMIN'

    profile = None
    if user.role == 'DOCTOR':
        profile = getattr(user, 'doctor_profile', None)
    elif user.role == 'PATIENT':
        profile = getattr(user, 'patient_profile', None)
    elif user.role == 'ADMIN':
        profile = getattr(user, 'admin_profile', None)

    return render(request, 'accounts/view_profile.html', {
        'user': user,
        'viewer': viewer,
        'profile': profile,
        'is_own_profile': is_own_profile,
        'viewer_is_admin' : viewer_is_admin
    })

@login_required
@permission_required('accounts.add_user', raise_exception=True)
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
        return HttpResponseForbidden()

    profile = None
    if user.role == 'DOCTOR':
        profile = getattr(user, 'doctor_profile', None)
    elif user.role == 'PATIENT':
        profile = getattr(user, 'patient_profile', None)
    elif user.role == 'ADMIN':
        profile = getattr(user, 'admin_profile', None)

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, request.FILES, instance=user, profile=profile)

        if form.is_valid():
            form.save()
            return redirect('view_profile', user_id=user.id)
    else:
        form = EditUserProfileForm(instance=user, profile=profile)

    return render(request, 'accounts/edit_profile.html', {'form': form, 'user': user})

@login_required
def dashboard_view(request):
    user: User = request.user
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

@login_required
@permission_required('accounts.list_user', raise_exception=True)
def users_list_view(request):
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden()
    query = request.GET.get('q')
    users = User.objects.order_by('name')

    if query:
        users = users.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(personal_id__icontains=query)
        )

    paginator = Paginator(users, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/users/users_list.html', {
        'page_obj': page_obj,
        'query': query,
    })

@login_required
@permission_required('accounts.block_user', raise_exception=True)
def admin_block_unblock_user(request, user_id):
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot block yourself.")
    else:
        user.is_active = not user.is_active
        user.save()
        messages.success(request, f"User {'unblocked' if user.is_active else 'blocked'} successfully.")

    return redirect('users_list')

@login_required
@permission_required('accounts.delete_user', raise_exception=True)
def admin_delete_user(request, user_id):
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden()

    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete yourself.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")

    return redirect('users_list')
