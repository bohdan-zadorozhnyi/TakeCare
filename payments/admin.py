from django.contrib import admin
from .models import Payment, SpecializationPrice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'price_display', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('appointment__id', 'stripe_payment_intent_id')

    def price_display(self, obj):
        return f"{obj.price / 100:.2f}{obj.currency}"
    price_display.short_description = 'Amount to Pay'

@admin.register(SpecializationPrice)
class SpecializationPriceAdmin(admin.ModelAdmin):
    list_display = ('specialization', 'get_price_pln', 'price')
    list_editable = ('price',)  # 'price' is a real model field
    readonly_fields = ('get_price_pln',)

    def get_price_pln(self, obj):
        return f"{obj.price / 100:.2f} PLN"
    get_price_pln.short_description = 'Price (PLN)'