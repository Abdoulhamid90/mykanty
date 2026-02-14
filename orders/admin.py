from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem
from django.utils import timezone

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_display', 'total', 'commission_display', 'seller_amount_display', 'payment_method', 'status', 'escrow_display', 'created_at']
    list_filter = ['status', 'payment_method', 'is_payment_verified', 'is_delivery_confirmed', 'is_payment_released']
    search_fields = ['order_number', 'user__username', 'guest_email', 'guest_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'commission_amount', 'seller_amount']
    
    fieldsets = (
        ('Informations commande', {
            'fields': ('order_number', 'user', 'guest_name', 'guest_email', 'guest_phone')
        }),
        ('Livraison', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_country', 'tracking_number')
        }),
        ('Prix', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
        ('Commission My Kanty (5%)', {
            'fields': ('commission_rate', 'commission_amount', 'seller_amount'),
        }),
        ('ESCROW - Paiement Client', {
            'fields': ('payment_method', 'payment_reference', 'payment_proof', 
                      'is_payment_verified', 'payment_verified_at', 'payment_verified_by'),
        }),
        ('ESCROW - Livraison', {
            'fields': ('is_delivery_confirmed', 'delivery_confirmed_at'),
        }),
        ('ESCROW - Paiement Vendeur', {
            'fields': ('is_payment_released', 'payment_released_at', 'payment_released_by'),
        }),
        ('Statut et Notes', {
            'fields': ('status', 'customer_notes', 'admin_notes', 'dispute_reason')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    actions = ['verify_payment', 'mark_in_preparation', 'mark_in_delivery', 'mark_delivered', 'release_payment']
    
    def customer_display(self, obj):
        return obj.get_customer_name()
    customer_display.short_description = 'Client'
    
    def commission_display(self, obj):
        return f"{obj.commission_amount} XOF ({obj.commission_rate}%)"
    commission_display.short_description = 'Commission My Kanty'
    
    def seller_amount_display(self, obj):
        return f"{obj.seller_amount} XOF"
    seller_amount_display.short_description = 'Montant Vendeur'
    
    def escrow_display(self, obj):
        status = []
        if obj.is_payment_verified:
            status.append('Paiement OK')
        if obj.is_delivery_confirmed:
            status.append('Livré')
        if obj.is_payment_released:
            status.append('Vendeur payé')
        return ' | '.join(status) if status else 'En attente'
    escrow_display.short_description = 'État Escrow'
    
    def verify_payment(self, request, queryset):
        updated = queryset.filter(is_payment_verified=False).update(
            is_payment_verified=True,
            payment_verified_at=timezone.now(),
            payment_verified_by=request.user,
            status='payment_received'
        )
        self.message_user(request, f"{updated} paiement(s) vérifié(s)")
    verify_payment.short_description = "Vérifier le paiement (Escrow)"
    
    def mark_in_preparation(self, request, queryset):
        queryset.update(status='in_preparation')
        self.message_user(request, "Commande(s) en préparation")
    mark_in_preparation.short_description = "Marquer en préparation"
    
    def mark_in_delivery(self, request, queryset):
        queryset.update(status='in_delivery')
        self.message_user(request, "Commande(s) en livraison")
    mark_in_delivery.short_description = "Marquer en livraison"
    
    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, "Commande(s) livrée(s)")
    mark_delivered.short_description = "Marquer comme livrée"
    
    def release_payment(self, request, queryset):
        eligible = queryset.filter(
            is_payment_verified=True,
            is_delivery_confirmed=True,
            is_payment_released=False
        )
        updated = eligible.update(
            is_payment_released=True,
            payment_released_at=timezone.now(),
            payment_released_by=request.user
        )
        self.message_user(request, f"Paiement libéré pour {updated} commande(s)")
    release_payment.short_description = "Libérer paiement au vendeur"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'total_price', 'seller']
    list_filter = ['seller']
    search_fields = ['product_name', 'order__order_number']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'created_at']
    search_fields = ['user__username', 'session_key']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'added_at']
    list_filter = ['added_at']