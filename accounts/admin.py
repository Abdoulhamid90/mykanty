from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SellerProfile, SellerRequest
from .emails import send_seller_approved
from django.utils import timezone

class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_seller', 'is_staff']
    list_filter = ['is_seller', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('phone_number', 'address', 'city', 'country', 'profile_picture', 'is_seller')}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'rating', 'total_sales']
    search_fields = ['user__username', 'business_name']

@admin.register(SellerRequest)
class SellerRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'status', 'contact_number', 'submitted_at']
    list_filter = ['status', 'preferred_payment_method', 'submitted_at']
    search_fields = ['full_name', 'user__username', 'contact_number', 'whatsapp_number']
    readonly_fields = ['submitted_at']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'full_name', 'contact_number', 'whatsapp_number', 'location')
        }),
        ('Informations business', {
            'fields': ('preferred_payment_method', 'product_types', 'business_description', 'id_document')
        }),
        ('Statut de la demande', {
            'fields': ('status', 'admin_notes', 'submitted_at', 'reviewed_at', 'reviewed_by')
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        for seller_request in queryset.filter(status='pending'):
            # Activer le statut vendeur
            seller_request.user.is_seller = True
            seller_request.user.save()
            
            # Créer le profil vendeur
            SellerProfile.objects.get_or_create(
                user=seller_request.user,
                defaults={
                    'business_name': f"Boutique de {seller_request.full_name}",
                    'business_description': seller_request.business_description
                }
            )
            
            # Mettre à jour la demande
            seller_request.status = 'approved'
            seller_request.reviewed_at = timezone.now()
            seller_request.reviewed_by = request.user
            seller_request.save()
            
            # Envoyer email d'approbation
            send_seller_approved(seller_request)
        
        self.message_user(request, f"{queryset.count()} demande(s) approuvée(s)")
    approve_requests.short_description = "✅ Approuver les demandes sélectionnées"
    
    def reject_requests(self, request, queryset):
        queryset.update(status='rejected', reviewed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} demande(s) rejetée(s)")
    reject_requests.short_description = "❌ Rejeter les demandes sélectionnées"