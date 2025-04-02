from rest_framework.routers import DefaultRouter
from .viewsets import AppointmentViewSet


router = DefaultRouter()
router.register('', AppointmentViewSet)

urlpatterns = router.urls