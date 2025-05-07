from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ReferralViewSet, ReferralDetailsViewSet

router = DefaultRouter()
router.register('referrals', ReferralViewSet, basename='referral')
router.register('details', ReferralDetailsViewSet, basename='referral-details')

urlpatterns = router.urls