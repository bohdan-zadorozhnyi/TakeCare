from rest_framework import serializers
from .models import Notification, NotificationType

class NotificationSerializer(serializers.ModelSerializer):
    receiver_name = serializers.SerializerMethodField()
    receiver_email = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'receiver', 'receiver_name', 'receiver_email', 
            'message', 'date', 'type', 'status', 
            'related_object_id', 'related_object_type',
            'is_delivered', 'data'
        ]
        read_only_fields = [
            'id', 'date', 'is_delivered', 'receiver_name', 
            'receiver_email', 'data'
        ]
    
    def get_receiver_name(self, obj):
        return obj.receiver.name if hasattr(obj.receiver, 'name') else obj.receiver.username
    
    def get_receiver_email(self, obj):
        return obj.receiver.email
    
    def get_data(self, obj):
        # Only decrypt sensitive data if it's a safe type of notification
        sensitive_types = [
            NotificationType.MEDICAL, 
            NotificationType.PRESCRIPTION
        ]
        
        if obj.sensitive_data and obj.type not in sensitive_types:
            return obj.decrypt_data()
        return None
    
    def create(self, validated_data):
        """
        Ensure only staff users can create notifications directly
        """
        user = self.context['request'].user
        if not user.is_staff:
            raise serializers.ValidationError(
                "Only staff users can create notifications directly."
            )
        return super().create(validated_data)