import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Notification, NotificationLog


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    """
    
    async def connect(self):
        """
        Connect to the notification channel for the authenticated user
        """
        self.user = self.scope["user"]
        
        if self.user.is_authenticated:
            # Create a notification group specific to this user
            self.notification_group_name = f"notifications_{self.user.id}"
            
            # Join the group
            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Send unread count and recent notifications on connect
            await self.send_status_on_connect()
        else:
            # Reject the connection if the user is not authenticated
            await self.close()
    
    async def disconnect(self, close_code):
        """
        Disconnect from the notification channel group
        """
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages (e.g., for marking notifications as read)
        """
        data = json.loads(text_data)
        action = data.get('action', None)
        
        if action == 'mark_read':
            notification_id = data.get('id')
            if notification_id:
                # Mark notification as read
                success = await self.mark_notification_read(notification_id)
                
                # Send back confirmation
                await self.send(text_data=json.dumps({
                    'action': 'mark_read_response',
                    'id': notification_id,
                    'success': success
                }))
                
                # Update unread count
                if success:
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'action': 'unread_count_update',
                        'count': unread_count
                    }))
        
        elif action == 'mark_all_read':
            # Mark all notifications as read
            count = await self.mark_all_notifications_read()
            
            # Send back confirmation
            await self.send(text_data=json.dumps({
                'action': 'mark_all_read_response',
                'count': count,
                'success': True
            }))
            
            # Update unread count (should be 0)
            await self.send(text_data=json.dumps({
                'action': 'unread_count_update',
                'count': 0
            }))
    
    async def notification_message(self, event):
        """
        Receive notification message from notification group
        and send it to the WebSocket
        """
        message = event['message']
        
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'action': 'new_notification',
            'notification': message
        }))
        
        # Update unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'action': 'unread_count_update',
            'count': unread_count
        }))
    
    async def send_status_on_connect(self):
        """
        Send initial status to client when they connect
        """
        unread_count = await self.get_unread_count()
        recent_notifications = await self.get_recent_notifications()
        
        await self.send(text_data=json.dumps({
            'action': 'initial_status',
            'unread_count': unread_count,
            'recent_notifications': recent_notifications
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """
        Get the count of unread notifications for the current user
        """
        return Notification.objects.filter(receiver=self.user, read=False).count()
    
    @database_sync_to_async
    def get_recent_notifications(self, limit=10):
        """
        Get recent notifications for the current user
        """
        notifications = Notification.objects.filter(receiver=self.user).order_by('-date')[:limit]
        
        return [
            {
                'id': str(notification.id),
                'message': notification.message,
                'type': notification.notification_type,
                'date': notification.date.isoformat(),
                'sender': notification.sender.name if notification.sender else None,
                'read': notification.read,
                'related_object_id': notification.related_object_id,
                'related_object_type': notification.related_object_type,
            }
            for notification in notifications
        ]
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read
        """
        try:
            notification = Notification.objects.get(id=notification_id, receiver=self.user)
            notification.read = True
            notification.save(update_fields=['read'])
            
            # Log this action
            NotificationLog.objects.create(
                notification=notification,
                action='read',
                details=f"Notification marked as read by {self.user.name} via WebSocket"
            )
            
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """
        Mark all notifications as read for the current user
        """
        notifications = Notification.objects.filter(receiver=self.user, read=False)
        count = notifications.count()
        
        if count > 0:
            notifications.update(read=True)
            
            # Log this action for the first notification
            if notifications:
                NotificationLog.objects.create(
                    notification=notifications.first(),
                    action='bulk_read',
                    details=f"{count} notifications marked as read by {self.user.name} via WebSocket"
                )
        
        return count