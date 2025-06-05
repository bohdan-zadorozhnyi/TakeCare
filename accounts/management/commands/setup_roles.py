from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from appointments.models import Appointment, AppointmentSlot
from articles.models import Article
from prescriptions.models import Prescription
from referrals.models import Referral
from accounts.models import User
from medical.models import MedicalRecord
from calendar_app.models import AppointmentNote

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        role_permissions = {
            'ADMIN': {
                Appointment: ['add', 'change', 'delete', 'view'],
                AppointmentSlot: ['add', 'change', 'delete', 'view'],
                Prescription: ['add', 'change', 'delete', 'view', 'list','search'],
                Referral: ['add', 'change', 'delete', 'view', 'search', 'list'],
                MedicalRecord: ['add', 'change', 'delete', 'view', 'search', 'list'],
                User: ['add', 'change', 'delete', 'view', 'block', 'list'],
                Article: ['add', 'change', 'delete', 'view', 'list'],
            },
            'DOCTOR': {
                Appointment: ['change', 'delete', 'view'],
                AppointmentSlot: ['add', 'change', 'delete', 'view'],
                Prescription: ['add', 'change', 'delete', 'view', 'list','search'],
                Referral: ['add', 'change', 'delete', 'view', 'search', 'list'],
                MedicalRecord: ['add', 'change', 'delete', 'view', 'search', 'list'],
                User: ['searchPatient'],
                Article: ['view'],
                AppointmentNote: ['add', 'change', 'delete', 'view'],
            },
            'PATIENT': {
                Appointment: ['add', 'change', 'delete', 'view'],
                AppointmentSlot: ['view'],
                Prescription: ['view', 'list', 'search'],
                Referral: ['view', 'search', 'list'],
                MedicalRecord: ['view', 'search', 'list'],
                Article: ['view'],
            }
        }

        for role, model_permissions in role_permissions.items():
            group, created = Group.objects.get_or_create(name=role)

            for model, actions in model_permissions.items():
                content_type = ContentType.objects.get_for_model(model)
                for action in actions:
                    codename = f"{action}_{model._meta.model_name}"
                    try:
                        perm = Permission.objects.get(codename=codename, content_type=content_type)
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Permission not found: {codename}"))

        self.stdout.write(self.style.SUCCESS("Role groups and permissions set up successfully."))