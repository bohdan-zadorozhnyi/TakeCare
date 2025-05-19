from django.core.management.base import BaseCommand
from accounts.models import User, DoctorProfile
from referrals.models import DoctorCategory

class Command(BaseCommand):
    help = 'Ensure all doctors have doctor profiles with specializations'

    def handle(self, *args, **options):
        doctors = User.objects.filter(role='DOCTOR')
        self.stdout.write(f"Found {doctors.count()} doctors")
        
        for doctor in doctors:
            self.stdout.write(f"Processing {doctor.name} ({doctor.id})")
            
            profile, created = DoctorProfile.objects.get_or_create(
                user=doctor,
                defaults={
                    'specialization': DoctorCategory.CARDIOLOGIST,
                    'work_address': doctor.address,
                    'license_uri': f'https://license.example.org/{doctor.id}'
                }
            )
            
            if created:
                self.stdout.write(f"  Created new profile with specialization: {profile.get_specialization_display()}")
            else:
                self.stdout.write(f"  Existing profile found with specialization: {profile.get_specialization_display()}")
        
        self.stdout.write(self.style.SUCCESS("All doctors now have profiles"))
