"""
MODELS POUR MY KANTY SERVICES
Créez ce fichier : services/models.py
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from datetime import datetime, timedelta

User = get_user_model()

class ServiceCategory(models.Model):
    """Catégories de services"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='fas fa-briefcase')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Catégorie de service"
        verbose_name_plural = "Catégories de services"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class SubscriptionPlan(models.Model):
    """Plans d'abonnement pour experts"""
    BASIC = 'basic'
    PRO = 'pro'
    PREMIUM = 'premium'
    
    PLAN_CHOICES = [
        (BASIC, 'Basic'),
        (PRO, 'Pro'),
        (PREMIUM, 'Premium'),
    ]
    
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # en XOF
    max_requests_per_month = models.IntegerField(help_text="Nombre de demandes max par mois")
    features = models.JSONField(default=list, help_text="Liste des fonctionnalités")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.display_name} - {self.price} XOF/mois"


class Expert(models.Model):
    """Profil d'expert/prestataire de services"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='expert_profile')
    
    # Informations de base
    business_name = models.CharField(max_length=200, help_text="Nom commercial ou raison sociale")
    slug = models.SlugField(unique=True, blank=True)
    bio = models.TextField(help_text="Présentation professionnelle")
    avatar = models.ImageField(upload_to='experts/avatars/', blank=True, null=True)
    
    # Catégories et compétences
    categories = models.ManyToManyField(ServiceCategory, related_name='experts')
    skills = models.TextField(help_text="Compétences séparées par des virgules")
    
    # Localisation
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=50, choices=[('TG', 'Togo'), ('NE', 'Niger')])
    address = models.CharField(max_length=255, blank=True)
    service_zone = models.CharField(max_length=255, help_text="Zones d'intervention")
    
    # Contact
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Tarification
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_description = models.CharField(max_length=255, blank=True, help_text="Ex: À partir de 10000 XOF")
    
    # Expérience
    years_experience = models.IntegerField(default=0)
    certifications = models.TextField(blank=True, help_text="Diplômes et certifications")
    
    # Abonnement
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)
    requests_this_month = models.IntegerField(default=0)
    
    # Badges
    is_verified = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)
    fast_responder = models.BooleanField(default=False)
    
    # Statistiques
    total_requests = models.IntegerField(default=0)
    completed_services = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.IntegerField(default=0)
    response_rate = models.IntegerField(default=0, help_text="Pourcentage de réponses")
    
    # Disponibilité
    is_available = models.BooleanField(default=True)
    availability_note = models.CharField(max_length=255, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Expert"
        verbose_name_plural = "Experts"
        ordering = ['-is_verified', '-is_top_rated', '-average_rating', '-created_at']
    
    def __str__(self):
        return self.business_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
        super().save(*args, **kwargs)
    
    @property
    def is_subscribed(self):
        """Vérifie si l'abonnement est actif"""
        if not self.subscription_end:
            return False
        return datetime.now() <= self.subscription_end
    
    @property
    def can_receive_requests(self):
        """Vérifie si l'expert peut recevoir des demandes"""
        if not self.is_subscribed:
            return False
        if self.subscription_plan.max_requests_per_month == -1:  # Illimité
            return True
        return self.requests_this_month < self.subscription_plan.max_requests_per_month
    
    def get_badges(self):
        """Retourne la liste des badges de l'expert"""
        badges = []
        if self.is_verified:
            badges.append({'name': 'Expert Vérifié', 'icon': 'fa-check-circle', 'color': 'green'})
        if self.is_top_rated:
            badges.append({'name': 'Top Rated', 'icon': 'fa-star', 'color': 'gold'})
        if self.fast_responder:
            badges.append({'name': 'Réponse Rapide', 'icon': 'fa-bolt', 'color': 'orange'})
        return badges


class ServiceRequest(models.Model):
    """Demande de service d'un client à un expert"""
    PENDING = 'pending'
    CONTACTED = 'contacted'
    ACCEPTED = 'accepted'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'En attente'),
        (CONTACTED, 'Contacté'),
        (ACCEPTED, 'Accepté'),
        (IN_PROGRESS, 'En cours'),
        (COMPLETED, 'Terminé'),
        (CANCELLED, 'Annulé'),
    ]
    
    # Acteurs
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='received_requests')
    
    # Détails de la demande
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255)
    preferred_date = models.DateField(null=True, blank=True)
    
    # Contact client
    client_name = models.CharField(max_length=100)
    client_phone = models.CharField(max_length=20)
    client_email = models.EmailField()
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    expert_response = models.TextField(blank=True)
    expert_quote = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Demande de service"
        verbose_name_plural = "Demandes de services"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.client_name} → {self.expert.business_name}"


class Review(models.Model):
    """Avis client sur un expert"""
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    service_request = models.OneToOneField(ServiceRequest, on_delete=models.CASCADE, null=True, blank=True)
    
    rating = models.IntegerField(choices=[(i, f"{i} étoiles") for i in range(1, 6)])
    comment = models.TextField()
    
    # Critères détaillés
    professionalism = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    quality = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    punctuality = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    value_for_money = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    
    is_verified = models.BooleanField(default=False, help_text="Avis vérifié (service réellement effectué)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating}★ - {self.expert.business_name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la moyenne de l'expert
        expert = self.expert
        reviews = expert.reviews.all()
        expert.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
        expert.total_reviews = reviews.count()
        expert.save()


class Subscription(models.Model):
    """Historique des abonnements"""
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Paiement
    payment_method = models.CharField(max_length=50, default='Mobile Money')
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_verified = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.expert.business_name} - {self.plan.display_name}"
