#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot SSH Completo com Sistema de Vendas Mercado Pago
Versão completa com todas as funcionalidades integradas
"""

import os
import json
import time
import random
import string
import sqlite3
import logging
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ParseMode
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Importa módulo de pagamentos
from mercado_pago_integration import PaymentManager, PaymentData

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações do bot
class BotConfig:
    def __init__(self, token: str = "", mercado_pago_access_token: str = "", admin_ids: List[int] = None, notification_group_id: int = 0, ssh_servers: List[Dict] = None, database_path: str = "bot_database.db", webhook_url: str = "", bot_active: bool = True):
        self.token = token
        self.mercado_pago_access_token = mercado_pago_access_token
        self.admin_ids = admin_ids if admin_ids is not None else []
        self.notification_group_id = notification_group_id
        self.ssh_servers = ssh_servers if ssh_servers is not None else [
                {"name": "Servidor 1", "ip": "SEU-IP-AQUI", "password": "SUA-SENHA-AQUI", "active": True},
                {"name": "Servidor 2", "ip": "SEU-IP-AQUI", "password": "SUA-SENHA-AQUI", "active": True},
                {"name": "Servidor 3", "ip": "SEU-IP-AQUI", "password": "SUA-SENHA-AQUI", "active": True}
            ]
        self.database_path = database_path
        self.webhook_url = webhook_url
        self.bot_active = bot_active

# Classe para gerenciar o banco de dados
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Retorna conexão com o banco"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_test_creation TIMESTAMP,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_expires TIMESTAMP
                )
            ''')
            
            # Tabela de contas SSH
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ssh_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    password TEXT,
                    server_ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    account_type TEXT DEFAULT 'test'
                )
            ''')
            
            # Tabela de vendas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    payment_id TEXT,
                    amount REAL,
                    status TEXT,
                    product_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP
                )
            ''')
            
            # Tabela de configurações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Tabela de mensagens em massa
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS broadcast_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    sent_count INTEGER DEFAULT 0,
                    total_users INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Tabela de pagamentos pendentes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_payments (
                    payment_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    plan_type TEXT,
                    amount REAL,
                    qr_code TEXT,
                    qr_code_base64 TEXT,
                    ticket_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Adiciona ou atualiza um usuário"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Obtém informações de um usuário"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None
    
    def can_create_test(self, user_id: int) -> bool:
        """Verifica se o usuário pode criar um teste (limite de 24h para não-premium)"""
        user = self.get_user(user_id)
        if not user:
            return True
        
        # Usuários premium podem criar quantos quiserem
        if user.get('is_premium') and user.get('premium_expires'):
            expires = datetime.fromisoformat(user['premium_expires'])
            if datetime.now() < expires:
                return True
        
        # Usuários gratuitos têm limite de 24h
        if not user['last_test_creation']:
            return True
        
        last_creation = datetime.fromisoformat(user['last_test_creation'])
        return datetime.now() - last_creation >= timedelta(hours=24)
    
    def update_last_test_creation(self, user_id: int):
        """Atualiza o timestamp da última criação de teste"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_test_creation = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def add_ssh_account(self, user_id: int, username: str, password: str, 
                       server_ip: str, expires_at: datetime, account_type: str = 'test'):
        """Adiciona uma conta SSH"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ssh_accounts (user_id, username, password, server_ip, expires_at, account_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, password, server_ip, expires_at.isoformat(), account_type))
            conn.commit()
    
    def get_all_users(self) -> List[Dict]:
        """Obtém todos os usuários para broadcast"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, first_name FROM users')
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def save_pending_payment(self, payment: PaymentData, user_id: int, plan_type: str):
        """Salva pagamento pendente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO pending_payments 
                (payment_id, user_id, plan_type, amount, qr_code, qr_code_base64, ticket_url, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                payment.payment_id, user_id, plan_type, payment.amount,
                payment.qr_code, payment.qr_code_base64, payment.ticket_url,
                payment.expires_at.isoformat()
            ))
            conn.commit()
    
    def get_pending_payment(self, payment_id: str) -> Optional[Dict]:
        """Obtém pagamento pendente"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pending_payments WHERE payment_id = ?', (payment_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
        return None

