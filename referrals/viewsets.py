from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Referral, ReferralDetails
from .serializers import ReferralSerializer, ReferralDetailsSerializer

class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

class ReferralDetailsViewSet(viewsets.ModelViewSet):
    queryset = ReferralDetails.objects.all()
    serializer_class = ReferralDetailsSerializer
    permission_classes = [IsAuthenticated]