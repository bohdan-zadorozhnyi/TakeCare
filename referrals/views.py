from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q

from .models import Referral, DoctorCategory
from accounts.models import User
from notifications.services import NotificationService

# Helper function to check if user is a doctor
def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@user_passes_test(is_doctor)
def create_referral(request):
    """
    View for doctors to create a new referral for a patient
    """
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        specialist_type = request.POST.get('specialist_type')
        expiration_date = request.POST.get('expiration_date')
        description = request.POST.get('description', '')

        try:
            patient = User.objects.get(id=patient_id, role='PATIENT')
            
            with transaction.atomic():
                referral = Referral.objects.create(
                    patient=patient,
                    referring_doctor=request.user,  # Need to add this field to model
                    specialist_type=specialist_type,
                    issue_date=timezone.now().date(),
                    expiration_date=expiration_date,
                    description=description  # Need to add this field to model
                )
                
                # Notify patient about the new referral
                NotificationService.notify_about_referral(referral)
                
                messages.success(request, f'Referral for {patient.name} created successfully.')
                return redirect('referral_detail', referral_id=referral.id)
                
        except User.DoesNotExist:
            messages.error(request, 'Patient not found.')
        except Exception as e:
            messages.error(request, str(e))
    
    # For GET requests, show the form
    patients = User.objects.filter(role='PATIENT')
    specialist_types = DoctorCategory.choices
    
    return render(request, 'referrals/create_referral.html', {
        'patients': patients,
        'specialist_types': specialist_types
    })

@login_required
def referral_list(request):
    """
    View for listing referrals based on user role
    """
    user = request.user
    
    if user.role == 'DOCTOR':
        referrals = Referral.objects.filter(referring_doctor=user).order_by('-issue_date')
    elif user.role == 'PATIENT':
        referrals = Referral.objects.filter(patient=user).order_by('-issue_date')
    else:
        referrals = Referral.objects.none()
    
    # Filter by active/inactive
    is_active = request.GET.get('active', 'true') == 'true'
    
    if is_active:
        referrals = referrals.filter(
            expiration_date__gte=timezone.now().date(),
            is_used=False
        )
    else:
        referrals = referrals.filter(
            Q(expiration_date__lt=timezone.now().date()) | 
            Q(is_used=True)
        )
    
    return render(request, 'referrals/referral_list.html', {
        'referrals': referrals,
        'is_active': is_active
    })

@login_required
def referral_detail(request, referral_id):
    """
    View for displaying referral details
    """
    referral = get_object_or_404(Referral, id=referral_id)
    
    # Check if user has permission to view this referral
    user = request.user
    if user.role == 'PATIENT' and referral.patient != user:
        messages.error(request, "You don't have permission to view this referral.")
        return redirect('referral_list')
    elif user.role == 'DOCTOR' and referral.referring_doctor != user:
        messages.error(request, "You don't have permission to view this referral.")
        return redirect('referral_list')
    
    return render(request, 'referrals/referral_detail.html', {
        'referral': referral,
        'today': timezone.now().date()
    })

@login_required
@user_passes_test(is_doctor)
def search_patients(request):
    """
    AJAX endpoint for searching patients when creating a referral
    """
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'results': []})
        
    patients = User.objects.filter(
        role='PATIENT',
        name__icontains=query
    ).values('id', 'name', 'email')[:10]
    
    return JsonResponse({
        'results': list(patients)
    })