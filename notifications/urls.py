from django.urls import path, include
from . import views
from . import api

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/', include(api)),
    
    # User notification views
    path('', views.notification_list_view, name='list'),
    path('<uuid:pk>/', views.notification_detail_view, name='detail'),
    path('<uuid:pk>/mark-read/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('unread-count/', views.get_unread_notification_count, name='unread_count'),
    
    # Technical issue reporting
    path('report-issue/', views.report_technical_issue, name='report_issue'),
    path('issue-reported/', views.issue_reported_view, name='issue_reported'),
    path('my-reported-issues/', views.user_reported_issues_view, name='my_reported_issues'),
    
    # Admin views
    path('admin/issues/', views.admin_technical_issues_dashboard, name='admin_issues_dashboard'),
    path('admin/issues/<uuid:pk>/resolve/', views.admin_resolve_issue, name='admin_resolve_issue'),
    path('admin/send/', views.admin_notification_dashboard, name='admin_notification_dashboard'),
    path('admin/send/process/', views.admin_send_notification, name='admin_send_notification'),
]