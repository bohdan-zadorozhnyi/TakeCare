from django.contrib import admin
from .models import Referral

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('patient', 'specialist_type', 'issue_date', 'expiration_date')
    list_filter = ('specialist_type', 'issue_date', 'expiration_date')
    search_fields = ('patient__name',)
    ordering = ('-issue_date',)