from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('create/', views.create_prescription, name='create_prescription'),
    path('list/', views.prescription_list, name='prescription_list'),
    path('<uuid:pk>/', views.prescription_detail, name='prescription_detail'),
    path('<uuid:pk>/delete/', views.delete_prescription, name='delete_prescription'),
    path('search/prescriptions/', views.search_prescriptions, name='search_prescriptions'),
    path('search-patients/', views.search_patients, name='search_patients'),
    path('search-users/', views.search_users, name='search_users'),
]