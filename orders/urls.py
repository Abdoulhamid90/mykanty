from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment/', views.payment_view, name='payment'),
    path('confirm-payment/', views.confirm_payment_view, name='confirm-payment'),
    path('success/<str:order_number>/', views.order_success_view, name='success'),
    path('my-orders/', views.my_orders_view, name='my-orders'),
    path('order/<str:order_number>/', views.order_detail_view, name='order-detail'),
    path('confirm-delivery/<str:order_number>/', views.confirm_delivery_view, name='confirm-delivery'),
    path('seller-orders/', views.seller_orders_view, name='seller-orders'),  # ← CETTE LIGNE
]