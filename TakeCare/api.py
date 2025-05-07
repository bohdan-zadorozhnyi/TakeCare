from accounts.urls import urlpatterns
from django.urls import path
from django.urls.conf import include

urlpatterns = [
    path('appointments/', include('appointments.api')),
    path('accounts/', include('accounts.api')),
    path('articles/', include('articles.api')),
    path('issues/', include('issues.api')),
    path('medical/', include('medical.api')),
    path('notifications/', include('notifications.api')),
    path('prescriptions/', include('prescriptions.api')),
    path('referrals/', include('referrals.api'))
]