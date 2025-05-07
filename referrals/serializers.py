from rest_framework import serializers
from .models import Referral, ReferralDetails

class ReferralDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralDetails
        fields = '__all__'

class ReferralSerializer(serializers.ModelSerializer):
    details = ReferralDetailsSerializer(many=True, read_only=True)
    
    class Meta:
        model = Referral
        fields = '__all__'