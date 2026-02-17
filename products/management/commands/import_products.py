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
        self.stdout.write("🚀 Début de l'import...")
        
        try:
            admin_user = User.objects.get(username='Abdoul-Hamid')
        except User.DoesNotExist:
            self.stdout.write("❌ Utilisateur admin non trouvé")
            return
        
        products_created = 0
        csv_file = 'produits_mykanty.csv'
        
        if not os.path.exists(csv_file):
            self.stdout.write(f"❌ Fichier {csv_file} non trouvé")
            return
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    category_slug = CATEGORY_MAPPING.get(row['category'])
                    if not category_slug:
                        continue
                    
                    category, _ = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'name': row['category'], 'is_active': True}
                    )
                    
                    product, created = Product.objects.update_or_create(
                        name=row['name'],
                        seller=admin_user,
                        defaults={
                            'description': row['description'],
                            'price': float(row['price']),
                            'category': category,
                            'stock_quantity': int(row['stock']),
                            'is_active': True,
			    'sku': f"SKU-{row['name'][:20].upper().replace(' ', '-')}-{products_created}",
                        }
                    )
                    
                    if created:
                        products_created += 1
                        self.stdout.write(f"✅ {row['name'][:40]}...")
                
                except Exception as e:
                    self.stdout.write(f"❌ Erreur: {str(e)}")
        
        self.stdout.write(f"\n✅ {products_created} produits créés!")