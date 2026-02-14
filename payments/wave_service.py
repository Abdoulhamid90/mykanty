"""
Service pour l'intégration de Wave Payment API
Documentation: https://developers.wave.com/
"""

import requests
import hashlib
import hmac
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class WavePaymentService:
    """
    Service pour gérer les paiements via Wave
    """
    
    def __init__(self):
        self.api_key = settings.WAVE_API_KEY
        self.api_secret = settings.WAVE_API_SECRET
        self.api_url = settings.WAVE_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def create_payment(self, amount, currency='XOF', customer_phone=None, order_number=None, metadata=None):
        """
        Crée une demande de paiement Wave
        
        Args:
            amount (Decimal): Montant à payer
            currency (str): Devise (XOF par défaut)
            customer_phone (str): Numéro de téléphone du client
            order_number (str): Numéro de commande
            metadata (dict): Métadonnées supplémentaires
        
        Returns:
            dict: Réponse de l'API Wave
        """
        try:
            payload = {
                'amount': str(amount),
                'currency': currency,
                'error_url': f'{settings.SITE_URL}/payment/error/',
                'success_url': f'{settings.SITE_URL}/payment/success/',
            }
            
            if customer_phone:
                payload['customer_phone_number'] = customer_phone
            
            if order_number:
                payload['client_reference'] = order_number
            
            if metadata:
                payload['metadata'] = metadata

            response = requests.post(
                f'{self.api_url}checkout/sessions',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Paiement Wave créé: {data.get('id')}")
            return {
                'success': True,
                'data': data,
                'wave_url': data.get('wave_launch_url'),
                'checkout_id': data.get('id')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la création du paiement Wave: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_payment(self, checkout_id):
        """
        Vérifie le statut d'un paiement
        
        Args:
            checkout_id (str): ID de la session de paiement
        
        Returns:
            dict: Statut du paiement
        """
        try:
            response = requests.get(
                f'{self.api_url}checkout/sessions/{checkout_id}',
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'status': data.get('payment_status'),
                'data': data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la vérification du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_webhook(self, payload, signature):
        """
        Traite un webhook Wave
        
        Args:
            payload (dict): Données du webhook
            signature (str): Signature pour vérification
        
        Returns:
            dict: Résultat du traitement
        """
        try:
            # Vérifier la signature du webhook
            if not self.verify_webhook_signature(payload, signature):
                logger.warning("Signature webhook invalide")
                return {
                    'success': False,
                    'error': 'Invalid signature'
                }
            
            event_type = payload.get('type')
            
            if event_type == 'checkout.session.completed':
                return self._handle_payment_completed(payload)
            elif event_type == 'checkout.session.failed':
                return self._handle_payment_failed(payload)
            
            return {
                'success': True,
                'message': f'Event {event_type} received'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_webhook_signature(self, payload, signature):
        """
        Vérifie la signature d'un webhook Wave
        
        Args:
            payload (dict): Données du webhook
            signature (str): Signature à vérifier
        
        Returns:
            bool: True si la signature est valide
        """
        try:
            # Créer la signature attendue
            payload_string = str(payload)
            expected_signature = hmac.new(
                self.api_secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de signature: {str(e)}")
            return False

    def _handle_payment_completed(self, payload):
        """
        Traite un paiement complété
        """
        checkout_id = payload.get('data', {}).get('id')
        logger.info(f"Paiement complété: {checkout_id}")
        
        return {
            'success': True,
            'action': 'payment_completed',
            'checkout_id': checkout_id
        }

    def _handle_payment_failed(self, payload):
        """
        Traite un paiement échoué
        """
        checkout_id = payload.get('data', {}).get('id')
        logger.warning(f"Paiement échoué: {checkout_id}")
        
        return {
            'success': True,
            'action': 'payment_failed',
            'checkout_id': checkout_id
        }

    def create_refund(self, transaction_id, amount, reason):
        """
        Crée un remboursement
        
        Args:
            transaction_id (str): ID de la transaction à rembourser
            amount (Decimal): Montant à rembourser
            reason (str): Raison du remboursement
        
        Returns:
            dict: Résultat du remboursement
        """
        try:
            payload = {
                'transaction_id': transaction_id,
                'amount': str(amount),
                'reason': reason
            }
            
            response = requests.post(
                f'{self.api_url}refunds',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Remboursement créé: {data.get('id')}")
            return {
                'success': True,
                'data': data
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la création du remboursement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Instance du service Wave
wave_service = WavePaymentService()
