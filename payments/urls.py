from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('webhook/', views.webhook_view, name='stripe_webhook'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_canceled, name='payment_canceled'),
]