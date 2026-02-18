"""
MODÈLES FAQ POUR MY KANTY
Ajoutez ce code dans un nouveau fichier : faq/models.py
Ou ajoutez dans un fichier existant
"""

from django.db import models

class FAQCategory(models.Model):
    """Catégories de FAQ"""
    GENERAL = 'general'
    PRODUCTS = 'products'
    SERVICES = 'services'
    PAYMENT = 'payment'
    DELIVERY = 'delivery'
    ACCOUNT = 'account'
    
    CATEGORY_CHOICES = [
        (GENERAL, 'Questions Générales'),
        (PRODUCTS, 'Achat de Produits'),
        (SERVICES, 'Services & Experts'),
        (PAYMENT, 'Paiement & Escrow'),
        (DELIVERY, 'Livraison'),
        (ACCOUNT, 'Compte & Profil'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fa-question-circle')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Catégorie FAQ"
        verbose_name_plural = "Catégories FAQ"
    
    def __str__(self):
        return self.display_name


class FAQ(models.Model):
    """Questions fréquemment posées"""
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.TextField(help_text="La question complète")
    answer = models.TextField(help_text="La réponse détaillée")
    keywords = models.TextField(
        blank=True,
        help_text="Mots-clés séparés par des virgules pour améliorer la recherche"
    )
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', '-helpful_count']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return f"{self.category.display_name}: {self.question[:50]}"
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def mark_helpful(self):
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])


class ChatbotLog(models.Model):
    """Log des conversations du chatbot pour amélioration"""
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    user_message = models.TextField()
    bot_response = models.TextField()
    matched_faq = models.ForeignKey(FAQ, on_delete=models.SET_NULL, null=True, blank=True)
    was_helpful = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat {self.session_id[:8]} - {self.created_at}"