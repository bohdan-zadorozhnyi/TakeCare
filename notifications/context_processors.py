from .services import NotificationService

def notification_context(request):
    """
    Context processor that provides notification count to all templates
    """
    context = {
        'unread_notifications': 0
    }
    
    if request.user.is_authenticated:
        context['unread_notifications'] = NotificationService.get_unread_count(request.user)
        
    return context