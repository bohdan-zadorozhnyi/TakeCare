from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatroom_list, name='chatroom_list'),
    path('<int:room_id>/', views.chatroom_detail, name='chatroom_detail'),
    path('<int:room_id>/send/', views.send_message, name='send_message'),
]