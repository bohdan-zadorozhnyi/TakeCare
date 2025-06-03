import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.views import View
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.forms import modelformset_factory
from appointments.models import Appointment
from referrals.models import DoctorCategory
from .models import Payment, SpecializationPrice
from .forms import SpecializationPriceFormSet

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_success(request):
    return render(request, 'payments/payment_success.html')

def payment_canceled(request):
    return render(request, 'payments/payment_canceled.html')

def create_checkout_session(request):
    YOUR_DOMAIN = "http://localhost:8000"
    if request.method == 'POST':
        appointment_id = request.GET.get("appointment_id")
        appointment = get_object_or_404(Appointment, id=appointment_id)

        try:
            payment = appointment.payment
            amount_cents = payment.price
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found for this appointment'}, status=404)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'pln',
                            'unit_amount': amount_cents,
                            'product_data': {
                                'name': f'Appointment with {appointment.appointment_slot.doctor}',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=YOUR_DOMAIN + '/payments/success/',
                cancel_url=YOUR_DOMAIN + '/payments/cancel/',
                metadata={'payment_id': str(payment.id)}
            )

            payment.stripe_payment_session_id = checkout_session.id
            payment.save()

            return HttpResponseRedirect(checkout_session.url)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=400)

endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

@csrf_exempt
def webhook_view(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

        # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        try:
            payment = Payment.objects.get(stripe_payment_session_id=session['id'])
        except Payment.DoesNotExist:
            return HttpResponse(status=404)

        if payment.status != 'succeeded':
            if session.get('payment_status') == 'paid':
                payment.status = 'succeeded'
                payment.save()

                appointment = payment.appointment
                appointment.status = 'confirmed'
                appointment.save()

    return HttpResponse(status=200)


def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@login_required
@user_passes_test(is_admin)
def view_prices(request):
    prices = SpecializationPrice.objects.all()
    return render(request, 'payments/view_prices.html', {'prices': prices})

@login_required
@user_passes_test(is_admin)
def edit_prices(request):
    if request.method == 'POST':
        formset = SpecializationPriceFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('payments:prices')
        else:
            print(formset.errors)
    else:
        formset = SpecializationPriceFormSet()

    return render(request, 'payments/edit_prices.html', {'formset': formset})