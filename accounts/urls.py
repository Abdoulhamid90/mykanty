from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('become-seller/', views.become_seller_view, name='become-seller'),
    path('reports/', views.seller_reports_view, name='seller-reports'),
    path('seller/<str:username>/', views.seller_public_profile_view, name='seller-profile'),
]