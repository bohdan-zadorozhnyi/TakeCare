from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta

from appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from accounts.models import User
from .models import AppointmentNote, AppointmentReminder, CalendarSettings

@login_required
def calendar_view(request):
    """Main calendar view that shows the user's appointments in a calendar format"""
    # Get or create user calendar settings
    settings, created = CalendarSettings.objects.get_or_create(
        user=request.user,
        defaults={
            'default_view': 'month',
            'reminder_before': 24,
            'show_past_appointments': True
        }
    )
    
    context = {
        'default_view': settings.default_view,
        'user_role': request.user.role,
    }
    
    # If the user is a doctor, provide locations and patients for the add slot form
    if request.user.role == 'DOCTOR':
        # Get unique locations from doctor's existing appointment slots
        doctor_locations = AppointmentSlot.objects.filter(
            doctor=request.user
        ).values_list('location', flat=True).distinct()
        
        # Get all patients (users with PATIENT role)
        patients = User.objects.filter(role='PATIENT')
        
        context.update({
            'doctor_locations': doctor_locations,
            'patients': patients
        })
    
    return render(request, 'calendar_app/calendar.html', context)

@login_required
def get_appointments_json(request):
    """API endpoint to get appointments in JSON format for the calendar widget"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if not (start_date and end_date):
        return HttpResponseBadRequest("Missing start or end date parameters")
    
    user = request.user
    appointments_data = []
    
    # Patient sees their booked appointments
    if user.role == 'PATIENT':
        appointments = Appointment.objects.filter(
            patient=user,
            appointment_slot__date__range=[start_date, end_date]
        ).select_related('appointment_slot', 'appointment_slot__doctor')
        
        for appointment in appointments:
            slot = appointment.appointment_slot
            appointments_data.append({
                'id': str(appointment.id),
                'title': f"Appointment with Dr. {slot.doctor.name}",
                'start': slot.date.isoformat(),
                'end': (slot.date + timezone.timedelta(minutes=slot.duration)).isoformat(),
                'location': slot.location,
                'description': slot.description,
                'status': slot.status,
                'url': reverse('appointment_detail', args=[appointment.id]),
                'backgroundColor': '#4285F4' if slot.status == 'Booked' else '#F4B400',
                'borderColor': '#3367D6' if slot.status == 'Booked' else '#E09C00',
            })
            
    # Doctor sees their appointment slots and booked appointments
    elif user.role == 'DOCTOR':
        # Get all appointment slots for this doctor
        slots = AppointmentSlot.objects.filter(
            doctor=user,
            date__range=[start_date, end_date]
        )
        
        for slot in slots:
            # Try to get the related appointment if it exists
            try:
                appointment = Appointment.objects.filter(appointment_slot=slot).first()
                if appointment:
                    # This is a booked appointment
                    appointments_data.append({
                        'id': str(appointment.id),
                        'title': f"Appointment with {appointment.patient.name}",
                        'start': slot.date.isoformat(),
                        'end': (slot.date + timezone.timedelta(minutes=slot.duration)).isoformat(),
                        'location': slot.location,
                        'description': slot.description,
                        'status': slot.status,
                        'patient': appointment.patient.name,
                        'url': reverse('appointment_detail', args=[appointment.id]),
                        'backgroundColor': '#4285F4',
                        'borderColor': '#3367D6',
                    })
                else:
                    # This is an available slot
                    appointments_data.append({
                        'id': str(slot.id),
                        'title': "Available Slot",
                        'start': slot.date.isoformat(),
                        'end': (slot.date + timezone.timedelta(minutes=slot.duration)).isoformat(),
                        'location': slot.location,
                        'description': slot.description,
                        'status': slot.status,
                        'url': reverse('appointment_slot_detail', args=[slot.id]),
                        'backgroundColor': '#34A853',
                        'borderColor': '#2E7D32',
                    })
            except Exception as e:
                continue
                
    # Admin sees all appointments
    elif user.role == 'ADMIN':
        appointments = Appointment.objects.filter(
            appointment_slot__date__range=[start_date, end_date]
        ).select_related('appointment_slot', 'appointment_slot__doctor', 'patient')
        
        for appointment in appointments:
            slot = appointment.appointment_slot
            appointments_data.append({
                'id': str(appointment.id),
                'title': f"{appointment.patient.name} with Dr. {slot.doctor.name}",
                'start': slot.date.isoformat(),
                'end': (slot.date + timezone.timedelta(minutes=slot.duration)).isoformat(),
                'location': slot.location,
                'description': slot.description,
                'status': slot.status,
                'url': reverse('appointment_detail', args=[appointment.id]),
                'backgroundColor': '#4285F4',
                'borderColor': '#3367D6',
            })
    
    return JsonResponse(appointments_data, safe=False)

@login_required
def appointment_detail(request, appointment_id):
    """View for appointment details when a user clicks on an appointment in the calendar"""
    appointment = get_object_or_404(
        Appointment.objects.select_related('appointment_slot', 'appointment_slot__doctor', 'patient'),
        id=appointment_id
    )
    
    # Check if user has permission to view this appointment
    user = request.user
    if user.role == 'PATIENT' and appointment.patient != user:
        return HttpResponseBadRequest("You do not have permission to view this appointment")
    if user.role == 'DOCTOR' and appointment.appointment_slot.doctor != user:
        return HttpResponseBadRequest("You do not have permission to view this appointment")
        
    # Get appointment notes
    notes = AppointmentNote.objects.filter(appointment=appointment).order_by('-created_at')
    
    # Check if there's a chat for this appointment
    from chat.models import ChatRoom
    chat_room = None
    try:
        # Look for a chat room between doctor and patient
        chat_room = ChatRoom.objects.filter(
            participants=appointment.patient
        ).filter(
            participants=appointment.appointment_slot.doctor
        ).first()
    except:
        pass

    context = {
        'appointment': appointment,
        'notes': notes,
        'chat_room': chat_room,
        'can_cancel': appointment.appointment_slot.status == 'Booked' and 
                    appointment.appointment_slot.date > timezone.now(),
        'can_reschedule': appointment.appointment_slot.status == 'Booked' and 
                        appointment.appointment_slot.date > timezone.now(),
    }
    
    return render(request, 'calendar_app/appointment_detail.html', context)

@login_required
def add_appointment_note(request, appointment_id):
    """Add a note to an appointment"""
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check if user has permission to add notes
        user = request.user
        if user.role == 'PATIENT' and appointment.patient != user:
            return HttpResponseBadRequest("You do not have permission to add notes to this appointment")
        if user.role == 'DOCTOR' and appointment.appointment_slot.doctor != user:
            return HttpResponseBadRequest("You do not have permission to add notes to this appointment")
            
        content = request.POST.get('content', '').strip()
        if content:
            note = AppointmentNote.objects.create(
                appointment=appointment,
                created_by=user,
                content=content
            )
            
        return redirect('appointment_detail', appointment_id=appointment_id)
    
    return HttpResponseBadRequest("Invalid request method")

@login_required
def appointment_slot_detail(request, slot_id):
    """View for appointment slot details for doctors"""
    slot = get_object_or_404(
        AppointmentSlot,
        id=slot_id
    )
    
    # Check if user has permission to view this slot
    user = request.user
    if user.role == 'DOCTOR' and slot.doctor != user:
        return HttpResponseBadRequest("You do not have permission to view this slot")
        
    context = {
        'slot': slot,
        'can_edit': slot.status == 'Available' or 
                  (slot.status == 'Booked' and slot.date > timezone.now())
    }
    
    return render(request, 'calendar_app/appointment_slot_detail.html', context)

@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
        
    appointment = get_object_or_404(
        Appointment.objects.select_related('appointment_slot'),
        id=appointment_id
    )
    
    # Check if user has permission to cancel this appointment
    user = request.user
    if user.role == 'PATIENT' and appointment.patient != user:
        return HttpResponseBadRequest("You do not have permission to cancel this appointment")
    if user.role == 'DOCTOR' and appointment.appointment_slot.doctor != user:
        return HttpResponseBadRequest("You do not have permission to cancel this appointment")
        
    # Check if appointment can be cancelled
    if appointment.appointment_slot.date <= timezone.now():
        return HttpResponseBadRequest("Cannot cancel past appointments")
        
    # Update appointment slot status
    slot = appointment.appointment_slot
    slot.status = 'Available'
    slot.save()
    
    # Delete the appointment
    appointment.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('calendar_view')

@login_required
def update_calendar_settings(request):
    """Update user calendar settings"""
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
        
    user = request.user
    settings, created = CalendarSettings.objects.get_or_create(user=user)
    
    # Update settings based on form data
    settings.default_view = request.POST.get('default_view', settings.default_view)
    settings.reminder_before = int(request.POST.get('reminder_before', settings.reminder_before))
    settings.show_past_appointments = request.POST.get('show_past_appointments', '') == 'on'
    settings.save()
    
    return redirect('calendar_view')

@login_required
@require_POST
def add_calendar_slot(request):
    """Add a new appointment slot to the calendar"""
    # Only doctors can create slots
    if request.user.role != 'DOCTOR':
        return JsonResponse({
            'status': 'error',
            'message': 'Only doctors can create appointment slots'
        }, status=403)
    
    try:
        # Get form data
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        duration = int(request.POST.get('duration', 30))
        description = request.POST.get('description', '')
        referal_type = request.POST.get('referal_type') or None  # Convert empty string to None
        location = request.POST.get('location', "Main Clinic")
        patient_id = request.POST.get('patient')
        
        # Create datetime object
        start_datetime = timezone.make_aware(
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        )
        
        # Check if the datetime is in the future
        if start_datetime <= timezone.now():
            return JsonResponse({
                'status': 'error',
                'message': 'Appointment slots must be in the future'
            }, status=400)
        
        # Create initial slot
        new_slot = AppointmentSlot(
            doctor=request.user,
            location=location,
            description=description,
            date=start_datetime,
            duration=duration,
            status=AppointmentStatus.AVAILABLE,
            referal_type=referal_type
        )
        new_slot.save()
        
        created_slots = [new_slot]
        
        # If a patient is selected, create an appointment for this slot
        if patient_id:
            try:
                patient = User.objects.get(id=patient_id, role='PATIENT')
                # Create appointment
                appointment = Appointment.objects.create(
                    patient=patient,
                    appointment_slot=new_slot
                )
                # Update slot status to booked
                new_slot.status = AppointmentStatus.BOOKED
                new_slot.save()
            except User.DoesNotExist:
                pass  # Continue without creating an appointment if patient doesn't exist
        
        # Handle recurring appointments if checked
        is_recurring = request.POST.get('is_recurring') == 'on'
        if is_recurring:
            recurring_type = request.POST.get('recurring_type', 'weekly')
            recurring_count = int(request.POST.get('recurring_count', 4))
            
            # Calculate recurring dates and create slots
            for i in range(1, recurring_count):
                if recurring_type == 'daily':
                    next_date = start_datetime + timedelta(days=i)
                elif recurring_type == 'weekly':
                    next_date = start_datetime + timedelta(weeks=i)
                elif recurring_type == 'biweekly':
                    next_date = start_datetime + timedelta(weeks=2*i)
                elif recurring_type == 'monthly':
                    # This is a simplified approach for monthly recurrence
                    # For a more accurate approach you might need a more complex calculation
                    next_month = start_datetime.month + i
                    next_year = start_datetime.year
                    while next_month > 12:
                        next_month -= 12
                        next_year += 1
                    next_date = start_datetime.replace(year=next_year, month=next_month)
                else:
                    continue
                
                # Create the recurring slot
                recurring_slot = AppointmentSlot(
                    doctor=request.user,
                    location=location,
                    description=description,
                    date=next_date,
                    duration=duration,
                    status=AppointmentStatus.AVAILABLE,
                    referal_type=referal_type
                )
                recurring_slot.save()
                created_slots.append(recurring_slot)
                
                # If a patient is selected, create appointments for all recurring slots too
                if patient_id:
                    try:
                        # Create appointment for this recurring slot
                        appointment = Appointment.objects.create(
                            patient=patient,
                            appointment_slot=recurring_slot
                        )
                        # Update slot status to booked
                        recurring_slot.status = AppointmentStatus.BOOKED
                        recurring_slot.save()
                    except:
                        pass  # Continue if there's an error with one slot
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully created {len(created_slots)} appointment slot(s)',
            'slots': [str(slot.id) for slot in created_slots]
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating appointment slot: {str(e)}'
        }, status=400)
