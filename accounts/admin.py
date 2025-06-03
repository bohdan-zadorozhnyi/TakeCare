from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, DoctorProfile, PatientProfile, AdminProfile
from django.utils.translation import gettext_lazy as _
from .forms import AdminCreateUserForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminCreateUserForm
    model = User
    list_display = ('email', 'name', 'role', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'name')

    fieldsets = (
        (None, {'fields': ('email', 'password', 'avatar')}),
        (_('Personal info'), {'fields': ('name', 'phone_number', 'birth_date', 'gender', 'address', 'personal_id')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
        (_('Role'), {'fields': ('role',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone_number', 'address',
                'birth_date', 'gender', 'personal_id', 'role', 'avatar',
                'password1', 'password2',),}),
    )

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'specialization', 'license_uri')
    search_fields = ('user__name', 'specialization')
    list_filter = ('specialization',)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__name', 'user__email')


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__name', 'user__email')