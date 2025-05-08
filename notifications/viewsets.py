from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from .models import (
    Notification, TechnicalIssueReport, NotificationLog,
    NotificationStatus, NotificationType, NotificationSeverity
)
from .serializers import (
    NotificationSerializer, NotificationDetailSerializer,
    TechnicalIssueReportSerializer, TechnicalIssueReportCreateSerializer,
    TechnicalIssueReportResolveSerializer, NotificationLogSerializer,
    BulkNotificationSerializer
)
from .services import NotificationService, TechnicalIssueService

User = get_user_model()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for viewing and managing notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user only"""
        return Notification.objects.filter(receiver=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve action"""
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = NotificationService.mark_as_read(pk, request.user)
        if notification:
            return Response({'status': 'success'})
        return Response({'status': 'error'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = NotificationService.mark_all_as_read(request.user)
        return Response({'status': 'success', 'count': count})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            receiver=request.user,
            status__in=[NotificationStatus.DELIVERED, NotificationStatus.PENDING]
        ).count()
        return Response({'count': count})


class AdminNotificationViewSet(viewsets.ModelViewSet):
    """API endpoints for admin notifications management"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Only admins can access these endpoints"""
        if self.request.user.role != 'ADMIN':
            return [permissions.IsAdminUser()]
        return super().get_permissions()
    
    def get_queryset(self):
        """Return all notifications for admins"""
        return Notification.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        """Select serializer based on action"""
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        elif self.action == 'send_bulk_notification':
            return BulkNotificationSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['post'])
    def send_bulk_notification(self, request):
        """Send notifications to multiple users"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get users
        user_ids = serializer.validated_data['receivers']
        receivers = User.objects.filter(id__in=user_ids)
        
        if not receivers.exists():
            return Response(
                {'error': 'No valid receivers found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create notifications
        notifications = NotificationService.send_bulk_notification(
            receivers=receivers,
            message=serializer.validated_data['message'],
            subject=serializer.validated_data['subject'],
            notification_type=serializer.validated_data['notification_type'],
            severity=serializer.validated_data['severity'],
            delivery_channel=serializer.validated_data['delivery_channel'],
            sender=request.user,
            is_encrypted=serializer.validated_data['is_encrypted']
        )
        
        return Response({
            'status': 'success',
            'count': len(notifications),
            'notification_ids': [str(n.id) for n in notifications]
        }, status=status.HTTP_201_CREATED)


class TechnicalIssueViewSet(viewsets.ModelViewSet):
    """API endpoints for managing technical issues"""
    serializer_class = TechnicalIssueReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return appropriate technical issues based on user role"""
        user = self.request.user
        
        # Admins can see all issues
        if user.role == 'ADMIN':
            return TechnicalIssueReport.objects.all().order_by('-created_at')
        
        # Regular users can only see their own reports
        return TechnicalIssueReport.objects.filter(reporter=user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Select serializer based on action"""
        if self.action == 'create':
            return TechnicalIssueReportCreateSerializer
        elif self.action == 'resolve':
            return TechnicalIssueReportResolveSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        """Create technical issue report and notify admins"""
        # Use the service to create issue report
        issue = TechnicalIssueService.report_issue(
            user=self.request.user,
            description=serializer.validated_data['description'],
            severity=serializer.validated_data['severity'],
            browser=serializer.validated_data.get('browser', ''),
            operating_system=serializer.validated_data.get('operating_system', ''),
            url=serializer.validated_data.get('url', ''),
            stacktrace=serializer.validated_data.get('stacktrace', '')
        )
        
        # Set the serializer instance for proper response
        serializer.instance = issue
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark issue as resolved"""
        # Check if user is admin
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can resolve issues'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        resolution_notes = serializer.validated_data.get('resolution_notes', '')
        issue = TechnicalIssueService.resolve_issue(pk, request.user, resolution_notes)
        
        if not issue:
            return Response(
                {'error': 'Issue not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({'status': 'success'})
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics for technical issues"""
        # Check if user is admin
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can access dashboard stats'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get counts by severity and status
        total_unresolved = TechnicalIssueReport.objects.filter(resolved=False).count()
        total_resolved = TechnicalIssueReport.objects.filter(resolved=True).count()
        
        critical_count = TechnicalIssueReport.objects.filter(
            resolved=False, 
            severity=NotificationSeverity.CRITICAL
        ).count()
        
        high_count = TechnicalIssueReport.objects.filter(
            resolved=False, 
            severity=NotificationSeverity.HIGH
        ).count()
        
        # Get recent issues
        recent_issues = TechnicalIssueReport.objects.filter(
            resolved=False
        ).order_by('-created_at')[:5]
        
        recent_serializer = TechnicalIssueReportSerializer(recent_issues, many=True)
        
        return Response({
            'total_unresolved': total_unresolved,
            'total_resolved': total_resolved,
            'critical_count': critical_count,
            'high_count': high_count,
            'recent_issues': recent_serializer.data
        })