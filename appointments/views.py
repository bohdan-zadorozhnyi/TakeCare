from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import Appointment
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import TruncDate
from django.db.models import Count
from collections import defaultdict

def CreateAppointment(request):
    curr_user = request.user
    if curr_user.role != 'Doctor':
        return HttpResponseForbidden("Only doctors can create appointments")
    
    if request.method == 'GET':
        # Return the appointment creation form
        return render(request, 'appointments/create_appointment.html')
    
    elif request.method == 'POST':
        # Process the form data and create a new appointment
        # TODO: Add form processing logic here
        # For now, just return a success message
        return render(request, 'appointments/success.html')

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
    if curr_user.role == 'Doctor':
        appointments = Appointment.objects.filter(doctor=curr_user)
        grouped_appointments = group_appointments_by_date(appointments)
    elif curr_user.role == 'Patient':
        appointments = Appointment.objects.filter(patient=curr_user)
        grouped_appointments = group_appointments_by_date(appointments)
    else:
        grouped_appointments = []
    
    # Pagination
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

def CancelAppointment(request, appointment_id):
    curr_user = request.user
    if not curr_user.is_authenticated:
        return render(request, 'shared/unauthenticated.html')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Check if the user has permission to cancel this appointment
        if curr_user.role == 'Doctor' and appointment.doctor == curr_user:
            # Doctor can cancel their own appointments
            appointment.status = 'Cancelled'
            appointment.save()
            return render(request, 'appointments/cancel_success.html')
        elif curr_user.role == 'Patient' and appointment.patient == curr_user:
            # Patient can cancel their own appointments
            appointment.status = 'Cancelled'
            appointment.save()
            return render(request, 'appointments/cancel_success.html')
        else:
            # User doesn't have permission to cancel this appointment
            return HttpResponseForbidden("You don't have permission to cancel this appointment")
    except Appointment.DoesNotExist:
        # Appointment not found
        return render(request, 'appointments/not_found.html')
    