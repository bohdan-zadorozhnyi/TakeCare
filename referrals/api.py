from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ReferralViewSet

router = DefaultRouter()
router.register('', ReferralViewSet)

urlpatterns = router.urls