# Classe principal do bot
class SSHBot:
    def __init__(self, config: BotConfig):
        self.config = config
        self.db = DatabaseManager(config.database_path)
        self.payment_manager = PaymentManager(
            config.mercado_pago_access_token, 
            self.db, 
            sandbox=True  # Mude para False em produção
        )
        self.application = None
        
    def generate_username(self) -> str:
        """Gera um nome de usuário aleatório"""
        prefix = "ssh"
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"
    
    def generate_password(self) -> str:
        """Gera uma senha aleatória"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        user_data = self.db.get_user(user.id)
        is_premium = user_data and user_data.get('is_premium', False)
        
        if is_premium and user_data.get('premium_expires'):
            expires = datetime.fromisoformat(user_data['premium_expires'])
            is_premium = datetime.now() < expires
        
        status_emoji = "💎" if is_premium else "🆓"
        status_text = "PREMIUM" if is_premium else "GRATUITO"
        
        welcome_text = f"""
🌟 <b>SSH Bot Premium - Sistema Completo!</b> 🌟

Olá <b>{user.first_name}</b>! 👋
{status_emoji} <b>Status:</b> {status_text}

🚀 <b>NOVIDADES v2.0:</b>
✅ Pagamento automático via PIX
✅ Notificações em tempo real
✅ Múltiplos servidores premium
✅ Sistema de configuração avançado
✅ Suporte 24/7 integrado

🎯 <b>Funcionalidades:</b>
🆓 Teste SSH 6h grátis (24h cooldown)
💎 Planos premium sem limites
📱 App oficial otimizado
💬 Suporte prioritário
📊 Painel administrativo

<i>Escolha uma opção para começar:</i>
        """
        
        keyboard = [
            [InlineKeyboardButton("🆓 TESTE GRÁTIS 6H", callback_data="create_test")],
            [
                InlineKeyboardButton("💎 SEMANAL R$10", callback_data="buy_weekly"),
                InlineKeyboardButton("🔥 MENSAL R$20", callback_data="buy_monthly")
            ],
            [InlineKeyboardButton("📱 BAIXAR APP", url="https://www.mediafire.com/file/vxzqhb0wbqwm9ky/GREAT+VPN+PRO.apk/file")],
            [
                InlineKeyboardButton("💬 SUPORTE", url="https://t.me/proverbiox9"),
                InlineKeyboardButton("ℹ️ MEUS DADOS", callback_data="my_info")
            ]
        ]
        
        # Adiciona botões de admin se for administrador
        if user.id in self.config.admin_ids:
            keyboard.append([InlineKeyboardButton("⚙️ PAINEL ADMIN", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def create_test_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para criar teste SSH"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self.db.can_create_test(user_id):
            user_data = self.db.get_user(user_id)
            is_premium = user_data and user_data.get('is_premium', False)
            
            if is_premium:
                # Usuário premium, pode criar
                pass
            else:
                await query.edit_message_text(
                    "⏰ <b>Limite de tempo atingido!</b>\n\n"
                    "❌ Você já criou um teste nas últimas 24 horas.\n"
                    "⏳ Aguarde o período de cooldown ou adquira um plano premium.\n\n"
                    "💎 <b>Vantagens Premium:</b>\n"
                    "✅ Contas SSH ilimitadas\n"
                    "✅ Sem tempo de espera\n"
                    "✅ Múltiplos servidores\n"
                    "✅ Suporte prioritário\n\n"
                    "🔥 <i>Aproveite nossos preços promocionais!</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("💎 SEMANAL R$10", callback_data="buy_weekly"),
                            InlineKeyboardButton("🔥 MENSAL R$20", callback_data="buy_monthly")
                        ],
                        [InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")]
                    ])
                )
                return
        
        # Seleciona servidor ativo aleatório
        active_servers = [s for s in self.config.ssh_servers if s.get('active', True)]
        if not active_servers:
            await query.edit_message_text(
                "🔧 <b>Manutenção em andamento</b>\n\n"
                "❌ Todos os servidores estão temporariamente indisponíveis.\n"
                "🔄 Tente novamente em alguns minutos.\n\n"
                "💡 <i>Nossos técnicos estão trabalhando para resolver rapidamente!</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 TENTAR NOVAMENTE", callback_data="create_test"),
                    InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")
                ]])
            )
            return
        
        server = random.choice(active_servers)
        username = self.generate_username()
        password = self.generate_password()
        expires_at = datetime.now() + timedelta(hours=6)
        
        # Simula criação da conta SSH
        success = await self.create_ssh_account(server, username, password, expires_at)
        
        if success:
            self.db.add_ssh_account(user_id, username, password, server['ip'], expires_at)
            self.db.update_last_test_creation(user_id)
            
            success_text = f"""
