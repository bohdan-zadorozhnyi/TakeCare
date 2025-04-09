from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    path('appointment/', views.GetAppointment, name='appointment'),
    path('appointment/create/', views.CreateAppointment, name='create_appointment'),
    path('appointment/cancel/<int:appointment_id>/', views.CancelAppointment, name='cancel_appointment'),
]