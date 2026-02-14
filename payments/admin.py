from django.contrib import admin
from .models import Payment, WaveWebhook, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['transaction_id', 'wave_transaction_id']

@admin.register(WaveWebhook)
class WaveWebhookAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'is_verified', 'is_processed', 'created_at']
    list_filter = ['is_verified', 'is_processed']

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'amount', 'status', 'requested_at']
    list_filter = ['status']