from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from orders.models import Order, OrderItem
from accounts.models import User, SellerRequest
from django.contrib.auth.decorators import login_required
from django.http import Http404

def home_view(request):
    categories = Category.objects.filter(is_active=True).order_by('name')
    featured_products = Product.objects.filter(
        is_active=True
    ).select_related('seller', 'category').order_by('-created_at')[:12]

    return render(request, 'home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })


@login_required
def admin_dashboard_view(request):
    if request.user.username != 'admin':
        from django.http import Http404
        raise Http404
    """
    Dashboard admin avec statistiques complètes
    """
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

    # ── STATISTIQUES GÉNÉRALES ──
    stats = {
        # Utilisateurs
        'total_users': User.objects.count(),
        'new_users_30d': User.objects.filter(date_joined__gte=last_30_days).count(),
        'total_sellers': User.objects.filter(is_seller=True).count(),
        'total_buyers': User.objects.filter(is_seller=False).count(),

        # Produits
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'out_of_stock': Product.objects.filter(stock_quantity=0, is_active=True).count(),

        # Commandes
        'total_orders': Order.objects.count(),
        'orders_today': Order.objects.filter(created_at__date=today.date()).count(),
        'orders_7d': Order.objects.filter(created_at__gte=last_7_days).count(),
        'orders_30d': Order.objects.filter(created_at__gte=last_30_days).count(),

        # Escrow
        'awaiting_payment': Order.objects.filter(status='awaiting_payment').count(),
        'payment_to_verify': Order.objects.filter(
            is_payment_verified=False,
            payment_reference__gt=''
        ).count(),
        'in_preparation': Order.objects.filter(status='in_preparation').count(),
        'in_delivery': Order.objects.filter(status='in_delivery').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'disputes': Order.objects.filter(status='dispute').count(),
        'payment_to_release': Order.objects.filter(
            is_payment_verified=True,
            is_delivery_confirmed=True,
            is_payment_released=False
        ).count(),

        # Finances
        'total_revenue': Order.objects.filter(
            is_payment_verified=True
        ).aggregate(t=Sum('total'))['t'] or 0,

        'total_commission': Order.objects.filter(
            is_payment_verified=True
        ).aggregate(t=Sum('commission_amount'))['t'] or 0,

        'revenue_30d': Order.objects.filter(
            is_payment_verified=True,
            created_at__gte=last_30_days
        ).aggregate(t=Sum('total'))['t'] or 0,

        'commission_30d': Order.objects.filter(
            is_payment_verified=True,
            created_at__gte=last_30_days
        ).aggregate(t=Sum('commission_amount'))['t'] or 0,

        # Demandes vendeur
        'pending_seller_requests': SellerRequest.objects.filter(status='pending').count(),
    }

    # ── DERNIÈRES COMMANDES ──
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # ── COMMANDES URGENTES ──
    urgent_orders = Order.objects.filter(
        Q(is_payment_verified=False, payment_reference__gt='') |
        Q(is_payment_verified=True, is_delivery_confirmed=True, is_payment_released=False) |
        Q(status='dispute')
    ).order_by('-created_at')[:10]

    # ── DEMANDES VENDEUR EN ATTENTE ──
    pending_requests = SellerRequest.objects.filter(
        status='pending'
    ).select_related('user').order_by('-submitted_at')[:5]

    # ── TOP VENDEURS (corrigé) ──
    top_sellers = []
    sellers = User.objects.filter(is_seller=True)
    for seller in sellers:
        total_sales = OrderItem.objects.filter(
            seller=seller
        ).aggregate(t=Sum('total_price'))['t'] or 0
        total_orders = OrderItem.objects.filter(
            seller=seller
        ).values('order').distinct().count()
        top_sellers.append({
            'username': seller.username,
            'total_sales': total_sales,
            'total_orders': total_orders,
        })
    top_sellers = sorted(top_sellers, key=lambda x: x['total_sales'], reverse=True)[:5]

    # ── TOP PRODUITS ──
    top_products = OrderItem.objects.values(
        'product_name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:5]

    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'urgent_orders': urgent_orders,
        'pending_requests': pending_requests,
        'top_sellers': top_sellers,
        'top_products': top_products,
    }

    return render(request, 'admin_dashboard.html', context)
    """
Ajoutez cette vue dans marketplace/views.py
Elle relaie les messages au chatbot Claude de façon sécurisée
"""

import json
import urllib.request
import urllib.error
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decouple import config

SYSTEM_PROMPT = """Tu es Kanty, l'assistant officiel de My Kanty — la marketplace de confiance au Togo 🇹🇬 et au Niger 🇳🇪.

MY KANTY EN BREF:
- Marketplace avec système Escrow sécurisé
- Commission de seulement 3% par vente
- Paiements: Mixx/Tmoney et Nita
- 2 pays: Togo et Niger
- Fondateur: Abdoul-Hamid Mohamed

CONTACTS:
- Togo: +228 93 33 78 02
- Niger: +227 92 53 44 35
- WhatsApp: +228 93 33 78 02
- Email: contact@mykanty.com
- Horaires: Lun-Sam 8h-18h

PAIEMENTS:
- Togo: Mixx/Tmoney → +228 72 22 23 72 | Nita → +228 72 22 23 72
- Niger: Mobile Money → +227 92 53 44 35 | Nita → +227 92 53 44 35

PAGES IMPORTANTES:
- Devenir vendeur: /accounts/become-seller/
- Mes commandes: /orders/my-orders/
- Guide Escrow: /legal/escrow-guide/
- CGV: /legal/cgv/
- Panier: /orders/cart/

ESCROW (système de paiement sécurisé):
1. Acheteur paie My Kanty
2. My Kanty vérifie le paiement (24-48h)
3. Vendeur prépare et expédie
4. Acheteur confirme réception
5. My Kanty libère le paiement au vendeur (moins 3%)

STYLE:
- Réponds en français
- Sois chaleureux, professionnel et concis
- Utilise des émojis modérément
- Réponds en maximum 3-4 phrases courtes
- Si tu ne sais pas, oriente vers le support: +228 93 33 78 02"""

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from anthropic import Anthropic
from django.conf import settings
from faq.models import FAQ
from difflib import SequenceMatcher
import re

def find_best_faq_match(user_message):
    """
    Trouve la meilleure FAQ correspondant au message de l'utilisateur
    """
    user_message_lower = user_message.lower().strip()
    
    # Récupérer toutes les FAQ actives
    all_faqs = FAQ.objects.filter(is_active=True).select_related('category')
    
    best_match = None
    best_score = 0.0
    
    for faq in all_faqs:
        # Comparer avec la question
        question_score = SequenceMatcher(
            None, 
            user_message_lower, 
            faq.question.lower()
        ).ratio()
        
        # Comparer avec les mots-clés
        keywords_score = 0.0
        if faq.keywords:
            keywords = [k.strip().lower() for k in faq.keywords.split(',')]
            matching_keywords = sum(1 for k in keywords if k in user_message_lower)
            keywords_score = matching_keywords / len(keywords) if keywords else 0
        
        # Score final (pondéré)
        final_score = (question_score * 0.7) + (keywords_score * 0.3)
        
        if final_score > best_score:
            best_score = final_score
            best_match = faq
    
    # Retourner seulement si le score est assez élevé (>= 30%)
    if best_score >= 0.3:
        return best_match, best_score
    
    return None, 0.0


def build_faq_context():
    """
    Construit le contexte FAQ pour Claude
    """
    faqs = FAQ.objects.filter(is_active=True).select_related('category').order_by('category__order', 'order')
    
    faq_text = "BASE DE CONNAISSANCE MY KANTY (FAQ) :\n\n"
    
    current_category = None
    for faq in faqs:
        if faq.category != current_category:
            current_category = faq.category
            faq_text += f"\n{'='*60}\n"
            faq_text += f"CATÉGORIE : {faq.category.display_name.upper()}\n"
            faq_text += f"{'='*60}\n\n"
        
        faq_text += f"Q: {faq.question}\n"
        faq_text += f"R: {faq.answer}\n\n"
    
    return faq_text


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({
                'error': 'Message requis'
            }, status=400)
        
        # 1. D'abord, essayer de trouver une FAQ correspondante
        matched_faq, match_score = find_best_faq_match(user_message)
        
        # 2. Construire le contexte FAQ
        faq_context = build_faq_context()
        
        # 3. Construire le prompt système
        system_prompt = f"""Tu es l'assistant virtuel de My Kanty, la marketplace n°1 au Togo et au Niger.

INFORMATIONS MY KANTY :
- Site web : https://mykanty-production.up.railway.app
- Pays : Togo 🇹🇬 et Niger 🇳🇪
- Contact Togo : +228 93 33 78 02
- Contact Niger : +227 92 53 44 35
- Email : contact@mykanty.com

MY KANTY PROPOSE :
1. 🛒 MARKETPLACE PRODUITS
   - 50+ produits dans 18 catégories
   - Paiement sécurisé Escrow 3%
   - Livraison Togo & Niger
   - URL : /products/

2. 👔 MARKETPLACE SERVICES
   - Experts vérifiés (plombiers, électriciens, développeurs, etc.)
   - 8 catégories professionnelles
   - Abonnements : 5000, 15000, 30000 XOF/mois
   - URL : /services/

{faq_context}

INSTRUCTIONS :
- Réponds UNIQUEMENT en te basant sur la FAQ ci-dessus
- Si la réponse est dans la FAQ, utilise-la EXACTEMENT
- Si la question n'est PAS dans la FAQ, dis : "Je n'ai pas cette information dans ma base de données. Contactez notre support : 🇹🇬 +228 93 33 78 02 ou 🇳🇪 +227 92 53 44 35"
- Sois concis, clair et amical
- Utilise des emojis pour rendre la conversation agréable
- Formate avec des sauts de ligne pour la lisibilité
- Si on te demande un lien, donne l'URL complète
"""
        
        # 4. Si match FAQ fort (>60%), répondre directement
        if matched_faq and match_score > 0.6:
            # Incrémenter les stats
            matched_faq.increment_views()
            
            response_text = f"📚 {matched_faq.category.display_name}\n\n"
            response_text += f"❓ {matched_faq.question}\n\n"
            response_text += f"✅ {matched_faq.answer}\n\n"
            response_text += "---\n💡 Autre question ? Je suis là pour vous aider !"
            
            return JsonResponse({
                'response': response_text,
                'matched_faq': True,
                'faq_id': matched_faq.id,
                'confidence': round(match_score * 100, 1)
            })
        
        # 5. Sinon, utiliser Claude avec le contexte FAQ
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_message
            }]
        )
        
        bot_response = message.content[0].text
        
        # Log la conversation (optionnel)
        # ChatbotLog.objects.create(
        #     user_message=user_message,
        #     bot_response=bot_response,
        #     matched_faq=matched_faq
        # )
        
        return JsonResponse({
            'response': bot_response,
            'matched_faq': False,
            'suggested_faq': matched_faq.id if matched_faq else None
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Erreur: {str(e)}'
        }, status=500)
