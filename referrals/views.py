from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Referral, ReferralDetails
from .forms import ReferralForm, ReferralDetailsFormSet
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from django.db import transaction

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@user_passes_test(is_doctor)
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        details_formset = ReferralDetailsFormSet(request.POST)
        
        # Print form data for debugging
        print("Form submitted with data:", request.POST)
        print("Form is valid:", form.is_valid())
        print("Formset is valid:", details_formset.is_valid())
        
        if not form.is_valid():
            print("Form errors:", form.errors)
        
        if not details_formset.is_valid():
            print("Formset errors:", details_formset.errors)
            print("Formset non-form errors:", details_formset.non_form_errors())
        
        if form.is_valid() and details_formset.is_valid():
            try:
                with transaction.atomic():
                    referral = form.save(commit=False)
                    referral.issuing_doctor = request.user  # Changed from doctor to issuing_doctor
                    referral.issue_date = timezone.now().date()
                    referral.save()
                    
                    details_formset.instance = referral
                    details_formset.save()
                    messages.success(request, 'Referral created successfully.')
                    return redirect('referrals:referral_detail', pk=referral.pk)
            except Exception as e:
                print("Error saving referral:", str(e))
                messages.error(request, f"Error creating referral: {str(e)}")
    else:
        form = ReferralForm()
        details_formset = ReferralDetailsFormSet()
    
    return render(request, 'referrals/referral_form.html', {
        'form': form,
        'details_formset': details_formset
    })

@login_required
def referral_list(request):
    if request.user.role == 'DOCTOR':
        referrals = Referral.objects.filter(issuing_doctor=request.user)
    else:
        referrals = Referral.objects.filter(patient=request.user)
    
    # Apply filters
    show_active = request.GET.get('active') == 'true'
    show_expired = request.GET.get('expired') == 'true'
    show_used = request.GET.get('used') == 'true'
    search_id = request.GET.get('search', '').strip()
    search_name = None
    
    today = timezone.now().date()
    
    # Filter by expiration date
    if show_active and not show_expired:
        referrals = referrals.filter(expiration_date__gte=today)
    elif show_expired and not show_active:
        referrals = referrals.filter(expiration_date__lt=today)
    
    # Filter by usage status
    if show_used:
        referrals = referrals.filter(is_used=True)
    
    # Search by user
    if search_id:
        try:
            if request.user.role == 'DOCTOR':
                search_user = User.objects.get(id=search_id, role='PATIENT')
                referrals = referrals.filter(patient=search_user)
                search_name = search_user.name
            else:
                search_user = User.objects.get(id=search_id, role='DOCTOR')
                referrals = referrals.filter(issuing_doctor=search_user)
                search_name = search_user.name
        except User.DoesNotExist:
            pass
    
    referrals = referrals.order_by('-issue_date')
    return render(request, 'referrals/referral_list.html', {
        'referrals': referrals,
        'filters': {
            'active': show_active,
            'expired': show_expired,
            'used': show_used,
            'search': search_id,
            'search_name': search_name,
        },
        'today': today,
    })

@login_required
def referral_detail(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    if request.user != referral.issuing_doctor and request.user != referral.patient:
        messages.error(request, 'You do not have permission to view this referral.')
        return redirect('referrals:referral_list')
    
    if request.method == 'POST' and 'mark_used' in request.POST and not referral.is_used:
        referral.is_used = True
        referral.save()
        messages.success(request, 'Referral marked as used.')
        return redirect('referrals:referral_detail', pk=referral.pk)
        
    today = timezone.now().date()
    return render(request, 'referrals/referral_detail.html', {
        'referral': referral,
        'today': today
    })

@login_required
@user_passes_test(is_doctor)
def search_patients(request):
    search_term = request.GET.get('term', '')
    if len(search_term) < 2:
        return JsonResponse({'results': []})
        
    patients = User.objects.filter(
        Q(role='PATIENT') &
        Q(name__icontains=search_term)
    ).values('id', 'name')[:10]
    
    results = [{'id': p['id'], 'text': p['name']} for p in patients]
    return JsonResponse({'results': results})

@login_required
def search_referrals(request):
    search_term = request.GET.get('term', '').strip()
    show_active = request.GET.get('active') == 'true'
    show_expired = request.GET.get('expired') == 'true'
    show_used = request.GET.get('used') == 'true'
    
    if request.user.role == 'DOCTOR':
        referrals = Referral.objects.filter(issuing_doctor=request.user)
    else:
        referrals = Referral.objects.filter(patient=request.user)
    
    today = timezone.now().date()
    
    # Filter by expiration date
    if show_active and not show_expired:
        referrals = referrals.filter(expiration_date__gte=today)
    elif show_expired and not show_active:
        referrals = referrals.filter(expiration_date__lt=today)
    
    # Filter by usage status
    if show_used:
        referrals = referrals.filter(is_used=True)
    
    # Search by specialist type or diagnosis
    if search_term:
        referrals = referrals.filter(
            Q(specialist_type__icontains=search_term) |
            Q(details__diagnosis__icontains=search_term)
        ).distinct()
    
    results = []
    for referral in referrals:
        details = [
            {'diagnosis': detail.diagnosis, 'priority': detail.get_priority_display()} 
            for detail in referral.details.all()
        ]
        results.append({
            'id': str(referral.id),
            'specialist_type': referral.get_specialist_type_display(),
            'details': details,
            'issue_date': referral.issue_date.strftime('%Y-%m-%d'),
            'is_expired': referral.expiration_date < today,
            'is_used': referral.is_used,
            'doctor_name': referral.issuing_doctor.name if request.user.role == 'PATIENT' else None,
            'patient_name': referral.patient.name if request.user.role == 'DOCTOR' else None,
        })
    
    return JsonResponse({'referrals': results})

@login_required
@user_passes_test(is_doctor)
def delete_referral(request, pk):
    if request.method != 'POST':
        return redirect('referrals:referral_detail', pk=pk)
        
    referral = get_object_or_404(Referral, pk=pk)
    if request.user != referral.issuing_doctor:
        messages.error(request, 'You do not have permission to delete this referral.')
        return redirect('referrals:referral_list')
    
    referral.delete()
    messages.success(request, 'Referral deleted successfully.')
    return redirect('referrals:referral_list')

@login_required
def search_users(request):
    search_term = request.GET.get('term', '')
    if len(search_term) < 2:
        return JsonResponse({'results': []})
    
    # If user is a doctor, search for patients
    # If user is a patient, search for doctors
    role_to_search = 'PATIENT' if request.user.role == 'DOCTOR' else 'DOCTOR'
    
    users = User.objects.filter(
        Q(role=role_to_search) &
        Q(name__icontains=search_term)
    ).values('id', 'name')[:10]
    
    results = [{'id': u['id'], 'text': u['name']} for u in users]
    return JsonResponse({'results': results})