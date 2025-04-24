from django.urls import path
from . import views

urlpatterns = [
    # User notifications
    path('', views.notification_list, name='notification_list'),
    path('<uuid:notification_id>/', views.notification_detail, name='notification_detail'),
    path('<uuid:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_notifications_read'),
    path('unread-count/', views.get_unread_count, name='notification_unread_count'),
    
    # Admin notifications
    path('admin/send/', views.admin_send_notification, name='admin_send_notification'),
]