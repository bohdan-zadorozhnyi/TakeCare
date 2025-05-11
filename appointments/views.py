from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import AppointmentSlot, Appointment, AppointmentStatus
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict
from notifications.models import Notification
from accounts.models import PatientProfile, DoctorProfile, AdminProfile
from django.contrib.auth.decorators import permission_required, login_required
from django.db.models import IntegerField, DateTimeField, Q, ExpressionWrapper, F
from django.db.models.functions import Cast
from datetime import datetime, timedelta
from referrals.models import Referral, DoctorCategory
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.http import JsonResponse


User = get_user_model()

@login_required()
#@permission_required('appointments.add_appointment', raise_exception=True)
def CreateAppointment(request, only_ids = False):
    curr_user = request.user
    if curr_user.role != 'DOCTOR':
        return render(request, "appointments/error.html", {'error_message': "Only doctors can create appointments"})

    if request.method == 'GET':
        return render(request, 'appointments/create_appointment.html')
    
    elif request.method == 'POST':
        try:
            datetime_str = request.POST.get('datetime')
            if not datetime_str:
                date = request.POST.get('date')
                time = request.POST.get('time')
                if date and time:
                    datetime_str = date + 'T' + time
                else:
                    raise ValueError("Date and time are required")
                
            duration = int(request.POST.get('duration', 30))
            description = request.POST.get('description', '')
            is_recurring = request.POST.get('is_recurring') == 'on'
            recurring_type = request.POST.get('recurring_type', '')
            recurring_count = int(request.POST.get('recurring_count', 1))
            referal_type = request.POST.get('referal_type')
            referal_type = request.POST.get('referal_type') or None  # Convert empty string to None
            
            
            # Make sure we create a timezone-aware datetime
            appointment_start_datetime = timezone.make_aware(datetime.fromisoformat(datetime_str))
            appointment_end_datetime = appointment_start_datetime + timedelta(minutes=duration)

            current_slot = AppointmentSlot.objects.annotate(
                end_time=ExpressionWrapper(
                    F('date') + Cast(F('duration'), IntegerField()) * timedelta(minutes=1),
                    output_field=DateTimeField()
                )
            ).filter(Q(
                Q(date__gt=appointment_start_datetime) & Q(end_time__lt=appointment_end_datetime))
            | Q(
                Q(date__lt=appointment_start_datetime) & Q(end_time__gt=appointment_start_datetime))
            | Q(
                Q(date__gt=appointment_start_datetime) & Q(end_time__gt=appointment_end_datetime)
            )).first()
            if current_slot:
                raise ValueError("Cannot create an appointment slot. This time is already used in some other timeslot")
            ids = []
            appointment = AppointmentSlot.objects.create(
                doctor=curr_user,
                date=appointment_start_datetime,
                duration=duration,
                description=description,
                status=AppointmentStatus.AVAILABLE,
                location = curr_user.address,
                referal_type=referal_type
            )
            ids.append(appointment.id)
            if is_recurring and recurring_type:
                if recurring_type == 'daily':
                    interval = timedelta(days=1)
                elif recurring_type == 'weekly':
                    interval = timedelta(weeks=1)
                elif recurring_type == 'biweekly':
                    interval = timedelta(weeks=2)
                elif recurring_type == 'monthly':
                    interval = timedelta(months=1)
                
                next_date = appointment_start_datetime
                for _ in range(1, recurring_count):
                    next_date = next_date + interval
                    appointment = AppointmentSlot.objects.create(
                        doctor=curr_user,
                        date=next_date,
                        duration=duration,
                        description=description,
                        status='Available',
                        location = curr_user.address,
                        referal_type = referal_type
                    )
                    ids.append(appointment.id)
            if only_ids:
                return ids
            return render(request, 'create_appointment.html')
            
        except Exception as e:
            print(f"Error creating appointment: {e}")
            if only_ids:
                return -1
            return render(request, 'error.html')
            


def categorize_appointments(appointments, today):
    past = [appointment for appointment in appointments if appointment.date.date() < today]
    today_appointments = [appointment for appointment in appointments if appointment.date.date() == today]
    future = [appointment for appointment in appointments if appointment.date.date() > today]
    
    return {
        'past': past,
        'today': today_appointments,
        'future': future
    }

def group_appointments_by_date(appointments):
    appointments_by_date = defaultdict(list)
    for appointment in appointments.order_by('date'):
        date_key = appointment.date.date()
        appointments_by_date[date_key].append(appointment)
    grouped_appointments = sorted(appointments_by_date.items(), key=lambda x: x[0])
    return grouped_appointments


