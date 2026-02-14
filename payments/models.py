from django.db import models
from orders.models import Order
from accounts.models import User
import uuid

class Payment(models.Model):
    """
    Modèle pour gérer les paiements
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('wave', 'Wave'),
        # Possibilité d'ajouter d'autres moyens plus tard
        # ('mtn_money', 'MTN Mobile Money'),
        # ('moov_money', 'Moov Money'),
    ]

    # Identifiants
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    
    # Relations
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    # Informations de paiement
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='wave')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')  # Franc CFA
    
    # Informations Wave
    wave_transaction_id = models.CharField(max_length=200, blank=True)
    wave_payment_url = models.URLField(blank=True)  # URL de paiement Wave
    wave_phone_number = models.CharField(max_length=20, blank=True)
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)  # Données supplémentaires
    error_message = models.TextField(blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Générer un ID de transaction unique
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement {self.transaction_id} - {self.get_status_display()}"

    def is_successful(self):
        """Vérifie si le paiement est réussi"""
        return self.status == 'completed'

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-created_at']


class WaveWebhook(models.Model):
    """
    Stockage des webhooks Wave pour traçabilité
    """
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='webhooks')
    
    # Données du webhook
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    # Sécurité
    signature = models.CharField(max_length=500, blank=True)
    is_verified = models.BooleanField(default=False)
    
    # État de traitement
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook {self.event_type} - {self.created_at}"

    class Meta:
        verbose_name = 'Webhook Wave'
        verbose_name_plural = 'Webhooks Wave'
        ordering = ['-created_at']


class Refund(models.Model):
    """
    Modèle pour gérer les remboursements
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
    ]

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    
    # Montant
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    # État
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Informations du remboursement
    refund_transaction_id = models.CharField(max_length=200, blank=True)
    
    # Dates
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Remboursement {self.amount} XOF - Commande {self.order.order_number}"

    class Meta:
        verbose_name = 'Remboursement'
        verbose_name_plural = 'Remboursements'
        ordering = ['-requested_at']
