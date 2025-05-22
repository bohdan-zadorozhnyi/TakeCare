from .models import Notification, NotificationStatus

def notification_context(request):
    """
    Add notification info to template context
    """
    context = {
        'unread_notification_count': 0,
        'is_notifications_page': False
    }
    
    # Check if current page is notifications related
    current_path = request.path
    if current_path.startswith('/notifications/'):
        context['is_notifications_page'] = True
    
    if request.user.is_authenticated:
        context['unread_notification_count'] = Notification.objects.filter(
            receiver=request.user,
            status=NotificationStatus.UNREAD
        ).count()
    
    return context
