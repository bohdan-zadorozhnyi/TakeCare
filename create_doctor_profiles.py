#!/usr/bin/env python
"""
This script ensures that all doctors have doctor profiles with specializations.
Run it with:
python manage.py shell < create_doctor_profiles.py
"""

from accounts.models import User, DoctorProfile
from referrals.models import DoctorCategory

print("Creating doctor profiles for all doctors...")
doctors = User.objects.filter(role='DOCTOR')
print(f"Found {doctors.count()} doctors")

for doctor in doctors:
    print(f"Processing {doctor.name} ({doctor.id})")
    
    profile, created = DoctorProfile.objects.get_or_create(
        user=doctor,
        defaults={
            'specialization': DoctorCategory.CARDIOLOGIST,
            'work_address': doctor.address,
            'license_uri': f'https://license.example.org/{doctor.id}'
        }
    )
    
    if created:
        print(f"  Created new profile with specialization: {profile.get_specialization_display()}")
    else:
        print(f"  Existing profile found with specialization: {profile.get_specialization_display()}")

print("All doctors now have profiles")
