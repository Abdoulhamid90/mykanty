from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

def product_list_view(request):
    """
    Liste des produits avec recherche et filtres
    """
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    # Recherche
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Filtre par catégorie
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category__id=category_id)
    
    # Filtre par prix
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Tri
    sort = request.GET.get('sort', '-created_at')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'total_results': products.count(),
    }
    
    return render(request, 'products/product_list.html', context)


def product_detail_view(request, product_id):
    """
    Détail d'un produit
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Produits similaires
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Profil vendeur
    seller_profile = None
    if hasattr(product.seller, 'seller_profile'):
        seller_profile = product.seller.seller_profile
    
    context = {
        'product': product,
        'similar_products': similar_products,
        'seller_profile': seller_profile,
    }
    
    return render(request, 'products/product_detail.html', context)