✅ <b>Conta SSH criada com sucesso!</b>

🖥️ <b>Servidor:</b> {server['name']}
🌐 <b>IP:</b> <code>{server['ip']}</code>
👤 <b>Usuário:</b> <code>{username}</code>
🔑 <b>Senha:</b> <code>{password}</code>
⏰ <b>Expira em:</b> 6 horas
📅 <b>Criado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

📱 <b>Como conectar:</b>
1️⃣ Baixe o aplicativo oficial
2️⃣ Configure com os dados acima
3️⃣ Ative dados móveis e desative Wi-Fi
4️⃣ Conecte e navegue ilimitado!

💡 <b>Dica:</b> Gostou? Nossos planos premium oferecem muito mais!
            """
            
            keyboard = [
                [InlineKeyboardButton("📱 BAIXAR APP", url="https://www.mediafire.com/file/vxzqhb0wbqwm9ky/GREAT+VPN+PRO.apk/file")],
                [
                    InlineKeyboardButton("💎 VER PLANOS", callback_data="buy_premium"),
                    InlineKeyboardButton("💬 SUPORTE", url="https://t.me/proverbiox9")
                ],
                [InlineKeyboardButton("🔙 MENU PRINCIPAL", callback_data="back_to_menu")]
            ]
            
            await query.edit_message_text(
                success_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Notifica grupo de vendas
            await self.notify_group(
                f"🆓 <b>Novo teste criado!</b>\n"
                f"👤 {query.from_user.first_name}\n"
                f"🆔 <code>{user_id}</code>\n"
                f"🖥️ {server['name']}\n"
                f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
        else:
            await query.edit_message_text(
                "❌ <b>Erro temporário</b>\n\n"
                "🔧 Ocorreu um problema na criação da conta.\n"
                "🔄 Tente novamente em alguns minutos.\n\n"
                "💬 Se o problema persistir, entre em contato com o suporte.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 TENTAR NOVAMENTE", callback_data="create_test")],
                    [
                        InlineKeyboardButton("💬 SUPORTE", url="https://t.me/proverbiox9"),
                        InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")
                    ]
                ])
            )
    
    async def buy_plan_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback genérico para compra de planos"""
        query = update.callback_query
        await query.answer()
        
        # Extrai tipo do plano do callback_data
        plan_type = query.data.replace("buy_", "")
        
        if plan_type == "premium":
            # Mostra opções de planos
            await self.show_premium_plans(query)
        else:
            # Processa compra específica
            await self.process_plan_purchase(query, plan_type)
    
    async def show_premium_plans(self, query):
        """Mostra planos premium disponíveis"""
        plans_text = """
💎 <b>PLANOS PREMIUM DISPONÍVEIS</b>

🚀 <b>PLANO SEMANAL</b>
💰 <b>Preço:</b> R$ 10,00
⏰ <b>Duração:</b> 7 dias
✅ Contas SSH ilimitadas
✅ Sem tempo de espera
✅ Múltiplos servidores
✅ Suporte prioritário

🔥 <b>PLANO MENSAL</b> <i>(Mais Popular)</i>
💰 <b>Preço:</b> R$ 20,00
⏰ <b>Duração:</b> 30 dias
✅ Contas SSH ilimitadas
✅ Sem tempo de espera
✅ Múltiplos servidores
✅ Suporte prioritário
✅ Desconto de 33%

🎯 <b>Pagamento:</b>
• PIX instantâneo e automático
• QR Code para facilitar
• Ativação imediata após pagamento

<i>Escolha seu plano e pague com segurança!</i>
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 SEMANAL - R$ 10", callback_data="buy_weekly")],
            [InlineKeyboardButton("🔥 MENSAL - R$ 20", callback_data="buy_monthly")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")]
        ]
        
        await query.edit_message_text(
            plans_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def process_plan_purchase(self, query, plan_type: str):
        """Processa compra de um plano específico"""
        user = query.from_user
        
        # Obtém informações do plano
        plan_info = self.payment_manager.get_plan_info(plan_type)
        if not plan_info:
            await query.edit_message_text("❌ Plano inválido!")
            return
        
        # Cria pagamento
        payment = self.payment_manager.create_payment(
            user_id=user.id,
            plan_type=plan_type,
            user_email=f"{user.id}@telegram.user"  # Email fictício para Telegram
        )
        
        if payment:
            # Salva pagamento pendente
            self.db.save_pending_payment(payment, user.id, plan_type)
            
            payment_text = f"""
