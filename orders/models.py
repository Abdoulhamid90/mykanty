from django.db import models
from accounts.models import User
from products.models import Product
import uuid

class Order(models.Model):
    """
    Commande avec système Escrow
    """
    STATUS_CHOICES = [
        ('awaiting_payment', 'En attente de paiement'),
        ('payment_received', 'Paiement reçu (Escrow)'),
        ('in_preparation', 'En préparation'),
        ('in_delivery', 'En livraison'),
        ('delivered', 'Livrée'),
        ('dispute', 'Litige'),
        ('cancelled', 'Annulée'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('nita', 'Nita (Transfert bancaire)'),
    ]
    
    # Identifiants
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Client
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_email = models.EmailField(blank=True)
    guest_name = models.CharField(max_length=200, blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    
    # Livraison
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100, default='Togo')
    
    # Prix
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Commission My Kanty (5%)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Commission en pourcentage")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Montant de la commission")
    seller_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Montant pour le vendeur (après commission)")
    
    # ESCROW - Paiement
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_reference = models.CharField(max_length=200, blank=True, help_text="Référence de transaction")
    payment_proof = models.FileField(upload_to='payment_proofs/', null=True, blank=True, help_text="Capture/reçu de paiement")
    
    # ESCROW - État du paiement
    is_payment_verified = models.BooleanField(default=False, help_text="Admin a vérifié le paiement")
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    payment_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    
    # ESCROW - État de livraison
    is_delivery_confirmed = models.BooleanField(default=False, help_text="Client a confirmé la réception")
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # ESCROW - Libération du paiement au vendeur
    is_payment_released = models.BooleanField(default=False, help_text="Argent libéré au vendeur")
    payment_released_at = models.DateTimeField(null=True, blank=True)
    payment_released_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_payments')
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting_payment')
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    dispute_reason = models.TextField(blank=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=200, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"MK-{uuid.uuid4().hex[:10].upper()}"
        
        # Calculer automatiquement la commission
        if self.total > 0:
            self.commission_amount = (self.total * self.commission_rate) / 100
            self.seller_amount = self.total - self.commission_amount
        
        super().save(*args, **kwargs)

    def get_customer_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username
        return self.guest_name

    def can_release_payment(self):
        """Vérifie si le paiement peut être libéré au vendeur"""
        return (
            self.is_payment_verified and 
            self.is_delivery_confirmed and 
            not self.is_payment_released and
            self.status == 'delivered'
        )

    def __str__(self):
        return f"Commande {self.order_number} - {self.get_status_display()}"

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']


class OrderItem(models.Model):
    """
    Articles d'une commande
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    
    # Informations figées au moment de l'achat
    product_name = models.CharField(max_length=300)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    
    # Vendeur
    seller = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    
    # Total
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculer le total automatiquement
        self.total_price = self.product_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    class Meta:
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'


class Cart(models.Model):
    """
    Panier d'achat (pour les sessions)
    """
    session_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Panier de {self.user.username if self.user else 'Invité'}"

    def get_total(self):
        """Calcule le total du panier"""
        return sum(item.get_subtotal() for item in self.items.all())

    def get_items_count(self):
        """Compte le nombre total d'articles"""
        return sum(item.quantity for item in self.items.all())

    class Meta:
        verbose_name = 'Panier'
        verbose_name_plural = 'Paniers'


class CartItem(models.Model):
    """
    Article dans le panier
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_subtotal(self):
        """Calcule le sous-total pour cet article"""
        return self.product.get_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    class Meta:
        verbose_name = 'Article du panier'
        verbose_name_plural = 'Articles du panier'
        unique_together = ['cart', 'product']