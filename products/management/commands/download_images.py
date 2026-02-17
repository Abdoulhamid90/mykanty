"""
COMMANDE DJANGO - VERSION CORRIGÉE POUR WINDOWS
Remplacez le contenu de : products/management/commands/download_images.py
"""

import os
import urllib.request
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from products.models import Product

# Mapping COMPLET des 50 produits
PRODUCT_IMAGES = {
    'Samsung Galaxy A14 128GB': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
    'iPhone 13 Pro 256GB Reconditionné': 'https://images.unsplash.com/photo-1632661674596-df8be070a5c5?w=800&q=80',
    'Ordinateur Portable HP 15': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
    'Télévision LED 43 pouces': 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800&q=80',
    'Casque Audio Bluetooth JBL': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
    'Enceinte Bluetooth Portable': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80',
    'Ventilateur Solaire 16 pouces': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80',
    'Kit Panneau Solaire 300W': 'https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800&q=80',
    'Power Bank Solaire 50000mAh': 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=800&q=80',
    'Batterie Solaire 200Ah': 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&q=80',
    'Lampe Solaire LED Jardin': 'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800&q=80',
    'Chargeur Solaire USB 21W': 'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&q=80',
    'Tissu Wax Hollandais 6 yards': 'https://images.unsplash.com/photo-1618220179428-22790b461013?w=800&q=80',
    'Boubou Homme Brodé': 'https://images.unsplash.com/photo-1622290291468-a28f7a7dc6a8?w=800&q=80',
    'Robe Ankara Femme Élégante': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&q=80',
    'Ensemble Kente Enfant': 'https://images.unsplash.com/photo-1519689680058-324335c77eba?w=800&q=80',
    'Gari Blanc 5kg': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&q=80',
    'Mil Complet 10kg': 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=800&q=80',
    "Pâte d'Arachide Naturelle 1kg": 'https://images.unsplash.com/photo-1551106652-a5bcf4b29e84?w=800&q=80',
    'Épices Mélange Togolais 500g': 'https://images.unsplash.com/photo-1596040033229-a0b8b5b9ce66?w=800&q=80',
    'Huile de Palme Rouge 5L': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&q=80',
    'Coffret Thé Tisanes Bio 24pc': 'https://images.unsplash.com/photo-1594631252845-29fc4cc8cde9?w=800&q=80',
    'Fauteuil en Rotin Tressé': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&q=80',
    "Table Basse Bois d'Iroko": 'https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=800&q=80',
    'Panier de Rangement Paille': 'https://images.unsplash.com/photo-1595515106969-1ce29566ff1c?w=800&q=80',
    'Lampe Suspension Calebasse': 'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800&q=80',
    'Set de 6 Assiettes Céramique': 'https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=800&q=80',
    'Mixeur Blender 1000W': 'https://images.unsplash.com/photo-1585515320310-259814833e62?w=800&q=80',
    'Fer à Repasser Vapeur': 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=800&q=80',
    'Matelas Mousse 140x190cm': 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&q=80',
    'Rideau Occultant Thermique': 'https://images.unsplash.com/photo-1616486029423-aaa4789e8c9a?w=800&q=80',
    'Machine à Coudre Portable': 'https://images.unsplash.com/photo-1597120236276-1e870a94700f?w=800&q=80',
    'Beurre de Karité Pur 500g': 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800&q=80',
    'Savon Noir Africain 1kg': 'https://images.unsplash.com/photo-1600428994540-70d501e9ae08?w=800&q=80',
    'Huile de Coco Vierge 500ml': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=800&q=80',
    'Pommade Croissance Cheveux': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=800&q=80',
    'Gommage Corps Café & Karité': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=80',
    'Statue Masque Africain 50cm': 'https://images.unsplash.com/photo-1582738411706-bfc8e691d1c2?w=800&q=80',
    'Djembé Artisanal Authentique': 'https://images.unsplash.com/photo-1519892300165-cb5542fb47c7?w=800&q=80',
    'Tableau Peinture Batik 60x80': 'https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=800&q=80',
    'Collier Perles Africaines': 'https://images.unsplash.com/photo-1599643477877-530eb83abc8e?w=800&q=80',
    'Sac à Main Bogolan': 'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=800&q=80',
    'Poussette Bébé 3 Roues': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&q=80',
    'Lit Bébé en Bois Massif': 'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=800&q=80',
    'Couches Bébé Taille 4 (96pc)': 'https://images.unsplash.com/photo-1519689373023-dd07c7988603?w=800&q=80',
    'Chaise Haute Bébé Évolutive': 'https://images.unsplash.com/photo-1598928636135-d146006ff4be?w=800&q=80',
    'Jouets Éducatifs Bois Set': 'https://images.unsplash.com/photo-1558060370-d644479cb6f7?w=800&q=80',
    'Sac École Enfant Solide': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80',
    'Chaussures Sport Enfant': 'https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=800&q=80',
    'Biberons Anti-Coliques Set 3': 'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=800&q=80',
}

class Command(BaseCommand):
    help = 'Télécharge et associe des images aux produits'

    def handle(self, *args, **kwargs):
        self.stdout.write("📸 Début du téléchargement...")
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for product_name, image_url in PRODUCT_IMAGES.items():
            try:
                # Chercher le produit
                product = Product.objects.filter(name__icontains=product_name[:30]).first()
                
                if not product:
                    error_count += 1
                    continue
                
                # Vérifier si image existe déjà
                if product.main_image:
                    skipped_count += 1
                    continue
                
                self.stdout.write(f"📥 {product_name[:35]}...")
                
                # Télécharger directement en mémoire (pas de fichier temporaire)
                req = urllib.request.Request(
                    image_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_data = response.read()
                
                # Sauvegarder avec ContentFile (pas de fichier temporaire)
                img_name = f"{product.slug}.jpg"
                product.main_image.save(img_name, ContentFile(image_data), save=True)
                
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ {product_name[:35]}..."))
                
                # Petit délai pour éviter rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"❌ {str(e)[:50]}"))
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ Nouvelles images: {success_count}"))
        self.stdout.write(f"⏭️  Déjà présentes: {skipped_count}")
        self.stdout.write(f"❌ Erreurs: {error_count}")
        self.stdout.write(self.style.SUCCESS(f"📦 Total: {success_count + skipped_count}/50"))
        self.stdout.write("="*60)