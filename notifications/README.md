# TakeCare Notification System Documentation

## Overview

The TakeCare notification system allows you to send real-time and persistent notifications to users across the application. Notifications can be triggered by various events, such as appointment creations, message arrivals, or medical record updates.

## Integration with Module Events

The notification system uses Django signals to listen for model changes (creation and updates) and automatically generate notifications. Here's how to integrate your module with notifications:

### Existing Notification Types

The system supports the following notification types:

- `APPOINTMENT`: For appointment scheduling, updates, and reminders
- `PRESCRIPTION`: For prescription creation and updates
- `REFERRAL`: For referral to specialists
- `MEDICAL`: For general medical information
- `MEDICAL_RECORD`: For patient medical record creation and updates
- `ISSUE`: For system issues reported by users and their resolution
- `MESSAGE`: For chat messages and communication
- `SYSTEM`: For general system notifications

### How to Integrate a New Module

To integrate a new module with the notification system:

1. Add your model's import to the signal handlers in `notifications/signals.py`:

```python
try:
    from your_module.models import YourModel
    YOUR_MODULE_ENABLED = True
except ImportError:
    YOUR_MODULE_ENABLED = False
```

2. Create a signal handler for your model's events:

```python
if YOUR_MODULE_ENABLED:
    @receiver(post_save, sender=YourModel)
    def send_your_model_notification(sender, instance, created, **kwargs):
        """
        Send notification when a new instance of your model is created or updated
        """
        try:
            # Your notification logic here
            # Example:
            if created:
                # For a new instance
                message = f"New {instance.some_field} has been created"
            else:
                # For an update
                message = f"{instance.some_field} has been updated"
                
            # Send to appropriate user(s)
            NotificationService.send_notification(
                user_id=instance.user.id,  # Or whoever should receive it
                message=message,
                notification_type=NotificationType.YOUR_TYPE,  # Use an existing type or add a new one
                related_object_id=str(instance.id),
                related_object_type="your_model_name"
            )
            logger.info(f"Notification sent for {instance.id}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
```

3. If you need a new notification type, add it to `notifications/models.py`:

```python
class NotificationType(models.TextChoices):
    # ... existing types ...
    YOUR_TYPE = 'YOUR_TYPE', 'Your Type Label'
```

4. Update the frontend to display your notification type correctly:
   - Add a filter option in `notification_list.html`
   - Add a type label and icon in the notification templates

## Sending Notifications Manually

You can also send notifications programmatically without using signals:

```python
from notifications.services import NotificationService
from notifications.models import NotificationType

# Send to a single user
NotificationService.send_notification(
    user_id=user_id,
    message="Your custom notification message",
    notification_type=NotificationType.SYSTEM,  # Or another type
    related_object_id=str(related_object_id),  # Optional
    related_object_type="related_object_type"   # Optional
)

# Send to multiple users
NotificationService.send_bulk_notification(
    user_ids=[user_id1, user_id2, user_id3],
    message="Bulk notification message",
    notification_type=NotificationType.SYSTEM
)
```

## Testing Notifications

To test notifications, you can use the included scripts:

- `create_test_notifications.py`: Creates random test notifications
- `create_specific_notifications.py`: Creates specific notification scenarios
- `create_module_notifications.py`: Tests notifications for new modules

## WebSocket Integration

The notification system uses Django Channels and WebSockets to deliver real-time notifications. When a notification is created, it's sent through the WebSocket to any connected clients for the target user.

## UI Components

The system includes several UI components:

1. Notification dropdown in the navbar
2. Notification badge with unread count
3. Full notification list page with filtering and search
4. "Mark as Read" functionality

## Best Practices

1. Keep notification messages concise and informative
2. Include only necessary information in the notification
3. For sensitive data, use the encryption feature
4. Always handle exceptions in your signal handlers to prevent breaking functionality
5. Test notifications thoroughly when integrating a new module

## Troubleshooting

If notifications aren't being sent or received:

1. Check Django logs for errors in signal handlers
2. Verify that WebSocket connections are established
3. Ensure the notification channel group names match the user IDs
4. Test with the included test scripts
