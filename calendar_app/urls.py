from django.urls import path
from . import views


urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('api/appointments/', views.get_appointments_json, name='get_appointments_json'),
    path('appointment/<uuid:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<uuid:appointment_id>/add-note/', views.add_appointment_note, name='add_appointment_note'),
    path('appointment/<uuid:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('slot/<uuid:slot_id>/', views.appointment_slot_detail, name='appointment_slot_detail'),
    path('slot/add/', views.add_calendar_slot, name='add_calendar_slot'),
    path('settings/update/', views.update_calendar_settings, name='update_calendar_settings'),
]