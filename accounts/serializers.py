from rest_framework import serializers
from .models import User, DoctorProfile, PatientProfile, AdminProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone_number', 'birth_date', 'gender', 'address', 'role']


class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['license_uri', 'specialization', 'work_address']

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        # fields = ['medical_history']
