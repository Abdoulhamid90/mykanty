from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import User, SellerProfile, SellerRequest
from .forms import (UserRegistrationForm, UserLoginForm, UserProfileForm,
                    SellerProfileForm, SellerRequestForm)
from orders.models import Order, OrderItem

try:
    from .emails import send_welcome_email, send_seller_request_submitted
except Exception:
    def send_welcome_email(*a, **k):
        pass
    def send_seller_request_submitted(*a, **k):
        pass


# ─────────────────────────────────────────
# INSCRIPTION
# ─────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                send_welcome_email(user)
            except Exception:
                pass
            messages.success(request, 'Compte créé avec succès ! Bienvenue sur My Kanty.')
            return redirect('accounts:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ─────────────────────────────────────────
# CONNEXION
# ─────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'accounts:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


# ─────────────────────────────────────────
# DÉCONNEXION
# ─────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('home')


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────
@login_required
def dashboard_view(request):
    user = request.user
    context = {'user': user}
    if user.is_seller:
        seller_orders = Order.objects.filter(
            items__seller=user
        ).distinct().order_by('-created_at')[:5]
        total_sales = OrderItem.objects.filter(
            seller=user
        ).aggregate(t=Sum('total_price'))['t'] or 0
        commission = float(total_sales) * 0.05
        net_earnings = float(total_sales) - commission
        context.update({
            'seller_orders': seller_orders,
            'total_sales': total_sales,
            'commission': commission,
            'net_earnings': net_earnings,
            'total_products': user.products.filter(is_active=True).count(),
        })
    else:
        my_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
        context['my_orders'] = my_orders
    return render(request, 'accounts/dashboard.html', context)


# ─────────────────────────────────────────
# PROFIL
# ─────────────────────────────────────────
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ─────────────────────────────────────────
# DEVENIR VENDEUR
# ─────────────────────────────────────────
def become_seller_view(request):
    form = SellerRequestForm()

    if request.user.is_authenticated:
        if request.user.is_seller:
            messages.info(request, 'Vous êtes déjà vendeur sur My Kanty !')
            return redirect('accounts:dashboard')

        existing = SellerRequest.objects.filter(
            user=request.user,
            status='pending'
        ).first()

        if existing:
            messages.info(
                request,
                "Votre demande est déjà en cours d'examen. Réponse sous 24-48h."
            )
            return redirect('accounts:dashboard')

        if request.method == 'POST':
            form = SellerRequestForm(request.POST, request.FILES)
            if form.is_valid():
                seller_request = form.save(commit=False)
                seller_request.user = request.user
                seller_request.save()
                try:
                    send_seller_request_submitted(seller_request)
                except Exception:
                    pass
                messages.success(
                    request,
                    'Votre demande a bien été envoyée ! Notre équipe vous répondra sous 24-48h.'
                )
                return redirect('accounts:dashboard')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
        else:
            initial = {
                'full_name': (
                    f"{request.user.first_name} {request.user.last_name}".strip()
                    or request.user.username
                ),
                'contact_number': getattr(request.user, 'phone_number', '') or '',
                'whatsapp_number': getattr(request.user, 'phone_number', '') or '',
                'location': getattr(request.user, 'city', '') or '',
            }
            form = SellerRequestForm(initial=initial)

    return render(request, 'accounts/become_seller.html', {'form': form})


# ─────────────────────────────────────────
# PROFIL PUBLIC VENDEUR
# ─────────────────────────────────────────
def seller_public_profile_view(request, username):
    seller = get_object_or_404(User, username=username, is_seller=True)
    products = seller.products.filter(is_active=True).order_by('-created_at')
    return render(request, 'accounts/seller_profile.html', {
        'seller': seller,
        'products': products,
    })


# ─────────────────────────────────────────
# RAPPORT VENDEUR
# ─────────────────────────────────────────
@login_required
def seller_reports_view(request):
    if not request.user.is_seller:
        messages.error(request, 'Accès réservé aux vendeurs.')
        return redirect('accounts:dashboard')

    user = request.user
    all_orders = Order.objects.filter(items__seller=user).distinct()
    released_orders = all_orders.filter(is_payment_released=True)
    pending_orders = all_orders.filter(
        is_payment_verified=True,
        is_payment_released=False
    )

    total_sales = OrderItem.objects.filter(
        seller=user
    ).aggregate(t=Sum('total_price'))['t'] or 0

    total_commission = float(total_sales) * 0.05
    net_earnings = float(total_sales) - total_commission

    top_products_qs = OrderItem.objects.filter(
        seller=user
    ).values('product_name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-revenue')[:10]

    top_products = []
    for p in top_products_qs:
        commission = float(p['revenue']) * 0.05
        top_products.append({
            'name': p['product_name'],
            'qty': p['qty'],
            'revenue': p['revenue'],
            'commission': commission,
            'net': float(p['revenue']) - commission,
        })

    stats = {
        'total_orders': all_orders.count(),
        'completed_orders': released_orders.count(),
        'total_sales': total_sales,
        'total_commission': total_commission,
        'net_earnings': net_earnings,
    }

    return render(request, 'accounts/seller_reports.html', {
        'stats': stats,
        'released_orders': released_orders,
        'pending_orders': pending_orders,
        'top_products': top_products,
    })