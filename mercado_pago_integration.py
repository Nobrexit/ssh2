#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Integração com Mercado Pago
Sistema de pagamentos PIX para o Bot SSH
"""

import json
import uuid
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Any


logger = logging.getLogger(__name__)

class PaymentData:
    def __init__(self, payment_id: str, amount: float, status: str, qr_code: str, qr_code_base64: str, ticket_url: str, created_at: datetime, expires_at: datetime, payer_email: str, description: str):
        self.payment_id = payment_id
        self.amount = amount
        self.status = status
        self.qr_code = qr_code
        self.qr_code_base64 = qr_code_base64
        self.ticket_url = ticket_url
        self.created_at = created_at
        self.expires_at = expires_at
        self.payer_email = payer_email
        self.description = description

class MercadoPagoAPI:
    """Cliente para API do Mercado Pago"""
    
    def __init__(self, access_token: str, sandbox: bool = True):
        self.access_token = access_token
        self.sandbox = sandbox
        self.base_url = "https://api.mercadopago.com"
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": ""
        }
    
    def _generate_idempotency_key(self) -> str:
        """Gera chave de idempotência única"""
        return str(uuid.uuid4())
    
    def create_pix_payment(self, amount: float, payer_email: str, 
                          description: str = "Pagamento SSH Premium") -> Optional[PaymentData]:
        """
        Cria um pagamento PIX
        
        Args:
            amount: Valor do pagamento
            payer_email: Email do pagador
            description: Descrição do pagamento
            
        Returns:
            PaymentData ou None em caso de erro
        """
        try:
            # Gera chave de idempotência
            idempotency_key = self._generate_idempotency_key()
            headers = self.headers.copy()
            headers["X-Idempotency-Key"] = idempotency_key
            
            # Dados do pagamento
            payment_data = {
                "transaction_amount": amount,
                "payment_method_id": "pix",
                "payer": {
                    "email": payer_email
                },
                "description": description,
                "external_reference": f"ssh_bot_{int(time.time())}",
                "notification_url": "https://seu-webhook-url.com/webhook",  # Configure seu webhook
                "date_of_expiration": (datetime.now() + timedelta(minutes=30)).isoformat()
            }
            
            # Faz a requisição
            response = requests.post(
                f"{self.base_url}/v1/payments",
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Extrai dados do PIX
                transaction_data = data.get("point_of_interaction", {}).get("transaction_data", {})
                
                return PaymentData(
                    payment_id=str(data["id"]),
                    amount=amount,
                    status=data["status"],
                    qr_code=transaction_data.get("qr_code", ""),
                    qr_code_base64=transaction_data.get("qr_code_base64", ""),
                    ticket_url=transaction_data.get("ticket_url", ""),
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(minutes=30),
                    payer_email=payer_email,
                    description=description
                )
            else:
                logger.error(f"Erro ao criar pagamento: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na criação do pagamento PIX: {e}")
            return None
    
    def get_payment_status(self, payment_id: str) -> Optional[str]:
        """
        Consulta o status de um pagamento
        
        Args:
            payment_id: ID do pagamento
            
        Returns:
            Status do pagamento ou None em caso de erro
        """
        try:
            response = requests.get(
                f"{self.base_url}/v1/payments/{payment_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("status")
            else:
                logger.error(f"Erro ao consultar pagamento: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na consulta do pagamento: {e}")
            return None

class PaymentManager:
    """Gerenciador de pagamentos do bot"""
    
    def __init__(self, mercado_pago_token: str, database_manager, sandbox: bool = True):
        self.mp_api = MercadoPagoAPI(mercado_pago_token, sandbox)
        self.db = database_manager
        
        # Preços dos planos
        self.plans = {
            "weekly": {
                "price": 10.00,
                "duration_days": 7,
                "name": "Plano Semanal"
            },
            "monthly": {
                "price": 20.00,
                "duration_days": 30,
                "name": "Plano Mensal"
            }
        }
    
    def create_payment(self, user_id: int, plan_type: str, user_email: str) -> Optional[PaymentData]:
        """
        Cria um pagamento para um plano
        
        Args:
            user_id: ID do usuário
            plan_type: Tipo do plano (weekly/monthly)
            user_email: Email do usuário
            
        Returns:
            PaymentData ou None em caso de erro
        """
        if plan_type not in self.plans:
            logger.error(f"Plano inválido: {plan_type}")
            return None
        
        plan = self.plans[plan_type]
        
        # Cria pagamento no Mercado Pago
        payment = self.mp_api.create_pix_payment(
            amount=plan["price"],
            payer_email=user_email,
            description=f"{plan['name']} - SSH Premium"
        )
        
        if payment:
            # Salva no banco de dados
            self._save_payment_to_db(user_id, payment, plan_type)
            
        return payment
    
    def _save_payment_to_db(self, user_id: int, payment: PaymentData, plan_type: str):
        """Salva pagamento no banco de dados"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sales (user_id, payment_id, amount, status, product_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    payment.payment_id,
                    payment.amount,
                    payment.status,
                    plan_type,
                    payment.created_at.isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar pagamento no DB: {e}")
    
    def check_payment_status(self, payment_id: str) -> Optional[str]:
        """Verifica status de um pagamento"""
        return self.mp_api.get_payment_status(payment_id)
    
    def process_payment_approval(self, payment_id: str) -> bool:
        """
        Processa aprovação de pagamento
        
        Args:
            payment_id: ID do pagamento aprovado
            
        Returns:
            True se processado com sucesso
        """
        try:
            # Busca pagamento no banco
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, product_type, amount FROM sales 
                    WHERE payment_id = ? AND status != 'approved'
                ''', (payment_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                user_id, plan_type, amount = result
                
                # Atualiza status do pagamento
                cursor.execute('''
                    UPDATE sales SET status = 'approved', paid_at = CURRENT_TIMESTAMP
                    WHERE payment_id = ?
                ''', (payment_id,))
                
                # Ativa premium para o usuário
                plan = self.plans.get(plan_type)
                if plan:
                    expires_at = datetime.now() + timedelta(days=plan["duration_days"])
                    
                    cursor.execute('''
                        UPDATE users SET 
                        is_premium = TRUE, 
                        premium_expires = ?
                        WHERE user_id = ?
                    ''', (expires_at.isoformat(), user_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Erro ao processar aprovação: {e}")
            return False
    
    def get_plan_info(self, plan_type: str) -> Optional[Dict]:
        """Retorna informações de um plano"""
        return self.plans.get(plan_type)

# Webhook handler para notificações do Mercado Pago
class WebhookHandler:
    """Manipulador de webhooks do Mercado Pago"""
    
    def __init__(self, payment_manager: PaymentManager, bot_instance):
        self.payment_manager = payment_manager
        self.bot = bot_instance
    
    def handle_payment_notification(self, notification_data: Dict) -> bool:
        """
        Processa notificação de pagamento
        
        Args:
            notification_data: Dados da notificação
            
        Returns:
            True se processado com sucesso
        """
        try:
            # Extrai dados da notificação
            payment_id = notification_data.get("data", {}).get("id")
            if not payment_id:
                return False
            
            # Verifica status atual do pagamento
            status = self.payment_manager.check_payment_status(payment_id)
            
            if status == "approved":
                # Processa aprovação
                success = self.payment_manager.process_payment_approval(payment_id)
                
                if success:
                    # Notifica usuário e grupo
                    self._notify_payment_approved(payment_id)
                
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return False
    
    def _notify_payment_approved(self, payment_id: str):
        """Notifica sobre pagamento aprovado"""
        # Implementar notificação para usuário e grupo
        pass

