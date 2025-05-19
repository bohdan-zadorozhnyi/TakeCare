from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.apps import apps
from referrals.models import DoctorCategory


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Create default user groups after migrations.
    This ensures that groups exist before any users are created.
    """
    groups = ['PATIENT', 'DOCTOR', 'ADMIN']
    
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)


@receiver(post_save)
def create_doctor_profile(sender, instance, created, **kwargs):
    """
    Create a doctor profile whenever a doctor user is created or updated.
    """
    # Only proceed if this is a User model
    if sender.__name__ != 'User':
        return
    
    # Only proceed for doctor users
    if instance.role != 'DOCTOR':
        return
        
    # Get the model classes (to avoid circular imports)
    DoctorProfile = apps.get_model('accounts', 'DoctorProfile')
    
    # Check if a profile exists
    if not hasattr(instance, 'doctor_profile'):
        # Create a profile with default values
        DoctorProfile.objects.create(
            user=instance,
            specialization=DoctorCategory.CARDIOLOGIST,
            work_address=instance.address,
            license_uri=f'https://medical-license.org/{instance.id}'
        )
