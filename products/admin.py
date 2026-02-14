from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category']
    search_fields = ['name', 'seller__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'is_featured']

    fieldsets = (
        ('Informations produit', {
            'fields': ('seller', 'category', 'name', 'description', 'sku')
        }),
        ('Prix & Stock', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Image', {
            'fields': ('main_image',)
        }),
        ('Statut', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )