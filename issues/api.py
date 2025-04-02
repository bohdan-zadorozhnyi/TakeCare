from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import IssueViewSet

router = DefaultRouter()
router.register('', IssueViewSet)

urlpatterns = router.urls