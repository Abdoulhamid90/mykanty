from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_welcome_email(user):
    """Email de bienvenue après inscription"""
    subject = '🎉 Bienvenue sur My Kanty !'
    message = f"""
Bonjour {user.username},

Bienvenue sur My Kanty, votre marketplace de confiance !

Votre compte a été créé avec succès. Vous pouvez maintenant :
✅ Acheter des produits en toute sécurité
✅ Demander à devenir vendeur
✅ Profiter de notre système de paiement Escrow

Connectez-vous : http://127.0.0.1:8000/accounts/login/

À très bientôt !
L'équipe My Kanty
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [user.email])

def send_seller_request_submitted(seller_request):
    """Email de confirmation de demande vendeur"""
    subject = '📝 Demande vendeur reçue - My Kanty'
    message = f"""
Bonjour {seller_request.full_name},

Nous avons bien reçu votre demande pour devenir vendeur sur My Kanty.

Votre demande est en cours d'examen. Notre équipe vous répondra sous 24-48h.

Informations soumises :
- Nom : {seller_request.full_name}
- Téléphone : {seller_request.contact_number}
- Localisation : {seller_request.location}
- Types de produits : {seller_request.product_types}

Nous vous contacterons par email dès que votre demande sera traitée.

Cordialement,
L'équipe My Kanty
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [seller_request.user.email])

def send_seller_approved(seller_request):
    """Email d'approbation vendeur"""
    subject = '✅ Félicitations ! Vous êtes maintenant vendeur - My Kanty'
    message = f"""
Félicitations {seller_request.full_name} !

Votre demande vendeur a été approuvée ! 🎉

Vous pouvez maintenant :
✅ Ajouter vos produits
✅ Recevoir des commandes
✅ Gérer votre boutique

Rappel important :
💰 Commission : 5% sur chaque vente
🔐 Paiement via système Escrow sécurisé
⏱️ Paiement libéré 24-48h après confirmation de livraison

Commencez à vendre : http://127.0.0.1:8000/admin/products/product/add/

Bonne vente !
L'équipe My Kanty
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [seller_request.user.email])

def send_order_confirmation(order):
    """Email de confirmation de commande"""
    subject = f'🛒 Commande {order.order_number} confirmée - My Kanty'
    message = f"""
Bonjour {order.get_customer_name()},

Votre commande a été enregistrée avec succès !

Numéro de commande : {order.order_number}
Montant total : {order.total} XOF
Statut : {order.get_status_display()}

🔐 Protection Escrow :
Votre paiement est sécurisé. Le vendeur sera payé uniquement après confirmation de livraison.

Prochaines étapes :
1. Notre équipe vérifie votre paiement
2. Le vendeur prépare votre commande
3. Vous recevez votre colis
4. Vous confirmez la réception
5. Le vendeur est payé

Suivre ma commande : http://127.0.0.1:8000/orders/my-orders/

Merci de votre confiance !
L'équipe My Kanty
    """
    email = order.guest_email if order.guest_email else (order.user.email if order.user else None)
    if email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [email])

def send_payment_verified(order):
    """Email de paiement vérifié"""
    subject = f'✅ Paiement vérifié - Commande {order.order_number}'
    message = f"""
Bonjour {order.get_customer_name()},

Bonne nouvelle ! Votre paiement a été vérifié.

Commande : {order.order_number}
Montant : {order.total} XOF

Le vendeur a été notifié et va préparer votre commande.

Suivre ma commande : http://127.0.0.1:8000/orders/my-orders/

L'équipe My Kanty
    """
    email = order.guest_email if order.guest_email else (order.user.email if order.user else None)
    if email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [email])

def send_order_shipped(order):
    """Email d'expédition"""
    subject = f'📦 Commande {order.order_number} expédiée !'
    message = f"""
Bonjour {order.get_customer_name()},

Votre commande a été expédiée ! 🚚

Commande : {order.order_number}
Numéro de suivi : {order.tracking_number or 'Non disponible'}

Vous devriez recevoir votre colis sous 2-5 jours.

N'oubliez pas de confirmer la réception après livraison pour que le vendeur soit payé.

Suivre ma commande : http://127.0.0.1:8000/orders/my-orders/

L'équipe My Kanty
    """
    email = order.guest_email if order.guest_email else (order.user.email if order.user else None)
    if email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [email])

def send_delivery_confirmed_to_seller(order):
    """Email au vendeur : livraison confirmée"""
    first_item = order.items.first()
    if first_item and first_item.seller:
        subject = f'💰 Livraison confirmée - Paiement en cours - {order.order_number}'
        message = f"""
Bonjour,

Bonne nouvelle ! Le client a confirmé la réception de sa commande.

Commande : {order.order_number}
Montant total : {order.total} XOF
Commission My Kanty (5%) : {order.commission_amount} XOF
Vous recevrez : {order.seller_amount} XOF

Votre paiement sera libéré dans les 24-48h.

Voir la commande : http://127.0.0.1:8000/orders/seller-orders/

L'équipe My Kanty
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [first_item.seller.email])

def send_payment_released(order):
    """Email au vendeur : paiement libéré"""
    first_item = order.items.first()
    if first_item and first_item.seller:
        subject = f'💸 Paiement libéré - {order.order_number}'
        message = f"""
Félicitations !

Votre paiement a été libéré ! 🎉

Commande : {order.order_number}
Montant versé : {order.seller_amount} XOF

Le paiement sera effectué sur votre compte dans les prochaines heures.

Détails :
- Montant total commande : {order.total} XOF
- Commission My Kanty (5%) : {order.commission_amount} XOF
- Net à recevoir : {order.seller_amount} XOF

Merci de vendre sur My Kanty !
L'équipe My Kanty
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL or 'noreply@mykanty.com', [first_item.seller.email])