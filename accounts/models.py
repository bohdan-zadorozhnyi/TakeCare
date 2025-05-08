from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.db import models
import uuid
from referrals.models import DoctorCategory

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)

        if "birth_date" not in extra_fields and extra_fields.get("is_superuser", False):
            extra_fields["birth_date"] = "2000-01-01"

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('name', 'Admin User')
        extra_fields.setdefault('phone_number', '0000000000')
        extra_fields.setdefault('personal_id', 'admin-id-0000')
        extra_fields.setdefault('birth_date', '2000-01-01')
        extra_fields.setdefault('gender', 'Other')
        extra_fields.setdefault('address', 'Admin Address')
        extra_fields.setdefault('role', 'ADMIN')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    personal_id = models.CharField(max_length=50, unique=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    role = models.CharField(max_length=20, choices=[
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Administrator')
    ])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name="custom_user_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_set", blank=True)

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default_avatar.jpg')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.name

    class Meta:
        permissions = [
            ("block_user", "Can block or unblock a user"),
            ("list_user", "Can see the whole or partial list of all users"),
        ]

class DoctorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='doctor_profile')
    license_uri = models.URLField(unique=True)
    specialization = models.CharField(
        max_length=50,
        choices=DoctorCategory.choices,
        default=DoctorCategory.PEDIATRICIAN,
    )
    work_address = models.TextField()


class PatientProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='patient_profile')

class AdminProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='admin_profile')
