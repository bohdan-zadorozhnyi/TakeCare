from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    path('report/', views.report_issue, name='report_issue'),
    path('my-issues/', views.my_issues, name='my_issues'),
    path('issue/<uuid:issue_id>/', views.issue_detail, name='issue_detail'),
    path('admin/issues/', views.admin_issues, name='admin_issues'),
    path('admin/issue/<uuid:issue_id>/', views.admin_issue_detail, name='admin_issue_detail'),
]