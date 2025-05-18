from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from .forms import MedicalRecordForm, EditMedicalRecordForm
from .models import MedicalRecord
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from accounts.models import User
from django.utils import timezone

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@user_passes_test(is_doctor)
def create_medical_record(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    medical_record = form.save(commit=False)
                    medical_record.doctor = request.user
                    medical_record.save()
                    messages.success(request, 'Medical record created successfully.')
                    return redirect('medical:medical_record_detail', pk=medical_record.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = MedicalRecordForm()

    return render(request, 'medical/create_medical_record.html', {'form': form})


@login_required
def medical_record_list(request):
    user = request.user
    queryset = MedicalRecord.objects.all()

    if user.role == 'DOCTOR':
        queryset = queryset.filter(doctor=user)
    elif user.role == 'PATIENT':
        queryset = queryset.filter(patient=user)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    condition = request.GET.get('condition')

    if date_from:
        queryset = queryset.filter(date__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__date__lte=date_to)
    if condition:
        queryset = queryset.filter(condition__icontains=condition)

    return render(request, 'medical/medical_record_list.html', {
        'medical_records': queryset.order_by('-date'),
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'condition': condition,
        }
    })



@login_required
def medical_record_detail(request, pk):
    medical_record = get_object_or_404(MedicalRecord, pk=pk)
    if request.user != medical_record.doctor and request.user != medical_record.patient:
        messages.error(request, 'You do not have permission to view this medical record.')
        return redirect('medical/medical_record_list.html')
    return render(request, 'medical/medical_record_detail.html', {'medical_record': medical_record})


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
@user_passes_test(is_doctor)
def delete_medical_record(request, pk):
    if request.method != 'POST':
        return redirect('medical:medical_record_detail', pk=pk)

    prescription = get_object_or_404(MedicalRecord, pk=pk)
    if request.user != prescription.doctor:
        messages.error(request, 'You do not have permission to delete this medical record.')
        return redirect('medical:medical_record_detail')

    prescription.delete()
    messages.success(request, 'Medical record deleted successfully.')
    return redirect('medical:medical_record_detail')

@login_required
def search_medical_record(request):
    search_term = request.GET.get('term', '').strip()
    filter_condition = request.GET.get('filter_condition', '').strip()
    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'desc')

    if request.user.role == 'DOCTOR':
        records = MedicalRecord.objects.filter(doctor=request.user)
    else:
        records = MedicalRecord.objects.filter(patient=request.user)

    if filter_condition:
        records = records.filter(condition__icontains=filter_condition)

    if search_term:
        records = records.filter(
            Q(condition__icontains=search_term) |
            Q(treatment__icontains=search_term) |
            Q(notes__icontains=search_term)
        ).distinct()

    if sort_by not in ['date', 'condition']:
        sort_by = 'date'
    if order == 'asc':
        records = records.order_by(sort_by)
    else:
        records = records.order_by(f'-{sort_by}')

    results = []
    for record in records:
        results.append({
            'id': str(record.id),
            'date': record.date.strftime('%Y-%m-%d %H:%M'),
            'condition': record.condition,
            'treatment': record.treatment,
            'doctor_name': record.doctor.name if request.user.role == 'PATIENT' else None,
            'patient_name': record.patient.name if request.user.role == 'DOCTOR' else None,
        })

    return JsonResponse({'medical_records': results})

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
@user_passes_test(is_doctor)
def edit_medical_record(request, pk):
    medical_record = get_object_or_404(MedicalRecord, pk=pk)

    if medical_record.doctor != request.user:
        return HttpResponseForbidden("You are not allowed to edit this record.")

    if request.method == 'POST':
        form = EditMedicalRecordForm(request.POST, request.FILES, instance=medical_record)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, "Medical record updated successfully.")
                    return redirect('medical:medical_record_detail', pk=medical_record.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = EditMedicalRecordForm(instance=medical_record)

    return render(request, 'medical/edit_medical_record.html', {
        'form': form,
        'record': medical_record
    })
