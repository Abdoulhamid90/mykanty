from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='product-list'),
    path('<int:product_id>/', views.product_detail_view, name='product-detail'),
]