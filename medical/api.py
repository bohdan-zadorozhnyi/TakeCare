from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import MedicalRecordViewSet

router = DefaultRouter()
router.register('', MedicalRecordViewSet)

urlpatterns = router.urls