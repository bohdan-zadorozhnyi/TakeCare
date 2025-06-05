from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Issue
from .forms import IssueReportForm, AdminIssueResponseForm
from notifications.services import NotificationService
from notifications.models import NotificationType

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@login_required
def report_issue(request):
    """
    View for users to report new issues
    """
    if request.method == 'POST':
        form = IssueReportForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.save()
            
            # Notify admins about the new issue
            admins = issue.user._meta.model.objects.filter(role='ADMIN')
            for admin in admins:
                NotificationService.send_notification(
                    user_id=str(admin.id),
                    message=f"New issue reported: {issue.title}",
                    notification_type=NotificationType.SYSTEM,
                    related_object_id=str(issue.id),
                    related_object_type="issue"
                )
            
            messages.success(request, "Your issue has been reported successfully.")
            return redirect('issues:my_issues')
    else:
        form = IssueReportForm()
    
    return render(request, 'issues/report_issue.html', {'form': form})

@login_required
def my_issues(request):
    """
    View for users to see their reported issues
    """
    issues = Issue.objects.filter(user=request.user)
    return render(request, 'issues/my_issues.html', {'issues': issues})

@login_required
def issue_detail(request, issue_id):
    """
    View for users to see details of a specific issue
    """
    issue = get_object_or_404(Issue, id=issue_id)
    
    # Check if the user is the owner or an admin
    if request.user != issue.user and not is_admin(request.user):
        messages.error(request, "You don't have permission to view this issue.")
        return redirect('core:home')
    
    return render(request, 'issues/issue_detail.html', {'issue': issue})

@login_required
@user_passes_test(is_admin)
def admin_issues(request):
    """
    View for admins to see all issues
    """
    status = request.GET.get('status', None)
    
    if status and status in dict(Issue.STATUS_CHOICES).keys():
        issues = Issue.objects.filter(status=status)
    else:
        issues = Issue.objects.all()
    
    return render(request, 'issues/admin_issues.html', {
        'issues': issues,
        'current_status': status,
        'status_choices': Issue.STATUS_CHOICES
    })

@login_required
@user_passes_test(is_admin)
def admin_issue_detail(request, issue_id):
    """
    View for admins to manage a specific issue
    """
    issue = get_object_or_404(Issue, id=issue_id)
    
    if request.method == 'POST':
        form = AdminIssueResponseForm(request.POST, instance=issue)
        if form.is_valid():
            old_status = issue.status
            issue = form.save(commit=False)
            
            # Check if status changed to resolved
            if old_status != 'RESOLVED' and issue.status == 'RESOLVED':
                issue.resolved_date = timezone.now()
                
                # Create notification for the user when their issue is resolved
                NotificationService.send_notification(
                    user_id=str(issue.user.id),
                    message=f"Your issue '{issue.title}' has been resolved.",
                    notification_type=NotificationType.SYSTEM,
                    related_object_id=str(issue.id),
                    related_object_type="issue_resolved"
                )
            
            issue.save()
            messages.success(request, "Issue updated successfully.")
            return redirect('issues:admin_issues')
    else:
        form = AdminIssueResponseForm(instance=issue)
    
    return render(request, 'issues/admin_issue_detail.html', {
        'issue': issue,
        'form': form
    })