💳 <b>Pagamento PIX Gerado!</b>

📦 <b>Plano:</b> {plan_info['name']}
💰 <b>Valor:</b> R$ {plan_info['price']:.2f}
⏰ <b>Duração:</b> {plan_info['duration_days']} dias
🆔 <b>ID Pagamento:</b> <code>{payment.payment_id}</code>

📱 <b>Como pagar:</b>
1️⃣ Copie o código PIX abaixo
2️⃣ Abra seu app bancário
3️⃣ Escolha PIX → Copia e Cola
4️⃣ Cole o código e confirme

⚡ <b>Ativação automática em até 2 minutos!</b>

🔗 <b>Código PIX:</b>
<code>{payment.qr_code}</code>

⏰ <i>Este pagamento expira em 30 minutos</i>
            """
            
            keyboard = [
                [InlineKeyboardButton("📋 COPIAR CÓDIGO PIX", callback_data=f"copy_pix_{payment.payment_id}")],
                [InlineKeyboardButton("🔍 VERIFICAR PAGAMENTO", callback_data=f"check_payment_{payment.payment_id}")],
                [InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")]
            ]
            
            await query.edit_message_text(
                payment_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Notifica grupo sobre nova venda
            await self.notify_group(
                f"💳 <b>Nova venda iniciada!</b>\n"
                f"👤 {user.first_name}\n"
                f"🆔 <code>{user.id}</code>\n"
                f"📦 {plan_info['name']}\n"
                f"💰 R$ {plan_info['price']:.2f}\n"
                f"🆔 Pagamento: <code>{payment.payment_id}</code>"
            )
            
        else:
            await query.edit_message_text(
                "❌ <b>Erro ao gerar pagamento</b>\n\n"
                "🔧 Ocorreu um problema temporário.\n"
                "🔄 Tente novamente em alguns minutos.\n\n"
                "💬 Se o problema persistir, entre em contato com o suporte.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 TENTAR NOVAMENTE", callback_data=f"buy_{plan_type}")],
                    [InlineKeyboardButton("💬 SUPORTE", url="https://t.me/proverbiox9")]
                ])
            )
    
    async def check_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verifica status de um pagamento"""
        query = update.callback_query
        await query.answer()
        
        payment_id = query.data.replace("check_payment_", "")
        
        # Verifica status no Mercado Pago
        status = self.payment_manager.check_payment_status(payment_id)
        
        if status == "approved":
            # Processa aprovação
            success = self.payment_manager.process_payment_approval(payment_id)
            
            if success:
                await query.edit_message_text(
                    "✅ <b>Pagamento aprovado!</b>\n\n"
                    "🎉 Seu plano premium foi ativado com sucesso!\n"
                    "💎 Agora você pode criar contas SSH ilimitadas!\n\n"
                    "🚀 <i>Aproveite todos os benefícios premium!</i>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🆓 CRIAR SSH", callback_data="create_test"),
                        InlineKeyboardButton("🔙 MENU", callback_data="back_to_menu")
                    ]])
                )
                
                # Notifica aprovação
                user = query.from_user
                await self.notify_group(
                    f"✅ <b>Pagamento aprovado!</b>\n"
                    f"👤 {user.first_name}\n"
                    f"🆔 <code>{user.id}</code>\n"
                    f"💳 <code>{payment_id}</code>\n"
                    f"💎 Premium ativado!"
                )
            else:
                await query.answer("❌ Erro ao processar pagamento", show_alert=True)
        
        elif status == "pending":
            await query.answer("⏳ Pagamento ainda pendente", show_alert=True)
        
        elif status == "rejected":
            await query.answer("❌ Pagamento rejeitado", show_alert=True)
        
        else:
            await query.answer("❓ Status desconhecido", show_alert=True)
    
    async def my_info_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra informações do usuário"""
        query = update.callback_query
        await query.answer()
        
        user = query.from_user
        user_data = self.db.get_user(user.id)
        
        is_premium = False
        premium_expires = "N/A"
        
        if user_data and user_data.get('is_premium'):
            if user_data.get('premium_expires'):
                expires = datetime.fromisoformat(user_data['premium_expires'])
                if datetime.now() < expires:
                    is_premium = True
                    premium_expires = expires.strftime('%d/%m/%Y %H:%M')
        
        status_emoji = "💎" if is_premium else "🆓"
        status_text = "Premium" if is_premium else "Gratuito"
        
        info_text = f"""
