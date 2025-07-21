#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Notificações e Mensagens em Massa
Módulo para gerenciar notificações de vendas e broadcast de mensagens
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from telegram import Bot, ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class NotificationConfig:
    def __init__(self, sales_group_id: int = 0, admin_group_id: int = 0, support_group_id: int = 0, enable_sales_notifications: bool = True, enable_admin_notifications: bool = True, enable_user_notifications: bool = True):
        self.sales_group_id = sales_group_id
        self.admin_group_id = admin_group_id
        self.support_group_id = support_group_id
        self.enable_sales_notifications = enable_sales_notifications
        self.enable_admin_notifications = enable_admin_notifications
        self.enable_user_notifications = enable_user_notifications

class BroadcastMessage:
    def __init__(self, message_id: int, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True, sent_count: int = 0, total_users: int = 0, failed_count: int = 0, completed: bool = False, created_at: datetime = None):
        self.message_id = message_id
        self.text = text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.sent_count = sent_count
        self.total_users = total_users
        self.failed_count = failed_count
        self.completed = completed
        self.created_at = created_at if created_at is not None else datetime.now()

class NotificationManager:
    """Gerenciador de notificações"""
    
    def __init__(self, bot: Bot, config: NotificationConfig, database_manager):
        self.bot = bot
        self.config = config
        self.db = database_manager
        
    async def notify_new_user(self, user_data: Dict):
        """Notifica sobre novo usuário"""
        if not self.config.enable_admin_notifications:
            return
            
        message = f"""
🆕 <b>Novo usuário cadastrado!</b>

👤 <b>Nome:</b> {user_data.get('first_name', 'N/A')}
📝 <b>Username:</b> @{user_data.get('username', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id')}</code>
📅 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 <b>Total de usuários:</b> {len(self.db.get_all_users())}
        """
        
        await self._send_to_admin_group(message)
    
    async def notify_test_creation(self, user_data: Dict, server_info: Dict, ssh_data: Dict):
        """Notifica sobre criação de teste SSH"""
        if not self.config.enable_sales_notifications:
            return
            
        message = f"""
🆓 <b>Novo teste SSH criado!</b>

👤 <b>Usuário:</b> {user_data.get('first_name', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id')}</code>
📝 <b>Username:</b> @{user_data.get('username', 'N/A')}

🖥️ <b>Servidor:</b> {server_info.get('name', 'N/A')}
🌐 <b>IP:</b> <code>{server_info.get('ip', 'N/A')}</code>
👤 <b>SSH User:</b> <code>{ssh_data.get('username', 'N/A')}</code>
⏰ <b>Expira:</b> {ssh_data.get('expires_at', 'N/A')}

📅 <b>Criado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        await self._send_to_sales_group(message)
    
    async def notify_payment_created(self, user_data: Dict, payment_data: Dict, plan_info: Dict):
        """Notifica sobre pagamento criado"""
        if not self.config.enable_sales_notifications:
            return
            
        message = f"""
💳 <b>Novo pagamento gerado!</b>

