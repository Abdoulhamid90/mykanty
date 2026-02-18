"""
VIEWS COMPLÈTES POUR MY KANTY SERVICES
Remplacez TOUT le contenu de : services/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Expert, ServiceCategory, ServiceRequest, Review, SubscriptionPlan

def experts_directory(request):
    """Page annuaire des experts avec filtres"""
    experts = Expert.objects.filter(is_available=True)
    
    # Filtres
    category_slug = request.GET.get('category')
    city = request.GET.get('city')
    search = request.GET.get('q')
    sort = request.GET.get('sort', '-average_rating')
    
    if category_slug:
        experts = experts.filter(categories__slug=category_slug)
    
    if city:
        experts = experts.filter(city__icontains=city)
    
    if search:
        experts = experts.filter(
            Q(business_name__icontains=search) |
            Q(bio__icontains=search) |
            Q(skills__icontains=search)
        )
    
    # Tri
    sort_options = {
        '-average_rating': '-average_rating',
        'price_asc': 'min_price',
        'price_desc': '-min_price',
        '-created_at': '-created_at',
    }
    experts = experts.order_by(sort_options.get(sort, '-average_rating'))
    
    # Pagination
    paginator = Paginator(experts, 12)
    page = request.GET.get('page')
    experts = paginator.get_page(page)
    
    # Récupérer toutes les catégories et villes
    categories = ServiceCategory.objects.filter(is_active=True)
    cities = Expert.objects.values_list('city', flat=True).distinct()
    
    context = {
        'experts': experts,
        'categories': categories,
        'cities': cities,
        'selected_category': category_slug,
        'selected_city': city,
        'search_query': search,
        'current_sort': sort,
    }
    
    return render(request, 'services/experts_directory.html', context)


def expert_detail(request, slug):
    """Page profil d'un expert"""
    expert = get_object_or_404(Expert, slug=slug)
    
    # Récupérer les avis
    reviews = expert.reviews.all()[:10]
    
    # Statistiques détaillées
    review_stats = expert.reviews.aggregate(
        avg_professionalism=Avg('professionalism'),
        avg_quality=Avg('quality'),
        avg_punctuality=Avg('punctuality'),
        avg_value=Avg('value_for_money'),
    )
    
    context = {
        'expert': expert,
        'reviews': reviews,
        'review_stats': review_stats,
        'badges': expert.get_badges(),
    }
    
    return render(request, 'services/expert_detail.html', context)