👤 <b>SUAS INFORMAÇÕES</b>

🆔 <b>ID:</b> <code>{user.id}</code>
👤 <b>Nome:</b> {user.first_name or 'N/A'}
📝 <b>Username:</b> @{user.username or 'N/A'}
📅 <b>Cadastrado:</b> {user_data.get('created_at', 'N/A')[:10] if user_data else 'N/A'}

{status_emoji} <b>Status:</b> {status_text}
⏰ <b>Premium expira:</b> {premium_expires}

📊 <b>Estatísticas:</b>
• Último teste: {user_data.get('last_test_creation', 'Nunca')[:16] if user_data and user_data.get('last_test_creation') else 'Nunca'}

🎯 <b>Benefícios disponíveis:</b>
{'✅ Contas SSH ilimitadas' if is_premium else '❌ Limite de 1 teste por 24h'}
{'✅ Múltiplos servidores' if is_premium else '❌ Servidor aleatório'}
{'✅ Suporte prioritário' if is_premium else '❌ Suporte padrão'}
        """
        
        keyboard = []
        if not is_premium:
            keyboard.append([InlineKeyboardButton("💎 ADQUIRIR PREMIUM", callback_data="buy_premium")])
        
        keyboard.append([InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")])
        
        await query.edit_message_text(
            info_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_panel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Painel administrativo"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id not in self.config.admin_ids:
            await query.answer("❌ Acesso negado", show_alert=True)
            return
        
        # Estatísticas básicas
        total_users = len(self.db.get_all_users())
        
        admin_text = f"""
⚙️ <b>PAINEL ADMINISTRATIVO</b>

