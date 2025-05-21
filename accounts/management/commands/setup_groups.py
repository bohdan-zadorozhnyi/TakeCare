from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from accounts.models import User


class Command(BaseCommand):
    help = 'Create default user groups and assign permissions'

    def handle(self, *args, **kwargs):
        # Create the basic groups
        self.stdout.write('Creating user groups...')
        groups = ['PATIENT', 'DOCTOR', 'ADMIN']
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
            else:
                self.stdout.write(f'Group already exists: {group_name}')
        
        # You can add specific permissions to each group here if needed
        # For example:
        # admin_group = Group.objects.get(name='ADMIN')
        # Add model permissions for admin group
        
        self.stdout.write(self.style.SUCCESS('Groups setup completed!'))
