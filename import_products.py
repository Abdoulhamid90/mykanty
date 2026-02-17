"""
COMMANDE DJANGO POUR IMPORTER LES PRODUITS
Créez ce fichier dans : products/management/commands/import_products.py
"""

import csv
import os
from django.core.management.base import BaseCommand
from products.models import Product, Category
from accounts.models import User

CATEGORY_MAPPING = {
    'Téléphonie': 'telephonie',
    'Énergie Solaire': 'energie-solaire',
    'Mode & Vêtements': 'mode-vetements',
    'Bébé & Enfants': 'bebe-enfants',
    'Alimentation': 'alimentation',
    'Maison & Cuisine': 'maison-cuisine',
    'Beauté & Santé': 'beaute-sante',
    'Art & Artisanat': 'art-artisanat',
    'Électronique': 'electronique',
}

class Command(BaseCommand):
    help = 'Importe les produits depuis le fichier CSV'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Début de l'import des produits...")
        
        # Récupérer l'utilisateur admin
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write(self.style.SUCCESS(f"✅ Utilisateur admin trouvé: {admin_user.username}"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Erreur: L'utilisateur 'admin' n'existe pas."))
            self.stdout.write("   Créez d'abord un superuser avec: python manage.py createsuperuser")
            return
        
        products_created = 0
        products_updated = 0
        errors = 0
        
        csv_file = 'produits_mykanty.csv'
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"❌ Fichier {csv_file} non trouvé à la racine du projet."))
            return
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    category_name = row['category']
                    category_slug = CATEGORY_MAPPING.get(category_name)
                    
                    if not category_slug:
                        self.stdout.write(self.style.WARNING(f"⚠️  Catégorie inconnue: {category_name}"))
                        errors += 1
                        continue
                    
                    category = Category.objects.filter(slug=category_slug).first()
                    
                    if not category:
                        self.stdout.write(f"⚠️  Création catégorie: {category_name}")
                        category = Category.objects.create(
                            name=category_name,
                            slug=category_slug,
                            is_active=True
                        )
                    
                    product, created = Product.objects.update_or_create(
                        name=row['name'],
                        vendor=admin_user,
                        defaults={
                            'description': row['description'],
                            'price': float(row['price']),
                            'category': category,
                            'stock': int(row['stock']),
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        products_created += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ Créé: {row['name'][:50]}..."))
                    else:
                        products_updated += 1
                        self.stdout.write(f"🔄 Mis à jour: {row['name'][:50]}...")
                
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"❌ Erreur: {row.get('name', 'INCONNU')} - {str(e)}"))
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("📊 RÉSUMÉ DE L'IMPORT"))
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ Produits créés: {products_created}"))
        self.stdout.write(f"🔄 Produits mis à jour: {products_updated}")
        self.stdout.write(f"❌ Erreurs: {errors}")
        self.stdout.write(self.style.SUCCESS(f"📦 Total produits en base: {Product.objects.count()}"))
        self.stdout.write("="*60)