def request_service(request, expert_slug):
    """Formulaire de demande de service"""
    expert = get_object_or_404(Expert, slug=expert_slug)
    
    # Vérifier si l'expert peut recevoir des demandes
    if not expert.can_receive_requests:
        messages.error(request, "Cet expert ne peut plus recevoir de demandes pour le moment.")
        return redirect('services:expert-detail', slug=expert_slug)
    
    if request.method == 'POST':
        # Créer la demande
        service_request = ServiceRequest.objects.create(
            client=request.user if request.user.is_authenticated else None,
            expert=expert,
            category_id=request.POST.get('category'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            budget=request.POST.get('budget') or None,
            location=request.POST.get('location'),
            preferred_date=request.POST.get('preferred_date') or None,
            client_name=request.POST.get('client_name'),
            client_phone=request.POST.get('client_phone'),
            client_email=request.POST.get('client_email'),
        )
        
        # Incrémenter le compteur de demandes
        expert.requests_this_month += 1
        expert.total_requests += 1
        expert.save()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # NOTIFICATION EMAIL À L'EXPERT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        try:
            subject = f"🔔 Nouvelle demande de service - {service_request.title}"
            
            message = f"""
Bonjour {expert.business_name},

Vous avez reçu une nouvelle demande de service sur My Kanty !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 DÉTAILS DE LA DEMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 Titre : {service_request.title}
📝 Description : {service_request.description}

👤 CLIENT
━━━━━━━━
• Nom : {service_request.client_name}
• Téléphone : {service_request.client_phone}
• Email : {service_request.client_email}
• Localisation : {service_request.location}

{f'💰 Budget : {service_request.budget} XOF' if service_request.budget else ''}
{f'📅 Date préférée : {service_request.preferred_date.strftime("%d/%m/%Y")}' if service_request.preferred_date else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ ACTION REQUISE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connectez-vous à votre dashboard pour répondre au client :
👉 https://mykanty-production.up.railway.app/services/dashboard/demande/{service_request.id}/

⏰ Répondez dans les 24h pour maximiser vos chances d'obtenir ce contrat !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

My Kanty Services
🇹🇬 +228 93 33 78 02 | 🇳🇪 +227 92 53 44 35
contact@mykanty.com
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[expert.email],
                fail_silently=True,
            )
            
            print(f"✅ Email envoyé à l'expert: {expert.email}")
            
        except Exception as e:
            print(f"❌ Erreur envoi email expert: {str(e)}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # NOTIFICATION EMAIL AU CLIENT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        try:
            client_subject = f"✅ Demande envoyée à {expert.business_name}"
            
            client_message = f"""
Bonjour {service_request.client_name},

Votre demande de service a bien été envoyée à {expert.business_name}.

📋 VOTRE DEMANDE
━━━━━━━━━━━━━━━
{service_request.title}
{service_request.description}

⏰ PROCHAINES ÉTAPES
━━━━━━━━━━━━━━━━
1. {expert.business_name} va examiner votre demande
2. Il vous contactera dans les 24-48h par téléphone ou email
3. Il vous proposera un devis personnalisé
4. Vous pourrez accepter et planifier le service

📞 CONTACT DE L'EXPERT
━━━━━━━━━━━━━━━━━━━
• Téléphone : {expert.phone}
• Email : {expert.email}
{f'• WhatsApp : {expert.whatsapp}' if expert.whatsapp else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Merci d'utiliser My Kanty Services !

My Kanty
🇹🇬 +228 93 33 78 02 | 🇳🇪 +227 92 53 44 35
            """
            
            send_mail(
                subject=client_subject,
                message=client_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[service_request.client_email],
                fail_silently=True,
            )
            
            print(f"✅ Email envoyé au client: {service_request.client_email}")
            
        except Exception as e:
            print(f"❌ Erreur envoi email client: {str(e)}")
        
        messages.success(request, f"Votre demande a été envoyée à {expert.business_name}. Vous serez contacté sous peu !")
        return redirect('services:request-success', request_id=service_request.id)
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'expert': expert,
        'categories': categories,
        'today': timezone.now(),
    }
    
    return render(request, 'services/request_service.html', context)


def request_success(request, request_id):
    """Page de confirmation après demande"""
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    context = {
        'service_request': service_request,
    }
    
    return render(request, 'services/request_success.html', context)


@login_required
def expert_dashboard(request):
    """Dashboard de l'expert"""
    try:
        expert = request.user.expert_profile
    except:
        messages.error(request, "Vous devez d'abord créer un profil d'expert.")
        return redirect('services:become-expert')
    
    # Récupérer les demandes
    requests_pending = expert.received_requests.filter(status='pending').order_by('-created_at')
    requests_in_progress = expert.received_requests.filter(
        status__in=['contacted', 'accepted', 'in_progress']
    ).order_by('-created_at')
    requests_completed = expert.received_requests.filter(status='completed').order_by('-completed_at')[:5]
    
    # Statistiques du mois
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0)
    
    requests_this_month = expert.received_requests.filter(created_at__gte=start_of_month).count()
    completed_this_month = expert.received_requests.filter(
        status='completed',
        completed_at__gte=start_of_month
    ).count()
    
    # Vérifier l'abonnement
    subscription_days_left = 0
    if expert.subscription_end:
        subscription_days_left = (expert.subscription_end - today).days
    
    context = {
        'expert': expert,
        'requests_pending': requests_pending,
        'requests_in_progress': requests_in_progress,
        'requests_completed': requests_completed,
        'requests_this_month': requests_this_month,
        'completed_this_month': completed_this_month,
        'subscription_days_left': subscription_days_left,
    }
    
    return render(request, 'services/expert_dashboard.html', context)


@login_required
def expert_request_detail(request, request_id):
    """Détails d'une demande pour l'expert"""
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    # Vérifier que c'est bien la demande de cet expert
    if service_request.expert.user != request.user:
        messages.error(request, "Vous n'avez pas accès à cette demande.")
        return redirect('services:expert-dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'respond':
            service_request.status = 'contacted'
            service_request.expert_response = request.POST.get('response')
            service_request.expert_quote = request.POST.get('quote') or None
            service_request.responded_at = timezone.now()
            service_request.save()
            messages.success(request, "Votre réponse a été envoyée au client.")
            
            # Envoyer email au client
            try:
                subject = f"📩 {service_request.expert.business_name} a répondu à votre demande"
                message = f"""
Bonjour {service_request.client_name},

{service_request.expert.business_name} a répondu à votre demande de service !

📋 VOTRE DEMANDE
{service_request.title}

💬 RÉPONSE DE L'EXPERT
{service_request.expert_response}

{f'💰 DEVIS PROPOSÉ: {service_request.expert_quote} XOF' if service_request.expert_quote else ''}

📞 CONTACT
• Téléphone: {service_request.expert.phone}
• Email: {service_request.expert.email}

My Kanty Services
                """
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [service_request.client_email], fail_silently=True)
            except:
                pass
        
        elif action == 'accept':
            service_request.status = 'accepted'
            service_request.save()
            messages.success(request, "Demande acceptée !")
        
        elif action == 'complete':
            service_request.status = 'completed'
            service_request.completed_at = timezone.now()
            service_request.save()
            service_request.expert.completed_services += 1
            service_request.expert.save()
            messages.success(request, "Service marqué comme terminé !")
        
        elif action == 'cancel':
            service_request.status = 'cancelled'
            service_request.save()
            messages.info(request, "Demande annulée.")
        
        return redirect('services:expert-request-detail', request_id=request_id)
    
    context = {
        'service_request': service_request,
    }
    
    return render(request, 'services/expert_request_detail.html', context)


@login_required
def expert_profile_edit(request):
    """Éditer le profil d'expert"""
    try:
        expert = request.user.expert_profile
    except:
        messages.error(request, "Créez d'abord un profil d'expert.")
        return redirect('services:become-expert')
    
    if request.method == 'POST':
        expert.business_name = request.POST.get('business_name')
        expert.bio = request.POST.get('bio')
        expert.skills = request.POST.get('skills')
        expert.city = request.POST.get('city')
        expert.country = request.POST.get('country')
        expert.address = request.POST.get('address')
        expert.service_zone = request.POST.get('service_zone')
        expert.phone = request.POST.get('phone')
        expert.whatsapp = request.POST.get('whatsapp')
        expert.email = request.POST.get('email')
        expert.website = request.POST.get('website')
        expert.hourly_rate = request.POST.get('hourly_rate') or None
        expert.min_price = request.POST.get('min_price') or None
        expert.price_description = request.POST.get('price_description')
        expert.years_experience = request.POST.get('years_experience') or 0
        expert.certifications = request.POST.get('certifications')
        expert.availability_note = request.POST.get('availability_note')
        expert.is_available = request.POST.get('is_available') == 'on'
        
        if request.FILES.get('avatar'):
            expert.avatar = request.FILES['avatar']
        
        expert.save()
        
        # Gérer les catégories
        category_ids = request.POST.getlist('categories')
        expert.categories.set(category_ids)
        
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect('services:expert-dashboard')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'expert': expert,
        'categories': categories,
    }
    
    return render(request, 'services/expert_profile_edit.html', context)


