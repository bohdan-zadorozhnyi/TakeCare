from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'appointments'

urlpatterns = [
    path('appointment/', views.GetAppointment, name='appointment'),
    path('appointment/list/', views.appointment_list, name='appointment_list'),
    path('appointment/create/', views.CreateAppointment, name='create_appointment'),
    path('appointment/cancel/<uuid:appointment_id>/', views.CancelAppointment, name='cancel_appointment'),
    path('appointment/book/<uuid:appointment_id>/', views.BookAppointment, name='book_appointment'),
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('doctors/appointment/list/<uuid:doctor_id>', views.doctor_available_appointments, name='doctors_available_appointments'),
    path('search-patients/', views.search_patients, name='search_patients'),
    path('search-users/', views.search_users, name='search_users'),
]