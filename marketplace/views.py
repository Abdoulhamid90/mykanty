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
from django.views.decorators.http import require_http_methods
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


@require_http_methods(["POST"])
@csrf_exempt
def chatbot_api_view(request):
    """
    Endpoint sécurisé pour le chatbot Claude.
    Relaie les messages entre le navigateur et l'API Anthropic.
    """
    try:
        # Parser le corps de la requête
        body = json.loads(request.body)
        messages = body.get('messages', [])

        if not messages:
            return JsonResponse({'error': 'Messages manquants'}, status=400)

        # Limiter l'historique à 10 messages pour économiser les tokens
        if len(messages) > 10:
            messages = messages[-10:]

        # Récupérer la clé API depuis les variables d'environnement
        api_key = config('ANTHROPIC_API_KEY', default='')

        if not api_key:
            return JsonResponse({
                'reply': "Le chatbot est temporairement indisponible. Contactez-nous au +228 93 33 78 02 🙏"
            })

        # Préparer la requête vers l'API Anthropic
        payload = json.dumps({
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 500,
            'system': SYSTEM_PROMPT,
            'messages': messages
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            method='POST'
        )

        # Appeler l'API Anthropic
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            reply = data['content'][0]['text']
            return JsonResponse({'reply': reply})

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        print(f"CHATBOT ERROR: {e.code} - {error_body}")
        return JsonResponse({
            'reply': "Désolé, je rencontre un problème. Contactez-nous au +228 93 33 78 02 📞"
        })
    except Exception as e:
        return JsonResponse({
            'reply': "Une erreur est survenue. Notre équipe est disponible au +228 93 33 78 02 🙏"
        })