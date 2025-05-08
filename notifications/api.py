from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    NotificationViewSet, AdminNotificationViewSet, TechnicalIssueViewSet
)

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notification')
router.register('admin-notifications', AdminNotificationViewSet, basename='admin-notification')
router.register('technical-issues', TechnicalIssueViewSet, basename='technical-issue')

urlpatterns = router.urls