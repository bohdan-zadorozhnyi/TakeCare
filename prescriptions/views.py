from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from .models import Prescription
from .forms import PrescriptionForm, PrescriptionMedicationFormSet
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from django.db import transaction

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@permission_required("prescriptions.add_prescription", raise_exception=True)
def create_prescription(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        medication_formset = PrescriptionMedicationFormSet(request.POST)
        
        if form.is_valid() and medication_formset.is_valid():
            try:
                with transaction.atomic():
                    prescription = form.save(commit=False)
                    prescription.doctor = request.user
                    prescription.issue_date = timezone.now().date()
                    prescription.save()
                    
                    medication_formset.instance = prescription
                    medication_formset.save()
                    messages.success(request, 'Prescription created successfully.')
                    return redirect('prescriptions:prescription_detail', pk=prescription.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = PrescriptionForm()
        medication_formset = PrescriptionMedicationFormSet()
    
    return render(request, 'prescriptions/prescription_form.html', {
        'form': form,
        'medication_formset': medication_formset
    })

@login_required
@permission_required("prescriptions.list_prescription", raise_exception=True)
def prescription_list(request):
    if request.user.role == 'DOCTOR':
        prescriptions = Prescription.objects.filter(doctor=request.user)
    else:
        prescriptions = Prescription.objects.filter(patient=request.user)
    
    # Apply filters
    show_active = request.GET.get('active') == 'true'
    show_expired = request.GET.get('expired') == 'true'
    search_id = request.GET.get('search', '').strip()
    search_name = None
    
    today = timezone.now().date()
    
    if show_active and not show_expired:
        prescriptions = prescriptions.filter(expiration_date__gte=today)
    elif show_expired and not show_active:
        prescriptions = prescriptions.filter(expiration_date__lt=today)
    # If both or neither are selected, show all prescriptions
    
    if search_id:
        try:
            if request.user.role == 'DOCTOR':
                search_user = User.objects.get(id=search_id, role='PATIENT')
                prescriptions = prescriptions.filter(patient=search_user)
                search_name = search_user.name
            else:
                search_user = User.objects.get(id=search_id, role='DOCTOR')
                prescriptions = prescriptions.filter(doctor=search_user)
                search_name = search_user.name
        except User.DoesNotExist:
            pass
    
    prescriptions = prescriptions.order_by('-issue_date')
    return render(request, 'prescriptions/prescription_list.html', {
        'prescriptions': prescriptions,
        'filters': {
            'active': show_active,
            'expired': show_expired,
            'search': search_id,
            'search_name': search_name,
        },
        'today': today,
    })

@login_required
@permission_required("prescriptions.view_prescription", raise_exception=True)
def prescription_detail(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.user != prescription.doctor and request.user != prescription.patient:
        messages.error(request, 'You do not have permission to view this prescription.')
        return redirect('prescriptions:prescription_list')
    return render(request, 'prescriptions/prescription_detail.html', {'prescription': prescription})

@login_required
@permission_required("accounts.searchPatient_user", raise_exception=True)
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
def search_users(request):
    search_term = request.GET.get('term', '')
    role = request.GET.get('role', '')
    
    if len(search_term) < 2 or role not in ['DOCTOR', 'PATIENT']:
        return JsonResponse({'results': []})
    
    users = User.objects.filter(
        role=role,
        name__icontains=search_term
    ).values('id', 'name')[:10]
    
    results = [{'id': str(user['id']), 'text': user['name']} for user in users]
    return JsonResponse({'results': results})

@login_required
@permission_required("prescriptions.search_prescription", raise_exception=True)
def search_prescriptions(request):
    search_term = request.GET.get('term', '').strip()
    show_active = request.GET.get('active') == 'true'
    show_expired = request.GET.get('expired') == 'true'
    
    if request.user.role == 'DOCTOR':
        prescriptions = Prescription.objects.filter(doctor=request.user)
    else:
        prescriptions = Prescription.objects.filter(patient=request.user)
    
    today = timezone.now().date()
    
    if show_active and not show_expired:
        prescriptions = prescriptions.filter(expiration_date__gte=today)
    elif show_expired and not show_active:
        prescriptions = prescriptions.filter(expiration_date__lt=today)
    
    if search_term:
        prescriptions = prescriptions.filter(
            medications__medication_name__icontains=search_term
        ).distinct()
    
    results = []
    for prescription in prescriptions:
        medications = [
            {'name': med.medication_name, 'dosage': med.dosage} 
            for med in prescription.medications.all()
        ]
        results.append({
            'id': str(prescription.id),
            'medications': medications,
            'issue_date': prescription.issue_date.strftime('%Y-%m-%d'),
            'is_expired': prescription.expiration_date < today,
            'doctor_name': prescription.doctor.name if request.user.role == 'PATIENT' else None,
            'doctor_avatar_url': prescription.doctor.avatar.url if request.user.role == 'PATIENT' else None,
            'patient_name': prescription.patient.name if request.user.role == 'DOCTOR' else None,
        })
    
    return JsonResponse({'prescriptions': results})

@login_required
@permission_required("prescriptions.delete_prescription", raise_exception=True)
def delete_prescription(request, pk):
    if request.method != 'POST':
        return redirect('prescriptions:prescription_detail', pk=pk)
        
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.user != prescription.doctor:
        messages.error(request, 'You do not have permission to delete this prescription.')
        return redirect('prescriptions:prescription_list')
    
    prescription.delete()
    messages.success(request, 'Prescription deleted successfully.')
    return redirect('prescriptions:prescription_list')