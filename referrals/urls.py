from django.urls import path
from . import views

urlpatterns = [
    path('', views.referral_list, name='referral_list'),
    path('create/', views.create_referral, name='create_referral'),
    path('<uuid:referral_id>/', views.referral_detail, name='referral_detail'),
    path('search/patients/', views.search_patients, name='referral_search_patients'),
]