@login_required()
def GetAppointment(request):
    curr_user = request.user
    
    if curr_user.role == 'DOCTOR':
        appointments = AppointmentSlot.objects.filter(
            doctor=curr_user
        ).filter(
            Q(status="Available") | Q(status="Booked")
        ).order_by('date')
    elif curr_user.role == 'PATIENT':
        filtered_slots = AppointmentSlot.objects.filter(
            Q(status="Available") | Q(status="Booked")
        )
        appointments = Appointment.objects.filter(
            patient=curr_user,
            appointment_slot__in=filtered_slots
        ).select_related('appointment_slot').order_by('appointment_slot__date')
    else:
        appointments = []
    
    appointments_by_date = defaultdict(list)
    for appointment in appointments:
        if curr_user.role == 'DOCTOR':
            date_key = appointment.date.date()
        else:
            date_key = appointment.appointment_slot.date.date()
        appointments_by_date[date_key].append(appointment)
    
    grouped_appointments = sorted(appointments_by_date.items(), key=lambda x: x[0])
    
    page = request.GET.get('page', 1)
    paginator = Paginator(grouped_appointments, 5)
    
    try:
        paginated_dates = paginator.page(page)
    except PageNotAnInteger:
        paginated_dates = paginator.page(1)
    except EmptyPage:
        paginated_dates = paginator.page(paginator.num_pages)
    
    context = {
        'grouped_appointments': paginated_dates,
        'has_appointments': len(grouped_appointments) > 0
    }
    
    return render(request, 'appointments/list.html', context)

@login_required()
#@permission_required('appointments.delete_appointment', raise_exception=True)
def CancelAppointment(request, appointment_id):
    curr_user = request.user
    
    try:
        chosen_appointment_slot = AppointmentSlot.objects.get(id=appointment_id)
        
        if curr_user.role == 'DOCTOR' and chosen_appointment_slot.doctor == curr_user:
            if chosen_appointment_slot.status == 'Booked':
                appointment = Appointment.objects.get(appointment_slot=chosen_appointment_slot)
                if appointment.referral:
                    appointment.referral.is_used = False
                appointment.referral.save()
                Notification.objects.create(receiver=appointment.patient, message="Your appointment has been cancelled by {appointment_slot.doctor}")
        elif curr_user.role == 'PATIENT' and appointment.patient == curr_user:
            if chosen_appointment_slot.status == 'Booked':
                appointment = Appointment.objects.get(appointment_slot=chosen_appointment_slot)
                if appointment.referral:
                    appointment.referral.is_used = False
                appointment.referral.save()
                Notification.objects.create(receiver=chosen_appointment_slot.doctor, message="The appointment has been cancelled by {appointment.patient}")
        else:
            return render(request, 'appointments/error.html', {'error_message': "You don't have right to do this!"})
        chosen_appointment_slot.status = 'Cancelled'
        chosen_appointment_slot.save()
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')

@login_required
#@permission_required('appointments.add_appointment', raise_exception=True)
def BookAppointment(request, appointment_id, user_id_var = None):
    curr_user = request.user

    if curr_user.role != "PATIENT":
        return render(request, 'appointments/error.html', {'error_message': "You can't do this!"})
    user_id = curr_user.id
    if user_id_var:
        user_id = user_id_var
    try:
        appointment_slot = AppointmentSlot.objects.get(id=appointment_id, status='Available')
        if not appointment_slot:
            return render(request, "appointments/error.html", {'error_message': "No slot available"})
        
        if request.method == "GET":
            return render(request, 'appointments/book_appointment.html', {'appointment': appointment_slot})
        
        if request.method == "POST":
            available_referral = None
            if appointment_slot.referal_type:
                # Use timezone.now() instead of datetime.now() for timezone awareness
                available_referral = Referral.objects.filter(Q(patient=curr_user) &
                                                        Q(specialist_type=appointment_slot.referal_type) &
                                                        Q(is_used=False) &
                                                        Q(expiration_date__gte=datetime.now().date())).first()
                if available_referral is None:
                    return render(request, 'appointments/error.html', {'error_message':"You are not alowed to book this as you don't have referral needed"})
                available_referral.is_used=True
                available_referral.save()
            patient = User.objects.filter(id = user_id).first()
            if patient is None:
                return render(request, 'appointments/error.html', {'error_message':"You are not alowed to book this as you don't have referral needed"})
            appointment = Appointment.objects.create(
                patient=patient,
                appointment_slot=appointment_slot,
                referral=available_referral
            )

            appointment_slot.status = "Booked"
            appointment_slot.save()
            

            doctor_notification = Notification.objects.create(
                receiver=appointment_slot.doctor,
                message=f"Your appointment slot on {appointment_slot.date} has been booked by {curr_user.name}."
            )
            
            Notification.objects.create(
                receiver=curr_user,
                message=f"Your appointment with Dr. {appointment_slot.doctor.user.name} on {appointment_slot.date} has been confirmed."
            )
            
            return render(request, 'appointments/booking_success.html', {'appointment': appointment})
            
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')


