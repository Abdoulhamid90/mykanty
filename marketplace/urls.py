from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('dashboard-admin/', views.admin_dashboard_view, name='admin-dashboard'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('legal/', include('legal.urls')),
    path('chatbot-api/', views.chatbot_api_view, name='chatbot-api'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)