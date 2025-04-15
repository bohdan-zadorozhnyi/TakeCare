from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import AppointmentSlot, Appointment
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import TruncDate
from django.db.models import Count
from collections import defaultdict
from notifications.models import Notification
from django.db.models import Q

def CreateAppointment(request):
    curr_user = request.user
    if curr_user.role != 'DOCTOR':
        return HttpResponseForbidden("Only doctors can create appointments")
    
    if request.method == 'GET':
        return render(request, 'appointments/create_appointment.html')
    
    elif request.method == 'POST':
        # Process the form data and create a new appointment
        try:
            # Get form data
            datetime_str = request.POST.get('datetime')
            if not datetime_str:
                # If datetime is not provided, try to combine date and time
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
            
            from datetime import datetime
            appointment_datetime = datetime.fromisoformat(datetime_str)

            current_slot = AppointmentSlot.objects.filter(date=appointment_datetime).first()
            if current_slot is not None:
                raise ValueError("Cannot create an appointment slot. This time is already used in some other timeslot")
            
            # Create the initial appointment
            appointment = AppointmentSlot.objects.create(
                doctor=curr_user,
                date=appointment_datetime,
                duration=duration,
                description=description,
                status='Available',
                location = curr_user.address
            )
            print(recurring_type)
            # Handle recurring appointments
            if is_recurring and recurring_type:
                from datetime import timedelta
                
                # Calculate the interval based on recurring type
                if recurring_type == 'daily':
                    interval = timedelta(days=1)
                elif recurring_type == 'weekly':
                    interval = timedelta(weeks=1)
                elif recurring_type == 'biweekly':
                    interval = timedelta(weeks=2)
                elif recurring_type == 'monthly':
                    # For monthly, we need to handle month boundaries
                    from dateutil.relativedelta import relativedelta
                    next_date = appointment_datetime
                    
                    for i in range(1, recurring_count):
                        next_date = next_date + relativedelta(months=1)
                        AppointmentSlot.objects.create(
                            doctor=curr_user,
                            date=next_date,
                            duration=duration,
                            description=description,
                            status='Available',
                            location = curr_user.address
                        )
                    
                    return render(request, 'appointments/success.html')
                
                next_date = appointment_datetime
                for i in range(1, recurring_count):
                    next_date = next_date + interval
                    AppointmentSlot.objects.create(
                        doctor=curr_user,
                        date=next_date,
                        duration=duration,
                        description=description,
                        status='Available',
                        location = curr_user.address
                    )
            
            return render(request, 'appointments/success.html')
            
        except Exception as e:
            # Log the error and return an error page
            print(f"Error creating appointment: {e}")
            return render(request, 'appointments/error.html', {'error_message': str(e)})
            


def categorize_appointments(appointments, today):
    past = []
    today_appointments = []
    future = []
    
    for appointment in appointments:
        if appointment.date.date() < today:
            past.append(appointment)
        elif appointment.date.date() == today:
            today_appointments.append(appointment)
        else:
            future.append(appointment)
    
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

def GetAppointment(request):
    curr_user = request.user
    if not curr_user.is_authenticated:
        return render(request, 'shared/unauthenticated.html')
    
    # Get appointments based on user role
    if curr_user.role == 'DOCTOR':
        appointments = AppointmentSlot.objects.filter(
            doctor=curr_user
        ).filter(
            Q(status="Available") | Q(status="Booked")
        ).order_by('date')
    elif curr_user.role == 'PATIENT':
        # First get the filtered appointment slots
        filtered_slots = AppointmentSlot.objects.filter(
            Q(status="Available") | Q(status="Booked")
        )
        # Then get appointments that reference these slots
        appointments = Appointment.objects.filter(
            patient=curr_user,
            appointment_slot__in=filtered_slots
        ).select_related('appointment_slot').order_by('appointment_slot__date')
    else:
        appointments = []
    
    # Group appointments by date
    appointments_by_date = defaultdict(list)
    for appointment in appointments:
        if curr_user.role == 'DOCTOR':
            date_key = appointment.date.date()
        else:  # PATIENT
            date_key = appointment.appointment_slot.date.date()
        appointments_by_date[date_key].append(appointment)
    
    # Convert to list of tuples (date, appointments) and sort by date
    grouped_appointments = sorted(appointments_by_date.items(), key=lambda x: x[0])
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(grouped_appointments, 5)  # Show 5 dates per page
    
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

def CancelAppointment(request, appointment_id):
    curr_user = request.user
    if not curr_user.is_authenticated:
        return render(request, 'shared/unauthenticated.html')
    
    try:
        appointment_slot = AppointmentSlot.objects.get(id=appointment_id)
        if appointment_slot.status == 'Booked':
            appointment = Appointment.objects.filter(appointment_slot = appointment_slot).first()
        if curr_user.role == 'DOCTOR' and appointment_slot.doctor == curr_user:
            if appointment_slot.status == 'Booked':
                Notification.objects.create(receiver=appointment.patient, message="Your appointment has been cancelled by {appointment_slot.doctor}")
            appointment_slot.status = 'Cancelled'
            appointment_slot.save()
            return render(request, 'appointments/cancel_success.html')
        elif curr_user.role == 'PATIENT' and appointment_slot.patient == curr_user:
            if appointment_slot.status == 'Booked':
                Notification.objects.create(receiver=appointment_slot.doctor, message="The appointment has been cancelled by {appointment.patient}")
            appointment_slot.status = 'Cancelled'
            appointment_slot.save()
            return render(request, 'appointments/cancel_success.html')
        else:
            return HttpResponseForbidden("You don't have permission to cancel this appointment")
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')


def BookAppointment(request, appointment_id):
    curr_user = request.user
    if not curr_user.is_authenticated:
        return HttpUnauthorized()
    
    if curr_user.role != "PATIENT":
        return HttpResponseForbidden("Only patients can book appointments")

    try:
        appointment_slot = AppointmentSlot.objects.get(id=appointment_id, status='Available')
        
        if request.method == "GET":
            return render(request, 'appointments/book_appointment.html', {'appointment': appointment_slot})
        
        if request.method == "POST":
            # Check if patient already has an appointment on the same day
            appointment_date = appointment_slot.date.date()
            existing_appointments = Appointment.objects.filter(
                patient=curr_user,
                appointment_slot__date__date=appointment_date
            )
            
            if existing_appointments.exists():
                # Patient already has an appointment on this day
                return render(request, 'appointments/error.html', {
                    'error_message': f"You already have an appointment scheduled for {appointment_date}. You cannot book multiple appointments on the same day."
                })
            
            # Create the appointment
            appointment = Appointment.objects.create(
                patient=curr_user,
                appointment_slot=appointment_slot
            )
            
            # Update the appointment slot status
            appointment_slot.status = "Booked"
            appointment_slot.save()
            
            # Send notifications to both doctor and patient
            doctor_notification = Notification.objects.create(
                receiver=appointment_slot.doctor,
                message=f"Your appointment slot on {appointment_slot.date} has been booked by {curr_user.first_name} {curr_user.last_name}."
            )
            
            patient_notification = Notification.objects.create(
                receiver=curr_user,
                message=f"Your appointment with Dr. {appointment_slot.doctor.first_name} {appointment_slot.doctor.last_name} on {appointment_slot.date} has been confirmed."
            )
            
            return render(request, 'appointments/booking_success.html', {'appointment': appointment})
            
    except AppointmentSlot.DoesNotExist:
        return render(request, 'appointments/not_found.html')
            