@login_required
def doctors_list(request):
    from referrals.models import DoctorCategory
    
    # Get all doctors
    doctors = User.objects.filter(role='DOCTOR')

    # Search by name
    search_query = request.GET.get('search', '')
    if search_query:
        doctors = doctors.filter(name__icontains=search_query)

    # Filter by specialization
    specialization = request.GET.get('specialization', '')
    if specialization:
        doctors = doctors.filter(doctor_profile__specialization=specialization)

    # Filter by available date
    available_date = request.GET.get('date', '')
    if available_date:
        try:
            date = datetime.strptime(available_date, '%Y-%m-%d').date()
            doctors = doctors.filter(
                appointments_as_doctor__date__date=date,
                appointments_as_doctor__status='Available'
            ).distinct()
        except ValueError:
            pass

    # Get specialization choices from the model
    specializations = DoctorCategory.choices

    # Order by name
    doctors = doctors.order_by('name')

    # Pagination
    paginator = Paginator(doctors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'specializations': specializations,
        'filters': {
            'search': search_query,
            'specialization': specialization,
            'date': available_date,
        },
        'today': timezone.now().date(),
    }

    return render(request, 'appointments/doctors/doctors_list.html', context)


@login_required
def appointment_list(request):
    if request.user.role == 'DOCTOR':
        appointments = Appointment.objects.filter(appointment_slot__doctor=request.user, appointment_slot__status="Booked")
    else:
        appointments = Appointment.objects.filter(patient=request.user)

    show_upcoming = request.GET.get('upcoming') == 'true'
    show_past = request.GET.get('past') == 'true'
    search_id = request.GET.get('search', '').strip()
    search_name = None

    today = timezone.now().date()
    if show_upcoming and not show_past:
        appointments = appointments.filter(appointment_slot__date__gte=today)
    elif show_past and not show_upcoming:
        appointments = appointments.filter(appointment_slot__date__lt=today)

    if search_id:
        try:
            if request.user.role == 'DOCTOR':
                search_user = User.objects.get(id=search_id, role='PATIENT')
                appointments = appointments.filter(patient=search_user)
                search_name = search_user.name
            else:
                search_user = User.objects.get(id=search_id, role='DOCTOR')
                appointments = appointments.filter(appointment_slot__doctor=search_user)
                search_name = search_user.name
        except User.DoesNotExist:
            pass
    today = timezone.now()
    appointments = appointments.order_by('appointment_slot__date')

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'filters': {
            'upcoming': show_upcoming,
            'past': show_past,
            'search': search_id,
            'search_name': search_name,
        },
        'today': today,
    })

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

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
@user_passes_test(lambda u: u.role == 'PATIENT')
def doctor_available_appointments(request, doctor_id):
    """
    View to list all available appointments for a specific doctor.
    Only accessible by patients.
    """
    try:
        doctor = User.objects.get(id=doctor_id, role='DOCTOR')
    except User.DoesNotExist:
        return render(request, 'appointments/error.html', {'error_message': 'Doctor not found'})

    # Get all available appointment slots for this doctor
    available_slots = AppointmentSlot.objects.filter(
        doctor=doctor,
        status=AppointmentStatus.AVAILABLE,
        date__gte=timezone.now()  # Only show future appointments
    ).order_by('date')

    # Group appointments by date
    appointments_by_date = defaultdict(list)
    for slot in available_slots:
        date_key = slot.date.date()
        appointments_by_date[date_key].append(slot)

    # Sort by date
    grouped_appointments = sorted(appointments_by_date.items(), key=lambda x: x[0])

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(grouped_appointments, 5)  # 5 dates per page

    try:
        paginated_dates = paginator.page(page)
    except PageNotAnInteger:
        paginated_dates = paginator.page(1)
    except EmptyPage:
        paginated_dates = paginator.page(paginator.num_pages)

    context = {
        'doctor': doctor,
        'grouped_appointments': paginated_dates,
        'has_appointments': len(grouped_appointments) > 0
    }

    return render(request, 'appointments/doctor_available_appointments.html', context)


