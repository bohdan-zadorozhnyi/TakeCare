from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import ArticleViewSet

router = DefaultRouter()
router.register('', ArticleViewSet)

urlpatterns = router.urls