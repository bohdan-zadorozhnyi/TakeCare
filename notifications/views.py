from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import uuid
from .models import Notification, NotificationType
from .services import NotificationService

@require_GET
def notification_status(request):
    """
    Check if the notification system is working
    """
    channel_layer = get_channel_layer()
    websocket_available = channel_layer is not None
    
    return JsonResponse({
        'status': 'online',
        'websocket_available': websocket_available,
        'message': 'Notification system is running'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_test(request):
    """
    Send a test notification to the current user
    """
    user = request.user
    message = request.data.get('message', 'This is a test notification')
    notification_type = request.data.get('notification_type', NotificationType.SYSTEM)
    
    # Validate notification type
    valid_types = [choice[0] for choice in NotificationType.choices]
    if notification_type not in valid_types:
        notification_type = NotificationType.SYSTEM
        
    # Create a test notification
    notification = NotificationService.send_notification(
        user_id=user.id,
        message=message,
        notification_type=notification_type
    )
    
    if notification:
        return Response({
            'status': 'success',
            'message': 'Test notification sent',
            'notification_id': str(notification.id)
        })
    else:
        return Response({
            'status': 'error',
            'message': 'Failed to send test notification'
        }, status=500)
        
@login_required
def notification_list(request):
    """
    Display the notification list page
    """
    return render(request, 'notifications/notification_list.html')