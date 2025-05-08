import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Notification, NotificationStatus


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for delivering real-time notifications"""
    
    async def connect(self):
        """Connect to notification channel and join user-specific group"""
        self.user = self.scope["user"]
        
        # Anonymous users can't receive notifications
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a user-specific notification group
        self.notification_group_name = f"user_{self.user.id}_notifications"
        
        # Join the group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send any unread notifications on connect
        unread = await self.get_unread_notifications()
        if unread:
            await self.send(text_data=json.dumps({
                'type': 'unread_notifications',
                'notifications': unread
            }))
    
    async def disconnect(self, close_code):
        """Leave notification group on disconnect"""
        # Leave the group if it was joined
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle receiving messages from WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            # Handle marking notifications as read
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked_read',
                        'notification_id': notification_id,
                        'success': success
                    }))
            
            # Handle marking all notifications as read
            elif action == 'mark_all_read':
                count = await self.mark_all_read()
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_marked_read',
                    'count': count
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def notification_message(self, event):
        """Handle notification.message type and forward to client"""
        # Forward the notification to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': {
                'id': event.get('notification_id'),
                'subject': event.get('subject'),
                'message': event.get('message'),
                'notification_type': event.get('notification_type'),
                'severity': event.get('severity'),
                'created_at': event.get('created_at'),
                'sender': event.get('sender')
            }
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Get unread notifications for the current user"""
        notifications = Notification.objects.filter(
            receiver=self.user, 
            status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
        ).order_by('-created_at')[:10]  # Limit to most recent 10
        
        return [
            {
                'id': str(notification.id),
                'subject': notification.subject,
                'message': notification.message if not notification.is_encrypted else None,
                'notification_type': notification.notification_type,
                'severity': notification.severity,
                'created_at': notification.created_at.isoformat(),
                'sender': notification.sender.name if notification.sender else None
            }
            for notification in notifications
        ]
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, receiver=self.user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_read(self):
        """Mark all notifications as read for this user"""
        unread = Notification.objects.filter(
            receiver=self.user, 
            status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
        )
        count = unread.count()
        
        # Bulk update
        unread.update(
            status=NotificationStatus.READ,
            read_at=timezone.now()
        )
        
        return count