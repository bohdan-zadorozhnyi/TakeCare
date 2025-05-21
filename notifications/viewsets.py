from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Notification, NotificationStatus
from .serializers import NotificationSerializer
from .services import NotificationService

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get notifications only for the current user
        """
        user = self.request.user
        return Notification.objects.filter(receiver=user).exclude(
            status=NotificationStatus.DELETED
        ).order_by('-date')
    
    def list(self, request, *args, **kwargs):
        """
        Get user's notifications with optional filtering
        """
        queryset = self.get_queryset()
        
        # Filter by status if specified
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by type if specified
        type_filter = request.query_params.get('type', None)
        if type_filter:
            queryset = queryset.filter(type=type_filter)
            
        # Get only unread notifications
        unread = request.query_params.get('unread', None)
        if unread and unread.lower() == 'true':
            queryset = queryset.filter(status=NotificationStatus.UNREAD)
            
        # Limit the number of notifications if specified
        limit = request.query_params.get('limit', None)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read
        """
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'notification marked as read'})
        
    @action(detail=True, methods=['post'], url_path='mark-deleted')
    def mark_deleted(self, request, pk=None):
        """
        Mark a notification as deleted
        """
        notification = self.get_object()
        notification.mark_as_deleted()
        return Response({'status': 'notification marked as deleted'})
        
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user
        """
        user = request.user
        Notification.objects.filter(
            receiver=user,
            status=NotificationStatus.UNREAD
        ).update(status=NotificationStatus.READ)
        return Response({'status': 'all notifications marked as read'})
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get the count of unread notifications for the current user
        """
        user = request.user
        count = Notification.objects.filter(
            receiver=user,
            status=NotificationStatus.UNREAD
        ).count()
        return Response({'unread_count': count})
        
    def create(self, request, *args, **kwargs):
        """
        Only allow staff users to create notifications directly via API
        """
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to create notifications directly."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)