📊 <b>Estatísticas:</b>
👥 Total de usuários: {total_users}
💎 Usuários premium: Em desenvolvimento
💰 Vendas hoje: Em desenvolvimento
📈 Receita total: Em desenvolvimento

🛠️ <b>Ferramentas disponíveis:</b>
📢 Enviar mensagem para todos
⚙️ Configurar servidores
📊 Relatórios detalhados
🔧 Manutenção do sistema

<i>Selecione uma opção abaixo:</i>
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast")],
            [InlineKeyboardButton("⚙️ SERVIDORES", callback_data="admin_servers")],
            [InlineKeyboardButton("📊 RELATÓRIOS", callback_data="admin_reports")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="back_to_menu")]
        ]
        
        await query.edit_message_text(
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def back_to_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Volta ao menu principal"""
        query = update.callback_query
        await query.answer()
        
        # Simula o comando /start
        await self.start_command(update, context)
    
    async def create_ssh_account(self, server: Dict, username: str, password: str, expires_at: datetime) -> bool:
        """Cria conta SSH no servidor"""
        try:
            # Comando para adicionar usuário
            add_user_cmd = f"sudo useradd -m -s /bin/bash {username}"
            subprocess.run(add_user_cmd, shell=True, check=True)

            # Comando para definir senha
            set_password_cmd = f"echo \"{username}:{password}\" | sudo chpasswd"
            subprocess.run(set_password_cmd, shell=True, check=True)

            # Definir expiração da conta (opcional, depende do sistema)
            # chage -E YYYY-MM-DD username
            expire_date = expires_at.strftime("%Y-%m-%d")
            set_expire_cmd = f"sudo chage -E {expire_date} {username}"
            subprocess.run(set_expire_cmd, shell=True, check=True)

            logger.info(f"Conta SSH {username} criada com sucesso no {server["ip"]}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando SSH: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao criar conta SSH: {e}")
            return False
    
    async def notify_group(self, message: str):
        """Envia notificação para o grupo"""
        if self.config.notification_group_id:
            try:
                await self.application.bot.send_message(
                    chat_id=self.config.notification_group_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Erro ao enviar notificação: {e}")
    
    def setup_handlers(self):
        """Configura os handlers do bot"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.create_test_callback, pattern="create_test"))
        self.application.add_handler(CallbackQueryHandler(self.buy_plan_callback, pattern="^buy_"))
        self.application.add_handler(CallbackQueryHandler(self.check_payment_callback, pattern="^check_payment_"))
        self.application.add_handler(CallbackQueryHandler(self.my_info_callback, pattern="my_info"))
        self.application.add_handler(CallbackQueryHandler(self.admin_panel_callback, pattern="admin_panel"))
        self.application.add_handler(CallbackQueryHandler(self.back_to_menu_callback, pattern="back_to_menu"))
    
    async def run(self):
        """Executa o bot"""
        self.application = Application.builder().token(self.config.token).build()
        self.setup_handlers()
        
        logger.info("🚀 Bot SSH Premium v2.0 iniciado!")
        await self.application.run_polling()

# Função para carregar configuração
def load_config() -> BotConfig:
    """Carrega configuração do arquivo JSON"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return BotConfig(
            token=data.get('bot_token', ''),
            mercado_pago_access_token=data.get('mercado_pago_access_token', ''),
            admin_ids=data.get('admin_ids', []),
            notification_group_id=data.get('notification_group_id', 0),
            ssh_servers=data.get('ssh_servers', []),
            webhook_url=data.get('webhook_url', '')
        )
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return BotConfig()

# Função principal
def main():
    """Função principal"""
    config = load_config()
    
    if not config.token:
        logger.error("Token do bot não configurado!")
        return
    
    if not config.mercado_pago_access_token:
        logger.error("Token do Mercado Pago não configurado!")
        return
    
    bot = SSHBot(config)
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()

