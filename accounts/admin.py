from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.utils.translation import gettext_lazy as _
from .forms import SignUpForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = SignUpForm
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