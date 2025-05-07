from django.urls import path, include
from .views import *
from .api import router

app_name = 'referrals'

urlpatterns = [
    path('api/', include(router.urls)),
    path('create/', create_referral, name='create_referral'),
    path('list/', referral_list, name='referral_list'),
    path('detail/<uuid:pk>/', referral_detail, name='referral_detail'),
    path('delete/<uuid:pk>/', delete_referral, name='delete_referral'),
    path('search/patients/', search_patients, name='search_patients'),
    path('search/referrals/', search_referrals, name='search_referrals'),
    path('search/users/', search_users, name='search_users'),
]