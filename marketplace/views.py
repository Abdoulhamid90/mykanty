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