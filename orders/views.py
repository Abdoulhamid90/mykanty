from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
from .models import Order, OrderItem
from products.models import Product
from accounts.emails import send_order_confirmation, send_delivery_confirmed_to_seller

def cart_view(request):
    """
    Vue du panier d'achat
    """
    return render(request, 'orders/cart.html')

def checkout_view(request):
    """
    Vue de la page de checkout
    """
    return render(request, 'orders/checkout.html')

def payment_view(request):
    """
    Page de paiement avec instructions Escrow
    """
    return render(request, 'orders/payment.html')

@require_POST
def confirm_payment_view(request):
    """
    Traite la confirmation de paiement avec preuve
    """
    try:
        # Récupérer les données
        order_data = json.loads(request.POST.get('order_data'))
        payment_reference = request.POST.get('payment_reference')
        payment_proof = request.FILES.get('payment_proof')
        
        customer = order_data['customer']
        items = order_data['items']
        payment_method = order_data['payment_method']
        
        # Créer la commande
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_name=customer['name'],
            guest_email=customer['email'],
            guest_phone=customer['phone'],
            shipping_address=customer['address'],
            shipping_city=customer['city'],
            subtotal=order_data['subtotal'],
            shipping_cost=order_data['shipping'],
            total=order_data['total'],
            payment_method=payment_method,
            payment_reference=payment_reference,
            payment_proof=payment_proof,
            customer_notes=order_data.get('notes', ''),
            status='awaiting_payment'
        )
        
        # Ajouter les articles
        for item in items:
            try:
                product = Product.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_price=product.get_price(),
                    quantity=item['quantity'],
                    seller=product.seller
                )
            except Product.DoesNotExist:
                pass
        
        # Envoyer email de confirmation
        send_order_confirmation(order)
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'message': 'Commande créée avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def order_success_view(request, order_number):
    """
    Page de succès après commande
    """
    return render(request, 'orders/success.html', {
        'order_number': order_number
    })

@login_required
def my_orders_view(request):
    """
    Liste des commandes de l'utilisateur connecté
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def order_detail_view(request, order_number):
    """
    Détail d'une commande
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def confirm_delivery_view(request, order_number):
    """
    Confirmation de réception par l'acheteur
    """
    if request.method == 'POST':
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        # Vérifier que la commande est livrée
        if order.status == 'delivered' and not order.is_delivery_confirmed:
            order.is_delivery_confirmed = True
            order.delivery_confirmed_at = timezone.now()
            order.save()
            
            # Envoyer email au vendeur
            send_delivery_confirmed_to_seller(order)
            
            messages.success(request, '✅ Réception confirmée ! Le paiement sera libéré au vendeur sous 24-48h.')
        else:
            messages.error(request, '❌ Impossible de confirmer cette commande.')
        
        return redirect('orders:my-orders')
    
    return redirect('orders:my-orders')

@login_required
def seller_orders_view(request):
    """
    Commandes reçues par le vendeur
    """
    if not request.user.is_seller:
        messages.error(request, 'Vous devez être vendeur pour accéder à cette page.')
        return redirect('accounts:dashboard')
    
    # Récupérer toutes les commandes contenant des produits du vendeur
    orders = Order.objects.filter(
        items__seller=request.user
    ).distinct().order_by('-created_at')
    
    return render(request, 'orders/seller_orders.html', {'orders': orders})