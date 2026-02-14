from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('cgv/', views.cgv_view, name='cgv'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('mentions/', views.mentions_view, name='mentions'),
    path('escrow-guide/', views.escrow_guide_view, name='escrow-guide'),
]