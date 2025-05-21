from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import NotificationViewSet
from .views import notification_status, notification_test, notification_list

app_name = 'notifications'

router = DefaultRouter()
router.register('', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', notification_list, name='notification_list'),
    path('status/', notification_status, name='notification_status'),
    path('test/', notification_test, name='notification_test'),
    path('api/', include(router.urls)),
]