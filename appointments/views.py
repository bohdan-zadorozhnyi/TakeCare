from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import AppointmentSlot, Appointment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict
from notifications.models import Notification
from accounts.models import PatientProfile, DoctorProfile, AdminProfile
from django.contrib.auth.decorators import permission_required, login_required
from django.db.models import IntegerField, DateTimeField, Q, ExpressionWrapper, F
from django.db.models.functions import Cast
from datetime import datetime, timedelta
from referrals.models import Referral


User = get_user_model()

@login_required()
@permission_required('appointments.add_appointment', raise_exception=True)
def CreateAppointment(request):
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
            
            
            appointment_start_datetime = datetime.fromisoformat(datetime_str)
            appointment_end_datetime = appointment_start_datetime + timedelta(minutes=duration)

            current_slot = AppointmentSlot.objects.annotate(
                                                            end_time=ExpressionWrapper(F('date') + Cast(F('duration'), IntegerField())  * timedelta(minutes=1)),
                                                            output_field=DateTimeField()
                                                            ).filter(Q(
                                                                        Q(date_gt=appointment_start_datetime) & Q(end_time_lt=appointment_end_datetime))
                                                                    | Q(
                                                                        Q(date_lt=appointment_start_datetime) & Q(end_time_gt=appointment_start_datetime))
                                                                    | Q(
                                                                        Q(date_gt=appointment_start_datetime) & Q(end_time_gt=appointment_end_datetime)
                                                                        )
                                                                    ).first()
            if current_slot is not None:
                raise ValueError("Cannot create an appointment slot. This time is already used in some other timeslot")
            
            appointment = AppointmentSlot.objects.create(
                doctor=curr_user,
                date=appointment_start_datetime,
                duration=duration,
                description=description,
                status='Available',
                location = curr_user.address
            )
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
                    AppointmentSlot.objects.create(
                        doctor=curr_user,
                        date=next_date,
                        duration=duration,
                        description=description,
                        status='Available',
                        location = curr_user.address,
                        referal_type = referal_type
                    )
            
            return render(request, 'appointments/success.html')
            
        except Exception as e:
            print(f"Error creating appointment: {e}")
            return render(request, 'appointments/error.html', {'error_message': str(e)})
            


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
@permission_required('appointments.view_appointment', raise_exception=True)
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
@permission_required('appointments.delete_appointment', raise_exception=True)
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
        return render(request, 'appointments/cancel_success.html')
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')

@login_required
@permission_required('appointments.add_appointment', raise_exception=True)
def BookAppointment(request, appointment_id):
    curr_user = request.user

    if curr_user.role != "PATIENT":
        return render(request, 'appointments/error.html', {'error_message': "You can't do this!"})

    try:
        appointment_slot = AppointmentSlot.objects.get(id=appointment_id, status='Available')
        if not appointment_slot:
            return render(request, "appointments/error.html", {'error_message': "No slot available"})
        
        if request.method == "GET":
            return render(request, 'appointments/book_appointment.html', {'appointment': appointment_slot})
        
        if request.method == "POST":
            available_referral = None
            if appointment_slot.referal_type:
                available_referral = Referral.objects.filter(Q(patient=curr_user) &
                                                        Q(specialist_type=appointment_slot.referal_type) &
                                                        Q(is_used=False) &
                                                        Q(expiration_date_gte=datetime.now().date())).first()
                if available_referral is None:
                    return render(request, 'appointments/error.html', {'error_message':"You are not alowed to book this as you don't have referral needed"})
                available_referral.is_used=True
                available_referral.save()
            appointment = Appointment.objects.create(
                patient=curr_user,
                appointment_slot=appointment_slot,
                referral=available_referral
            )

            appointment_slot.status = "Booked"
            appointment_slot.save()
            

            doctor_notification = Notification.objects.create(
                receiver=appointment_slot.doctor,
                message=f"Your appointment slot on {appointment_slot.date} has been booked by {curr_user.first_name} {curr_user.last_name}."
            )
            
            Notification.objects.create(
                receiver=curr_user,
                message=f"Your appointment with Dr. {appointment_slot.doctor.user.first_name} {appointment_slot.doctor.user.last_name} on {appointment_slot.date} has been confirmed."
            )
            
            return render(request, 'appointments/booking_success.html', {'appointment': appointment})
            
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')


@login_required
def doctors_list(request):
    doctors = User.objects.filter(role='DOCTOR').order_by('name')

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'appointments/doctors/doctors_list.html', {
        'page_obj': page_obj
    })