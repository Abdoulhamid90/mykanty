from django.db import models
from accounts.models import User
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, default='')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='tag', help_text="Nom icône Font Awesome (ex: laptop, tshirt)")
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']


class Product(models.Model):
    """
    Modèle principal pour les produits
    """
    CONDITION_CHOICES = [
        ('new', 'Neuf'),
        ('used', 'Occasion'),
        ('refurbished', 'Reconditionné'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    
    # Informations de base
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    
    # Prix et stock
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    
    # Images
    main_image = models.ImageField(upload_to='products/')
    
    # Informations supplémentaires
    brand = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, blank=True, unique=True)  # Référence produit
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Poids en kg")
    
    # Statistiques
    views_count = models.IntegerField(default=0)
    sales_count = models.IntegerField(default=0)
    
    # États
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # Produit mis en avant
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_price(self):
        """Retourne le prix effectif (avec promo si existe)"""
        return self.discount_price if self.discount_price else self.price

    def get_discount_percentage(self):
        """Calcule le pourcentage de réduction"""
        if self.discount_price and self.price > self.discount_price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    def is_in_stock(self):
        """Vérifie si le produit est en stock"""
        return self.stock_quantity > 0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']


class ProductImage(models.Model):
    """
    Images supplémentaires pour un produit
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image de {self.product.name}"

    class Meta:
        verbose_name = 'Image Produit'
        verbose_name_plural = 'Images Produits'


class Review(models.Model):
    """
    Avis clients sur les produits
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    guest_name = models.CharField(max_length=200, blank=True)  # Pour les non-inscrits
    guest_email = models.EmailField(blank=True)
    
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 à 5 étoiles
    comment = models.TextField()
    
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)  # Modération
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        reviewer = self.user.username if self.user else self.guest_name
        return f"Avis de {reviewer} sur {self.product.name}"

    class Meta:
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
        ordering = ['-created_at']
