#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Webhook para Mercado Pago
Recebe notificações de pagamento e processa automaticamente
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

logger = logging.getLogger(__name__)

class WebhookServer:
    """Servidor webhook para receber notificações do Mercado Pago"""
    
    def __init__(self, bot_instance, payment_manager, notification_manager, port: int = 5000):
        self.bot = bot_instance
        self.payment_manager = payment_manager
        self.notification_manager = notification_manager
        self.port = port
        
        # Configura Flask
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configura rotas
        self.setup_routes()
        
    def setup_routes(self):
        """Configura as rotas do webhook"""
        
        @self.app.route('/webhook/mercadopago', methods=['POST'])
        def mercadopago_webhook():
            """Endpoint para webhooks do Mercado Pago"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({"error": "No data received"}), 400
                
                # Log da notificação
                logger.info(f"Webhook recebido: {data}")
                
                # Processa notificação em thread separada
                threading.Thread(
                    target=self._process_webhook_async,
                    args=(data,)
                ).start()
                
                return jsonify({"status": "ok"}), 200
                
            except Exception as e:
                logger.error(f"Erro no webhook: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/webhook/test', methods=['GET', 'POST'])
        def test_webhook():
            """Endpoint para testar webhook"""
            return jsonify({
                "status": "ok",
                "message": "Webhook funcionando!",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Endpoint de health check"""
            return jsonify({
                "status": "healthy",
                "service": "SSH Bot Webhook",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/stats', methods=['GET'])
        def stats():
            """Endpoint com estatísticas básicas"""
            try:
                total_users = len(self.bot.db.get_all_users())
                
                return jsonify({
                    "total_users": total_users,
                    "webhook_status": "active",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def _process_webhook_async(self, data: Dict[Any, Any]):
        """Processa webhook em thread separada"""
        try:
            # Cria novo loop de eventos para esta thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executa processamento
            loop.run_until_complete(self._process_webhook(data))
            
        except Exception as e:
            logger.error(f"Erro no processamento async do webhook: {e}")
        finally:
            loop.close()
    
    async def _process_webhook(self, data: Dict[Any, Any]):
        """Processa notificação do webhook"""
        try:
            # Extrai informações da notificação
            notification_type = data.get("type")
            
            if notification_type == "payment":
                await self._process_payment_notification(data)
            
            elif notification_type == "plan":
                await self._process_plan_notification(data)
            
            elif notification_type == "subscription":
                await self._process_subscription_notification(data)
            
            else:
                logger.warning(f"Tipo de notificação desconhecido: {notification_type}")
                
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
    
    async def _process_payment_notification(self, data: Dict[Any, Any]):
        """Processa notificação de pagamento"""
        try:
            payment_data = data.get("data", {})
            payment_id = payment_data.get("id")
            
            if not payment_id:
                logger.error("Payment ID não encontrado na notificação")
                return
            
            # Consulta status atual do pagamento
            status = self.payment_manager.check_payment_status(str(payment_id))
            
            if status == "approved":
                # Processa aprovação
                success = self.payment_manager.process_payment_approval(str(payment_id))
                
                if success:
                    # Busca dados do pagamento no banco
                    payment_info = self.bot.db.get_pending_payment(str(payment_id))
                    
                    if payment_info:
                        user_id = payment_info['user_id']
                        plan_type = payment_info['plan_type']
                        amount = payment_info['amount']
                        
                        # Busca dados do usuário
                        user_data = self.bot.db.get_user(user_id)
                        plan_info = self.payment_manager.get_plan_info(plan_type)
                        
                        if user_data and plan_info:
                            # Notifica aprovação
                            await self.notification_manager.notify_payment_approved(
                                user_data, 
                                {"payment_id": payment_id, "amount": amount},
                                plan_info
                            )
                            
                            # Envia mensagem para o usuário
                            await self._notify_user_payment_approved(user_id, plan_info)
                
            elif status == "rejected":
                # Processa rejeição
                payment_info = self.bot.db.get_pending_payment(str(payment_id))
                
                if payment_info:
                    user_data = self.bot.db.get_user(payment_info['user_id'])
                    
                    if user_data:
                        await self.notification_manager.notify_payment_failed(
                            user_data,
                            {"payment_id": payment_id, "amount": payment_info['amount']},
                            "Pagamento rejeitado"
                        )
            
        except Exception as e:
            logger.error(f"Erro ao processar notificação de pagamento: {e}")
    
    async def _process_plan_notification(self, data: Dict[Any, Any]):
        """Processa notificação de plano"""
        # Implementar se necessário
        pass
    
    async def _process_subscription_notification(self, data: Dict[Any, Any]):
        """Processa notificação de assinatura"""
        # Implementar se necessário
        pass
    
    async def _notify_user_payment_approved(self, user_id: int, plan_info: Dict):
        """Notifica usuário sobre pagamento aprovado"""
        try:
            expires_date = datetime.now().strftime('%d/%m/%Y')
            
            message = f"""
🎉 <b>Pagamento Aprovado!</b>

✅ Seu plano premium foi ativado com sucesso!

📦 <b>Plano:</b> {plan_info['name']}
⏰ <b>Válido até:</b> {expires_date}

💎 <b>Benefícios liberados:</b>
• Contas SSH ilimitadas
• Sem tempo de espera
• Múltiplos servidores
• Suporte prioritário

🚀 Digite /start para criar sua primeira conta SSH premium!
            """
            
            await self.bot.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar usuário: {e}")
    
    def run(self, host: str = '0.0.0.0', debug: bool = False):
        """Executa o servidor webhook"""
        logger.info(f"Iniciando servidor webhook na porta {self.port}")
        self.app.run(host=host, port=self.port, debug=debug)
    
    def run_threaded(self, host: str = '0.0.0.0', debug: bool = False):
        """Executa o servidor webhook em thread separada"""
        def run_server():
            self.app.run(host=host, port=self.port, debug=debug, use_reloader=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info(f"Servidor webhook iniciado em thread separada na porta {self.port}")
        return thread

# Classe para gerenciar URLs de webhook
class WebhookManager:
    """Gerenciador de URLs de webhook"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get_mercadopago_webhook_url(self) -> str:
        """Retorna URL do webhook do Mercado Pago"""
        return f"{self.base_url}/webhook/mercadopago"
    
    def get_test_webhook_url(self) -> str:
        """Retorna URL de teste do webhook"""
        return f"{self.base_url}/webhook/test"
    
    def get_health_check_url(self) -> str:
        """Retorna URL de health check"""
        return f"{self.base_url}/health"
    
    async def register_webhook_with_mercadopago(self, access_token: str, webhook_url: str) -> bool:
        """
        Registra webhook no Mercado Pago (implementação futura)
        
        Args:
            access_token: Token de acesso do MP
            webhook_url: URL do webhook
            
        Returns:
            True se registrado com sucesso
        """
        # Implementar registro automático de webhook no MP
        # Por enquanto, deve ser feito manualmente no painel do MP
        logger.info(f"Webhook URL para configurar no MP: {webhook_url}")
        return True

# Utilitários para teste
class WebhookTester:
    """Utilitários para testar webhook"""
    
    @staticmethod
    def create_test_payment_notification(payment_id: str, status: str = "approved") -> Dict:
        """Cria notificação de teste para pagamento"""
        return {
            "id": 12345,
            "live_mode": False,
            "type": "payment",
            "date_created": datetime.now().isoformat(),
            "application_id": 123456789,
            "user_id": 123456789,
            "version": 1,
            "api_version": "v1",
            "action": "payment.updated",
            "data": {
                "id": payment_id
            }
        }
    
    @staticmethod
    async def test_webhook_endpoint(webhook_url: str, payment_id: str) -> bool:
        """Testa endpoint de webhook"""
        import aiohttp
        
        try:
            test_data = WebhookTester.create_test_payment_notification(payment_id)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=test_data) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Erro ao testar webhook: {e}")
            return False

