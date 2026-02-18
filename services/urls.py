"""
URLs POUR MY KANTY SERVICES
Créez ce fichier : services/urls.py
"""

from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Public
    path('', views.experts_directory, name='experts-directory'),
    path('expert/<slug:slug>/', views.expert_detail, name='expert-detail'),
    path('expert/<slug:expert_slug>/demande/', views.request_service, name='request-service'),
    path('demande/<int:request_id>/confirmation/', views.request_success, name='request-success'),
    path('devenir-expert/', views.become_expert, name='become-expert'),
    path('abonnements/', views.subscription_plans, name='subscription-plans'),
    path('abonnement/<str:plan_name>/souscrire/', views.subscribe, name='subscribe'),
    
    # Dashboard Expert
    path('dashboard/', views.expert_dashboard, name='expert-dashboard'),
    path('dashboard/demande/<int:request_id>/', views.expert_request_detail, name='expert-request-detail'),
    path('dashboard/profil/modifier/', views.expert_profile_edit, name='expert-profile-edit'),
]