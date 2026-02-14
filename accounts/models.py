from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé
    Étend le modèle User de Django avec des champs supplémentaires
    """
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Togo')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_seller = models.BooleanField(default=False)  # Peut vendre des produits
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.email}"

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']


class SellerProfile(models.Model):
    """
    Profil vendeur avec informations supplémentaires
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200)
    business_description = models.TextField(blank=True)
    business_logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sales = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} - {self.user.username}"

    class Meta:
        verbose_name = 'Profil Vendeur'
        verbose_name_plural = 'Profils Vendeurs'

# AJOUTEZ à la fin du fichier accounts/models.py

class SellerRequest(models.Model):
    """
    Demande pour devenir vendeur - nécessite approbation admin
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('nita', 'Nita (Transfert bancaire)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    
    # Informations personnelles
    full_name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=20)
    location = models.CharField(max_length=200, help_text="Ville/Quartier")
    
    # Informations business
    preferred_payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    product_types = models.TextField(help_text="Types de produits que vous vendez")
    business_description = models.TextField()
    
    # Documents (optionnel)
    id_document = models.FileField(upload_to='seller_requests/documents/', null=True, blank=True)
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Notes de l'administrateur")
    
    # Dates
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    
    def __str__(self):
        return f"Demande de {self.full_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = 'Demande Vendeur'
        verbose_name_plural = 'Demandes Vendeurs'
        ordering = ['-submitted_at']