def subscription_plans(request):
    """Page des plans d'abonnement"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'services/subscription_plans.html', context)


@login_required
def subscribe(request, plan_name):
    """Page de souscription à un plan"""
    plan = get_object_or_404(SubscriptionPlan, name=plan_name, is_active=True)
    
    try:
        expert = request.user.expert_profile
    except:
        messages.error(request, "Créez d'abord un profil d'expert.")
        return redirect('services:become-expert')
    
    if request.method == 'POST':
        # Vérification du paiement (à implémenter avec Mobile Money)
        payment_reference = request.POST.get('payment_reference')
        
        # Créer l'abonnement
        start_date = timezone.now()
        end_date = start_date + timedelta(days=30)
        
        from .models import Subscription
        subscription = Subscription.objects.create(
            expert=expert,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            amount_paid=plan.price,
            payment_reference=payment_reference,
            payment_verified=False,  # À vérifier manuellement
        )
        
        # Mettre à jour l'expert
        expert.subscription_plan = plan
        expert.subscription_start = start_date
        expert.subscription_end = end_date
        expert.requests_this_month = 0
        expert.save()
        
        messages.success(request, f"Abonnement {plan.display_name} activé ! Vérification du paiement en cours.")
        return redirect('services:expert-dashboard')
    
    context = {
        'plan': plan,
        'expert': expert,
    }
    
    return render(request, 'services/subscribe.html', context)


def become_expert(request):
    """Page d'inscription en tant qu'expert"""
    if not request.user.is_authenticated:
        messages.info(request, "Connectez-vous d'abord pour devenir expert.")
        return redirect('accounts:login')
    
    # Vérifier si l'utilisateur est déjà expert
    try:
        expert = request.user.expert_profile
        return redirect('services:expert-dashboard')
    except:
        pass
    
    if request.method == 'POST':
        # Créer le profil expert
        expert = Expert.objects.create(
            user=request.user,
            business_name=request.POST.get('business_name'),
            bio=request.POST.get('bio'),
            skills=request.POST.get('skills'),
            city=request.POST.get('city'),
            country=request.POST.get('country'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            service_zone=request.POST.get('service_zone', ''),
            years_experience=request.POST.get('years_experience', 0),
        )
        
        # Ajouter les catégories
        category_ids = request.POST.getlist('categories')
        expert.categories.set(category_ids)
        
        messages.success(request, "Profil expert créé ! Choisissez maintenant votre plan d'abonnement.")
        return redirect('services:subscription-plans')
    
    categories = ServiceCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'services/become_expert.html', context)