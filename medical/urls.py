from django.urls import path
from . import views

app_name = 'medical'

urlpatterns = [
    path('create/', views.create_medical_record, name='create_medical_record'),
    path('list/', views.medical_record_list, name='medical_record_list'),
    path('<uuid:pk>/', views.medical_record_detail, name='medical_record_detail'),
    path('<uuid:pk>/delete/', views.delete_medical_record, name='delete_medical_record'),
    path('search/medical/', views.search_medical_record, name='search_medical_record'),
    path('search-patients/', views.search_patients, name='search_patients'),
    path('<uuid:pk>/edit/', views.edit_medical_record, name='edit_medical_record'),
    #path('search-users/', views.search_users, name='search_users'),
]