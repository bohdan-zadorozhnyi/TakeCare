from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, TechnicalIssueReport, NotificationLog
from accounts.serializers import UserSerializer

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'subject', 'notification_type', 'severity',
            'status', 'created_at', 'delivered_at', 'read_at', 'is_encrypted',
            'is_resolved'
        ]
        read_only_fields = ['id', 'created_at', 'delivered_at', 'read_at', 'is_encrypted']
    
    def to_representation(self, instance):
        """Add message to representation only if it's not encrypted"""
        data = super().to_representation(instance)
        if not instance.is_encrypted:
            data['message'] = instance.message
        return data


class NotificationDetailSerializer(NotificationSerializer):
    """Detailed notification serializer including message"""
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + ['message']
    
    def to_representation(self, instance):
        """Include message safely"""
        data = super(NotificationSerializer, self).to_representation(instance)
        
        # Always include message even if encrypted (will be handled by the model property)
        data['message'] = instance.message
        
        return data


class TechnicalIssueReportSerializer(serializers.ModelSerializer):
    """Serializer for technical issue reports"""
    reporter = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = TechnicalIssueReport
        fields = [
            'id', 'reporter', 'description', 'severity', 'created_at', 
            'resolved', 'resolved_by', 'resolved_at', 'resolution_notes',
            'browser', 'operating_system', 'url'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at', 'resolved_by']


class TechnicalIssueReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating technical issue reports"""
    
    class Meta:
        model = TechnicalIssueReport
        fields = ['description', 'severity', 'browser', 'operating_system', 'url', 'stacktrace']


class TechnicalIssueReportResolveSerializer(serializers.Serializer):
    """Serializer for resolving technical issues"""
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs"""
    
    class Meta:
        model = NotificationLog
        fields = ['id', 'notification', 'timestamp', 'action', 'details']
        read_only_fields = ['id', 'notification', 'timestamp', 'action', 'details']


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for sending bulk notifications"""
    receivers = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of user IDs to send notification to"
    )
    subject = serializers.CharField(required=True, max_length=255)
    message = serializers.CharField(required=True)
    notification_type = serializers.CharField(required=False, default='SYSTEM')
    severity = serializers.CharField(required=False, default='MEDIUM')
    delivery_channel = serializers.CharField(required=False, default='IN_APP')
    is_encrypted = serializers.BooleanField(required=False, default=False)