👤 <b>Cliente:</b> {user_data.get('first_name', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id')}</code>
📝 <b>Username:</b> @{user_data.get('username', 'N/A')}

📦 <b>Plano:</b> {plan_info.get('name', 'N/A')}
💰 <b>Valor:</b> R$ {payment_data.get('amount', 0):.2f}
⏰ <b>Duração:</b> {plan_info.get('duration_days', 0)} dias

🆔 <b>Payment ID:</b> <code>{payment_data.get('payment_id', 'N/A')}</code>
📅 <b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
⏰ <b>Expira em:</b> 30 minutos

💡 <i>Aguardando pagamento...</i>
        """
        
        await self._send_to_sales_group(message)
    
    async def notify_payment_approved(self, user_data: Dict, payment_data: Dict, plan_info: Dict):
        """Notifica sobre pagamento aprovado"""
        if not self.config.enable_sales_notifications:
            return
            
        message = f"""
✅ <b>PAGAMENTO APROVADO!</b> 🎉

👤 <b>Cliente:</b> {user_data.get('first_name', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id')}</code>
📝 <b>Username:</b> @{user_data.get('username', 'N/A')}

📦 <b>Plano:</b> {plan_info.get('name', 'N/A')}
💰 <b>Valor:</b> R$ {payment_data.get('amount', 0):.2f}
⏰ <b>Duração:</b> {plan_info.get('duration_days', 0)} dias

🆔 <b>Payment ID:</b> <code>{payment_data.get('payment_id', 'N/A')}</code>
📅 <b>Pago em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

💎 <b>Status:</b> Premium ativado!
🚀 <b>Cliente pode criar SSH ilimitado!</b>
        """
        
        await self._send_to_sales_group(message)
        await self._send_to_admin_group(message)
    
    async def notify_payment_failed(self, user_data: Dict, payment_data: Dict, reason: str = ""):
        """Notifica sobre pagamento falhado"""
        if not self.config.enable_sales_notifications:
            return
            
        message = f"""
❌ <b>Pagamento rejeitado/expirado</b>

👤 <b>Cliente:</b> {user_data.get('first_name', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id')}</code>

🆔 <b>Payment ID:</b> <code>{payment_data.get('payment_id', 'N/A')}</code>
💰 <b>Valor:</b> R$ {payment_data.get('amount', 0):.2f}
📅 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

❓ <b>Motivo:</b> {reason or 'Não especificado'}

💡 <i>Cliente pode tentar novamente</i>
        """
        
        await self._send_to_sales_group(message)
    
    async def notify_system_error(self, error_type: str, error_message: str, user_id: int = None):
        """Notifica sobre erro do sistema"""
        if not self.config.enable_admin_notifications:
            return
            
        message = f"""
🚨 <b>ERRO DO SISTEMA</b>

🔧 <b>Tipo:</b> {error_type}
📝 <b>Mensagem:</b> {error_message}
👤 <b>Usuário afetado:</b> {user_id or 'N/A'}
📅 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

⚠️ <i>Verificar logs para mais detalhes</i>
        """
        
        await self._send_to_admin_group(message)
    
    async def notify_server_status(self, server_name: str, status: str, details: str = ""):
        """Notifica sobre status do servidor"""
        if not self.config.enable_admin_notifications:
            return
            
        status_emoji = "✅" if status == "online" else "❌"
        
        message = f"""
{status_emoji} <b>Status do Servidor</b>

🖥️ <b>Servidor:</b> {server_name}
📊 <b>Status:</b> {status.upper()}
📝 <b>Detalhes:</b> {details or 'N/A'}
📅 <b>Verificado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        await self._send_to_admin_group(message)
    
    async def _send_to_sales_group(self, message: str):
        """Envia mensagem para grupo de vendas"""
        if self.config.sales_group_id:
            try:
                await self.bot.send_message(
                    chat_id=self.config.sales_group_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except TelegramError as e:
                logger.error(f"Erro ao enviar para grupo de vendas: {e}")
    
    async def _send_to_admin_group(self, message: str):
        """Envia mensagem para grupo de administradores"""
        if self.config.admin_group_id:
            try:
                await self.bot.send_message(
                    chat_id=self.config.admin_group_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except TelegramError as e:
                logger.error(f"Erro ao enviar para grupo admin: {e}")
    
    async def _send_to_support_group(self, message: str):
        """Envia mensagem para grupo de suporte"""
        if self.config.support_group_id:
            try:
                await self.bot.send_message(
                    chat_id=self.config.support_group_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except TelegramError as e:
                logger.error(f"Erro ao enviar para grupo de suporte: {e}")

class BroadcastManager:
    """Gerenciador de mensagens em massa"""
    
    def __init__(self, bot: Bot, database_manager):
        self.bot = bot
        self.db = database_manager
        
    async def create_broadcast(self, message_text: str, admin_id: int) -> int:
        """
        Cria uma nova mensagem de broadcast
        
        Args:
            message_text: Texto da mensagem
            admin_id: ID do administrador que criou
            
        Returns:
            ID da mensagem de broadcast
        """
        users = self.db.get_all_users()
        total_users = len(users)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO broadcast_messages (message, total_users, created_at)
                VALUES (?, ?, ?)
            ''', (message_text, total_users, datetime.now().isoformat()))
            
            broadcast_id = cursor.lastrowid
            conn.commit()
            
        return broadcast_id
    
    async def send_broadcast(self, broadcast_id: int, delay_seconds: float = 0.1) -> Dict[str, int]:
        """
        Envia mensagem de broadcast para todos os usuários
        
        Args:
            broadcast_id: ID da mensagem de broadcast
            delay_seconds: Delay entre envios para evitar rate limit
            
        Returns:
            Estatísticas do envio
        """
        # Busca dados do broadcast
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM broadcast_messages WHERE id = ?', (broadcast_id,))
            broadcast_data = cursor.fetchone()
            
            if not broadcast_data:
                return {"error": "Broadcast não encontrado"}
        
        message_text = broadcast_data[1]  # message column
        users = self.db.get_all_users()
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await self.bot.send_message(
                    chat_id=user['user_id'],
                    text=message_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                sent_count += 1
                
                # Atualiza contador no banco
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE broadcast_messages SET sent_count = ?
                        WHERE id = ?
                    ''', (sent_count, broadcast_id))
                    conn.commit()
                
                # Delay para evitar rate limit
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                    
            except TelegramError as e:
                failed_count += 1
                logger.warning(f"Falha ao enviar para {user['user_id']}: {e}")
                
                # Delay mesmo em caso de erro
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
        
        # Marca como completo
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE broadcast_messages 
                SET sent_count = ?, completed = TRUE
                WHERE id = ?
            ''', (sent_count, broadcast_id))
            conn.commit()
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(users)
        }
    
    async def get_broadcast_status(self, broadcast_id: int) -> Optional[Dict]:
        """Obtém status de um broadcast"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM broadcast_messages WHERE id = ?', (broadcast_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        
        return None
    
    async def get_recent_broadcasts(self, limit: int = 10) -> List[Dict]:
        """Obtém broadcasts recentes"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM broadcast_messages 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

class UserMessageManager:
    """Gerenciador de mensagens para usuários específicos"""
    
    def __init__(self, bot: Bot, database_manager):
        self.bot = bot
        self.db = database_manager
    
    async def send_welcome_message(self, user_id: int, user_name: str):
        """Envia mensagem de boas-vindas personalizada"""
        message = f"""
🎉 <b>Bem-vindo ao SSH Bot Premium, {user_name}!</b>

Obrigado por se cadastrar! Aqui estão algumas dicas para começar:

🆓 <b>Teste Grátis:</b>
• Crie sua primeira conta SSH de 6 horas
• Teste nossa qualidade sem compromisso
• Limite de 1 teste por 24 horas

💎 <b>Planos Premium:</b>
• Contas SSH ilimitadas
• Múltiplos servidores disponíveis
• Suporte prioritário 24/7
• Sem tempo de espera

📱 <b>Aplicativo:</b>
• Baixe nosso app oficial
• Interface otimizada
• Configuração automática

💬 <b>Suporte:</b>
• Dúvidas? Fale conosco!
• Resposta rápida garantida

<i>Digite /start para acessar o menu principal!</i>
        """
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except TelegramError as e:
            logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")
    
    async def send_payment_reminder(self, user_id: int, payment_id: str, amount: float, expires_in_minutes: int):
        """Envia lembrete de pagamento"""
        message = f"""
⏰ <b>Lembrete de Pagamento</b>

Você tem um pagamento PIX pendente que expira em {expires_in_minutes} minutos!

💰 <b>Valor:</b> R$ {amount:.2f}
🆔 <b>ID:</b> <code>{payment_id}</code>

📱 <b>Para pagar:</b>
1. Copie o código PIX
2. Abra seu app bancário
3. Escolha PIX → Copia e Cola
4. Cole e confirme o pagamento

⚡ <b>Ativação automática após pagamento!</b>

<i>Digite /start para acessar o pagamento</i>
        """
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except TelegramError as e:
            logger.error(f"Erro ao enviar lembrete de pagamento: {e}")
    
    async def send_premium_activated(self, user_id: int, plan_name: str, expires_date: str):
        """Envia confirmação de ativação premium"""
        message = f"""
🎉 <b>Premium Ativado com Sucesso!</b>

Parabéns! Seu plano premium foi ativado:

📦 <b>Plano:</b> {plan_name}
⏰ <b>Válido até:</b> {expires_date}

✅ <b>Benefícios liberados:</b>
• Contas SSH ilimitadas
• Sem tempo de espera
• Múltiplos servidores
• Suporte prioritário

🚀 <b>Comece agora:</b>
Digite /start e crie sua primeira conta SSH premium!

💎 <i>Aproveite todos os benefícios!</i>
        """
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except TelegramError as e:
            logger.error(f"Erro ao enviar confirmação premium: {e}")
    
    async def send_premium_expiring(self, user_id: int, days_left: int):
        """Envia aviso de expiração do premium"""
        message = f"""
⚠️ <b>Seu Premium está expirando!</b>

Seu plano premium expira em {days_left} dia(s).

💎 <b>Para renovar:</b>
• Acesse /start
• Escolha seu plano
• Pague via PIX instantâneo

🎯 <b>Não perca os benefícios:</b>
• Contas SSH ilimitadas
• Múltiplos servidores
• Suporte prioritário

💰 <b>Renove agora e continue aproveitando!</b>
        """
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
        except TelegramError as e:
            logger.error(f"Erro ao enviar aviso de expiração: {e}")
    
    async def send_custom_message(self, user_id: int, message_text: str, parse_mode: str = "HTML"):
        """Envia mensagem personalizada para usuário"""
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            logger.error(f"Erro ao enviar mensagem personalizada: {e}")
            return False

