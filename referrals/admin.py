from django.contrib import admin
from .models import Referral, ReferralDetails

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('patient', 'specialist_type', 'issue_date', 'expiration_date')
    list_filter = ('specialist_type', 'issue_date', 'expiration_date')
    search_fields = ('patient__name',)
    ordering = ('-issue_date',)

@admin.register(ReferralDetails)
class ReferralDetailsAdmin(admin.ModelAdmin):
    list_display = ('referral', 'diagnosis', 'priority')
    list_filter = ('priority',)
    search_fields = ('diagnosis', 'referral__patient__name')