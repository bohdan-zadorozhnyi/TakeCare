from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.db.models import Q
from .models import (
    Notification, NotificationStatus, TechnicalIssueReport, 
    NotificationSeverity, NotificationType
)
from .services import NotificationService, TechnicalIssueService
import json


@login_required
def notification_list_view(request):
    """View for displaying user notifications"""
    notifications = Notification.objects.filter(receiver=request.user).order_by('-created_at')
    
    # Handle filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        notifications = notifications.filter(status=status_filter)
        
    # Pagination
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    context = {
        'notifications': notifications,
        'unread_count': Notification.objects.filter(
            receiver=request.user, 
            status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
        ).count(),
    }
    
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail_view(request, pk):
    """View for displaying a single notification"""
    notification = get_object_or_404(Notification, id=pk, receiver=request.user)
    
    # Mark as read if not already
    if notification.status != NotificationStatus.READ:
        notification.mark_as_read()
    
    context = {
        'notification': notification
    }
    
    return render(request, 'notifications/notification_detail.html', context)


@login_required
@require_POST
def mark_notification_read(request, pk):
    """AJAX endpoint to mark a notification as read"""
    notification = NotificationService.mark_as_read(pk, request.user)
    
    if notification:
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """AJAX endpoint to mark all notifications as read"""
    count = NotificationService.mark_all_as_read(request.user)
    return JsonResponse({'status': 'success', 'count': count})


@login_required
@require_GET
def get_unread_notification_count(request):
    """AJAX endpoint to get unread notification count"""
    count = Notification.objects.filter(
        receiver=request.user,
        status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
    ).count()
    return JsonResponse({'count': count})


@login_required
def report_technical_issue(request):
    """View for reporting technical issues"""
    if request.method == 'POST':
        description = request.POST.get('description')
        severity = request.POST.get('severity', 'MEDIUM')
        
        # Browser information
        browser = request.POST.get('browser', '')
        operating_system = request.POST.get('operating_system', '')
        url = request.POST.get('url', request.META.get('HTTP_REFERER', ''))
        
        # Create issue
        issue = TechnicalIssueService.report_issue(
            user=request.user,
            description=description,
            severity=severity,
            browser=browser,
            operating_system=operating_system,
            url=url
        )
        
        messages.success(request, "Your issue has been reported. Thank you for helping improve TakeCare!")
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': "Your issue has been reported. Thank you for helping improve TakeCare!"
            })
            
        return redirect('notifications:issue_reported')
    
    # GET request - show form
    context = {
        'severity_choices': NotificationSeverity.choices,
    }
    
    return render(request, 'notifications/report_issue.html', context)


@login_required
def issue_reported_view(request):
    """Thank you page after submitting an issue"""
    return render(request, 'notifications/issue_reported.html')


@login_required
def user_reported_issues_view(request):
    """View for users to see their reported issues"""
    issues = TechnicalIssueReport.objects.filter(reporter=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(issues, 10)
    page = request.GET.get('page')
    issues = paginator.get_page(page)
    
    context = {
        'issues': issues
    }
    
    return render(request, 'notifications/user_reported_issues.html', context)


# ADMIN VIEWS
@login_required
def admin_technical_issues_dashboard(request):
    """Admin dashboard for technical issues"""
    if request.user.role != 'ADMIN':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
        
    # Get counts
    total_unresolved = TechnicalIssueReport.objects.filter(resolved=False).count()
    total_resolved = TechnicalIssueReport.objects.filter(resolved=True).count()
    critical_count = TechnicalIssueReport.objects.filter(resolved=False, severity='CRITICAL').count()
    high_count = TechnicalIssueReport.objects.filter(resolved=False, severity='HIGH').count()
    
    # Get issues with filters
    issues = TechnicalIssueReport.objects.all()
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter == 'resolved':
        issues = issues.filter(resolved=True)
    elif status_filter == 'unresolved':
        issues = issues.filter(resolved=False)
    
    severity_filter = request.GET.get('severity')
    if severity_filter:
        issues = issues.filter(severity=severity_filter)
    
    # Default sort
    issues = issues.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(issues, 25)
    page = request.GET.get('page')
    issues = paginator.get_page(page)
    
    context = {
        'issues': issues,
        'total_unresolved': total_unresolved,
        'total_resolved': total_resolved,
        'critical_count': critical_count,
        'high_count': high_count,
        'severity_choices': NotificationSeverity.choices,
        'active_status': status_filter or 'all',
        'active_severity': severity_filter or 'all',
    }
    
    return render(request, 'notifications/admin_issues_dashboard.html', context)


@login_required
@require_POST
def admin_resolve_issue(request, pk):
    """Admin view to resolve an issue"""
    if request.user.role != 'ADMIN':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')
        
    resolution_notes = request.POST.get('resolution_notes', '')
    issue = TechnicalIssueService.resolve_issue(pk, request.user, resolution_notes)
    
    if issue:
        messages.success(request, "Issue has been resolved successfully.")
    else:
        messages.error(request, "Issue not found.")
    
    # Handle AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success' if issue else 'error'})
    
    return redirect('notifications:admin_issues_dashboard')


@login_required
def admin_notification_dashboard(request):
    """Admin dashboard for sending notifications"""
    if request.user.role != 'ADMIN':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get all users for selection
    from accounts.models import User
    users = User.objects.exclude(role='ADMIN').order_by('role', 'name')
    doctors = users.filter(role='DOCTOR')
    patients = users.filter(role='PATIENT')
    
    context = {
        'users': users,
        'doctors': doctors,
        'patients': patients,
        'notification_types': NotificationType.choices,
        'severity_choices': NotificationSeverity.choices,
    }
    
    return render(request, 'notifications/admin_notification_dashboard.html', context)


@login_required
@require_POST
def admin_send_notification(request):
    """Admin endpoint to send notifications"""
    if request.user.role != 'ADMIN':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')
    
    try:
        data = json.loads(request.body) if request.body else request.POST
        
        # Get receivers
        receiver_ids = data.getlist('receivers[]') if hasattr(data, 'getlist') else data.get('receivers', [])
        receiver_type = data.get('receiver_type', 'specific')
        
        from accounts.models import User
        
        if receiver_type == 'all_users':
            receivers = User.objects.all()
        elif receiver_type == 'all_doctors':
            receivers = User.objects.filter(role='DOCTOR')
        elif receiver_type == 'all_patients':
            receivers = User.objects.filter(role='PATIENT')
        else:
            # Specific users
            receivers = User.objects.filter(id__in=receiver_ids)
        
        if not receivers:
            return JsonResponse({'status': 'error', 'message': 'No recipients selected'}, status=400)
        
        # Create message
        subject = data.get('subject', '')
        message = data.get('message', '')
        notification_type = data.get('notification_type', NotificationType.ADMIN)
        severity = data.get('severity', NotificationSeverity.MEDIUM)
        
        if not message:
            return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)
        
        # Send notifications
        notifications = NotificationService.send_bulk_notification(
            receivers=receivers,
            message=message,
            subject=subject,
            notification_type=notification_type,
            severity=severity,
            sender=request.user
        )
        
        messages.success(
            request, 
            f"Sent {len(notifications)} notifications successfully."
        )
        
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success', 
                'count': len(notifications)
            })
        
        return redirect('notifications:admin_notification_dashboard')
        
    except Exception as e:
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        messages.error(request, f"Error: {str(e)}")
        return redirect('notifications:admin_notification_dashboard')