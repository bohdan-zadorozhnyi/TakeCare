import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications
    """
    
    async def connect(self):
        """
        Called when a WebSocket connection is established
        """
        self.user = self.scope["user"]
        self.notification_group_name = f"notifications_{self.user.id}"
        
        # Reject the connection if the user is not authenticated
        if self.user.is_anonymous:
            logger.warning(f"Anonymous user attempted to connect to notification socket")
            await self.close()
            return
            
        # Add this channel to the user's notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"User {self.user.id} connected to notification socket")
        
        # Send any undelivered notifications on connect
        await self.send_undelivered_notifications()
        
    async def disconnect(self, close_code):
        """
        Called when a WebSocket connection is closed
        """
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
        logger.info(f"User {self.user.id if not self.user.is_anonymous else 'anonymous'} disconnected from notification socket")
    
    async def receive(self, text_data):
        """
        Called when a message is received from the WebSocket
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'status': 'success',
                        'action': 'mark_read',
                        'notification_id': notification_id
                    }))
            elif action == 'mark_all_read':
                await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'status': 'success',
                    'action': 'mark_all_read'
                }))
        except json.JSONDecodeError:
            logger.error(f"Received invalid JSON from client: {text_data}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)
    
    async def notification_message(self, event):
        """
        Send a notification to the connected client
        """
        message = event["message"]
        notification_id = event.get("notification_id")
        notification_type = event.get("notification_type", "SYSTEM")
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'notification_id': str(notification_id),
            'type': notification_type
        }))
        
        # Mark the notification as delivered in the database
        if notification_id:
            await self.mark_notification_delivered(notification_id)
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read
        """
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, receiver=self.user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"User {self.user.id} tried to mark non-existent notification {notification_id} as read")
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """
        Mark all notifications as read for the current user
        """
        from .models import Notification, NotificationStatus
        Notification.objects.filter(
            receiver=self.user, 
            status=NotificationStatus.UNREAD
        ).update(status=NotificationStatus.READ)
        return True
    
    @database_sync_to_async
    def mark_notification_delivered(self, notification_id):
        """
        Mark a notification as delivered
        """
        from .models import Notification
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_delivered()
            return True
        except Notification.DoesNotExist:
            logger.warning(f"Could not mark non-existent notification {notification_id} as delivered")
            return False
    
    @database_sync_to_async
    def get_undelivered_notifications(self):
        """
        Retrieve undelivered notifications for the connected client
        """
        from .models import Notification
        
        undelivered = Notification.objects.filter(
            receiver=self.user,
            is_delivered=False
        ).order_by('-date')[:50]  # Limit to most recent 50
        
        # Just get the notifications and record the attempt, we'll send them in the async method
        notifications_data = []
        for notification in undelivered:
            notification.record_delivery_attempt()
            notifications_data.append({
                "message": notification.message,
                "notification_id": str(notification.id),
                "type": notification.notification_type
            })
        
        return notifications_data

    async def send_undelivered_notifications(self):
        """
        Send all undelivered notifications to the connected client
        """
        notifications = await self.get_undelivered_notifications()
        
        for notification_data in notifications:
            # Now we can use the channel layer directly in this async method
            await self.channel_layer.group_send(
                self.notification_group_name,
                {
                    "type": "notification_message",
                    **notification_data
                }
            )
