from .models import Notification, NotificationStatus

def notification_context(request):
    """
    Add notification info to template context
    """
    context = {
        'unread_notification_count': 0
    }
    
    if request.user.is_authenticated:
        context['unread_notification_count'] = Notification.objects.filter(
            receiver=request.user,
            status=NotificationStatus.UNREAD
        ).count()
    
    return context
