from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import login_view, register_view



urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
]