from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import PrescriptionViewSet

router = DefaultRouter()
router.register('', PrescriptionViewSet)

urlpatterns = router.urls