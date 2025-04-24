from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Notification, NotificationLog
from .services import NotificationService


@login_required
def notification_list(request):
    """
    View for displaying a list of user's notifications
    """
    notifications = Notification.objects.filter(receiver=request.user).order_by('-date')
    
    # Filter by type if requested
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Filter by read status if requested
    read_status = request.GET.get('read')
    if read_status == 'read':
        notifications = notifications.filter(read=True)
    elif read_status == 'unread':
        notifications = notifications.filter(read=False)
    
    # Paginate the results
    paginator = Paginator(notifications, 20)  # Show 20 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'unread_count': Notification.objects.filter(receiver=request.user, read=False).count(),
        'notification_types': Notification.objects.filter(receiver=request.user).values_list('notification_type', flat=True).distinct(),
        'filter_type': notification_type,
        'filter_read': read_status,
    }
    
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, notification_id):
    """
    View a single notification
    """
    notification = get_object_or_404(Notification, id=notification_id, receiver=request.user)
    
    # Mark as read if not already
    if not notification.read:
        NotificationService.mark_as_read(notification_id, request.user)
    
    # Handle redirect to related object if available
    if request.GET.get('redirect') == 'true' and notification.related_object_type and notification.related_object_id:
        if notification.related_object_type == 'appointment':
            return redirect('appointment_detail', appointment_id=notification.related_object_id)
        elif notification.related_object_type == 'prescription':
            return redirect('prescriptions:prescription_detail', pk=notification.related_object_id)
        elif notification.related_object_type == 'referral':
            return redirect('referral_detail', referral_id=notification.related_object_id)
        elif notification.related_object_type == 'issue':
            return redirect('issue_detail', issue_id=notification.related_object_id)
    
    # Get decrypted data if available
    decrypted_data = notification.decrypt_data() if notification.encrypted_data else None
    
    context = {
        'notification': notification,
        'decrypted_data': decrypted_data,
    }
    
    return render(request, 'notifications/notification_detail.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read
    """
    success = NotificationService.mark_as_read(notification_id, request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': success})
    
    # Redirect back to notifications list or a specific URL
    next_url = request.GET.get('next', 'notification_list')
    return redirect(next_url)


@login_required
def mark_all_read(request):
    """
    Mark all notifications as read
    """
    count = NotificationService.mark_all_as_read(request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': count})
    
    # Redirect back to notifications list
    return redirect('notification_list')


@login_required
def get_unread_count(request):
    """
    Get the count of unread notifications (for AJAX requests)
    """
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'count': count})


# Admin views for sending notifications
@login_required
def admin_send_notification(request):
    """
    Admin view for sending notifications to users
    """
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    if request.method == 'POST':
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type')
        recipient_role = request.POST.get('recipient_role')
        
        if message and recipient_role:
            notifications = NotificationService.send_notifications_to_role(
                message=message,
                role=recipient_role,
                notification_type=notification_type,
                sender=request.user
            )
            
            return JsonResponse({
                'success': True,
                'count': len(notifications),
                'message': f'Successfully sent {len(notifications)} notifications.'
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Missing required fields.'
        })
    
    # GET request - show the form
    from accounts.models import User
    
    context = {
        'roles': User.ROLE_CHOICES
    }
    
    return render(request, 'notifications/admin_send.html', context)