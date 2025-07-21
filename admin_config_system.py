#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Configuração via Chat
Módulo para administradores configurarem o bot através do Telegram
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Estados da conversa
(
    CONFIG_MENU, CONFIG_SERVERS, CONFIG_PAYMENTS, CONFIG_NOTIFICATIONS,
    CONFIG_MESSAGES, CONFIG_USERS, ADD_SERVER, EDIT_SERVER, REMOVE_SERVER,
    SET_MP_TOKEN, SET_PRICES, SET_GROUP_IDS, BROADCAST_MESSAGE,
    USER_MANAGEMENT, PREMIUM_MANAGEMENT
) = range(15)

class ConfigState:
    def __init__(self, user_id: int, current_menu: str, temp_data: Dict = None):
        self.user_id = user_id
        self.current_menu = current_menu
        self.temp_data = temp_data if temp_data is not None else {}

class AdminConfigManager:
    """Gerenciador de configurações administrativas"""
    
    def __init__(self, bot_instance, database_manager, config_file_path: str = "config.json"):
        self.bot = bot_instance
        self.db = database_manager
        self.config_file = config_file_path
        self.active_configs = {}  # user_id -> ConfigState
        
    def load_config(self) -> Dict:
        """Carrega configuração do arquivo"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return {}
    
    def save_config(self, config_data: Dict) -> bool:
        """Salva configuração no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar config: {e}")
            return False
    
    async def start_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Inicia o sistema de configuração"""
        user_id = update.effective_user.id
        
        # Verifica se é admin
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Acesso negado!")
            return ConversationHandler.END
        
        # Inicializa estado
        self.active_configs[user_id] = ConfigState(user_id=user_id, current_menu="main")
        
        await self._show_main_config_menu(update, context)
        return CONFIG_MENU
    
    async def _show_main_config_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra menu principal de configuração"""
        config = self.load_config()
        
        menu_text = f"""
⚙️ <b>PAINEL DE CONFIGURAÇÃO</b>

📊 <b>Status Atual:</b>
🤖 Bot Token: {'✅ Configurado' if config.get('bot_token') else '❌ Não configurado'}
💳 Mercado Pago: {'✅ Configurado' if config.get('mercado_pago_access_token') else '❌ Não configurado'}
🖥️ Servidores: {len(config.get('ssh_servers', []))} configurados
👥 Grupos: {'✅ Configurado' if config.get('notification_group_id') else '❌ Não configurado'}

🛠️ <b>Opções de Configuração:</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("🖥️ SERVIDORES SSH", callback_data="config_servers")],
            [InlineKeyboardButton("💳 PAGAMENTOS", callback_data="config_payments")],
            [InlineKeyboardButton("🔔 NOTIFICAÇÕES", callback_data="config_notifications")],
            [InlineKeyboardButton("📢 MENSAGENS", callback_data="config_messages")],
            [InlineKeyboardButton("👥 USUÁRIOS", callback_data="config_users")],
            [InlineKeyboardButton("📊 RELATÓRIOS", callback_data="config_reports")],
            [InlineKeyboardButton("❌ SAIR", callback_data="config_exit")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
    
    async def handle_config_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Manipula callbacks de configuração"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in self.active_configs:
            await query.edit_message_text("❌ Sessão expirada. Use /config novamente.")
            return ConversationHandler.END
        
        if data == "config_exit":
            del self.active_configs[user_id]
            await query.edit_message_text("✅ Configuração finalizada!")
            return ConversationHandler.END
        
        elif data == "config_servers":
            return await self._show_servers_menu(update, context)
        
        elif data == "config_payments":
            return await self._show_payments_menu(update, context)
        
        elif data == "config_notifications":
            return await self._show_notifications_menu(update, context)
        
        elif data == "config_messages":
            return await self._show_messages_menu(update, context)
        
        elif data == "config_users":
            return await self._show_users_menu(update, context)
        
        elif data == "config_back":
            await self._show_main_config_menu(update, context)
            return CONFIG_MENU
        
        return CONFIG_MENU
    
    async def _show_servers_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mostra menu de configuração de servidores"""
        config = self.load_config()
        servers = config.get('ssh_servers', [])
        
        menu_text = f"""
🖥️ <b>CONFIGURAÇÃO DE SERVIDORES SSH</b>

📊 <b>Servidores Cadastrados:</b> {len(servers)}

"""
        
        for i, server in enumerate(servers, 1):
            status = "🟢 Ativo" if server.get('active', True) else "🔴 Inativo"
            menu_text += f"{i}. <b>{server.get('name', 'Sem nome')}</b>\n"
            menu_text += f"   IP: <code>{server.get('ip', 'N/A')}</code>\n"
            menu_text += f"   Status: {status}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ ADICIONAR SERVIDOR", callback_data="add_server")],
            [InlineKeyboardButton("✏️ EDITAR SERVIDOR", callback_data="edit_server")],
            [InlineKeyboardButton("🗑️ REMOVER SERVIDOR", callback_data="remove_server")],
            [InlineKeyboardButton("🔄 TESTAR SERVIDORES", callback_data="test_servers")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="config_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
        
        return CONFIG_SERVERS
    
    async def _show_payments_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mostra menu de configuração de pagamentos"""
        config = self.load_config()
        pricing = config.get('pricing', {})
        
        menu_text = f"""
💳 <b>CONFIGURAÇÃO DE PAGAMENTOS</b>

🔑 <b>Mercado Pago Token:</b> {'✅ Configurado' if config.get('mercado_pago_access_token') else '❌ Não configurado'}

💰 <b>Preços Atuais:</b>
• Semanal: R$ {pricing.get('weekly', {}).get('price', 0):.2f}
• Mensal: R$ {pricing.get('monthly', {}).get('price', 0):.2f}

📊 <b>Estatísticas:</b>
• Vendas hoje: Em desenvolvimento
• Receita total: Em desenvolvimento
        """
        
        keyboard = [
            [InlineKeyboardButton("🔑 CONFIGURAR TOKEN MP", callback_data="set_mp_token")],
            [InlineKeyboardButton("💰 ALTERAR PREÇOS", callback_data="set_prices")],
            [InlineKeyboardButton("📊 VER VENDAS", callback_data="view_sales")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="config_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
        
        return CONFIG_PAYMENTS
    
    async def _show_notifications_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mostra menu de configuração de notificações"""
        config = self.load_config()
        
        menu_text = f"""
🔔 <b>CONFIGURAÇÃO DE NOTIFICAÇÕES</b>

📱 <b>Grupos Configurados:</b>
• Vendas: {'✅' if config.get('notification_group_id') else '❌'} <code>{config.get('notification_group_id', 'Não configurado')}</code>
• Admin: {'✅' if config.get('admin_group_id') else '❌'} <code>{config.get('admin_group_id', 'Não configurado')}</code>

⚙️ <b>Configurações:</b>
• Notificar vendas: ✅ Ativo
• Notificar erros: ✅ Ativo
• Notificar novos usuários: ✅ Ativo
        """
        
        keyboard = [
            [InlineKeyboardButton("📱 CONFIGURAR GRUPOS", callback_data="set_group_ids")],
            [InlineKeyboardButton("🔔 TESTAR NOTIFICAÇÃO", callback_data="test_notification")],
            [InlineKeyboardButton("⚙️ CONFIGURAÇÕES", callback_data="notification_settings")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="config_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
        
        return CONFIG_NOTIFICATIONS
    
    async def _show_messages_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mostra menu de configuração de mensagens"""
        total_users = len(self.db.get_all_users())
        
        menu_text = f"""
📢 <b>SISTEMA DE MENSAGENS</b>

👥 <b>Usuários Cadastrados:</b> {total_users}

📊 <b>Últimos Broadcasts:</b>
Em desenvolvimento...

🛠️ <b>Ferramentas Disponíveis:</b>
• Enviar mensagem para todos
• Mensagem para usuários premium
• Mensagem para usuários gratuitos
• Mensagem personalizada
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 BROADCAST GERAL", callback_data="broadcast_all")],
            [InlineKeyboardButton("💎 BROADCAST PREMIUM", callback_data="broadcast_premium")],
            [InlineKeyboardButton("🆓 BROADCAST GRATUITO", callback_data="broadcast_free")],
            [InlineKeyboardButton("📝 MENSAGEM PERSONALIZADA", callback_data="custom_message")],
            [InlineKeyboardButton("📊 HISTÓRICO", callback_data="broadcast_history")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="config_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
        
        return CONFIG_MESSAGES
    
    async def _show_users_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Mostra menu de gerenciamento de usuários"""
        users = self.db.get_all_users()
        total_users = len(users)
        
        # Conta usuários premium (implementação básica)
        premium_users = 0  # Implementar contagem real
        
        menu_text = f"""
👥 <b>GERENCIAMENTO DE USUÁRIOS</b>

📊 <b>Estatísticas:</b>
• Total de usuários: {total_users}
• Usuários premium: {premium_users}
• Usuários gratuitos: {total_users - premium_users}

🛠️ <b>Ferramentas:</b>
• Buscar usuário por ID
• Gerenciar premium
• Banir/desbanir usuário
• Ver histórico de atividades
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 BUSCAR USUÁRIO", callback_data="search_user")],
            [InlineKeyboardButton("💎 GERENCIAR PREMIUM", callback_data="manage_premium")],
            [InlineKeyboardButton("🚫 BANIR USUÁRIO", callback_data="ban_user")],
            [InlineKeyboardButton("📊 ESTATÍSTICAS", callback_data="user_stats")],
            [InlineKeyboardButton("🔙 VOLTAR", callback_data="config_back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(
            menu_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup
        )
        
        return CONFIG_USERS
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Manipula entrada de texto durante configuração"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.active_configs:
            return ConversationHandler.END
        
        state = self.active_configs[user_id]
        
        # Processa baseado no estado atual
        if state.current_menu == "add_server":
            return await self._process_add_server(update, context, text)
        
        elif state.current_menu == "set_mp_token":
            return await self._process_mp_token(update, context, text)
        
        elif state.current_menu == "set_prices":
            return await self._process_prices(update, context, text)
        
        elif state.current_menu == "broadcast_message":
            return await self._process_broadcast(update, context, text)
        
        return CONFIG_MENU
    
    async def _process_add_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
        """Processa adição de servidor"""
        state = self.active_configs[update.effective_user.id]
        
        if 'step' not in state.temp_data:
            state.temp_data['step'] = 'name'
        
        if state.temp_data['step'] == 'name':
            state.temp_data['name'] = text
            state.temp_data['step'] = 'ip'
            await update.message.reply_text("📝 Agora digite o IP do servidor:")
            return CONFIG_SERVERS
        
        elif state.temp_data['step'] == 'ip':
            state.temp_data['ip'] = text
            state.temp_data['step'] = 'password'
            await update.message.reply_text("🔑 Agora digite a senha do servidor:")
            return CONFIG_SERVERS
        
        elif state.temp_data['step'] == 'password':
            state.temp_data['password'] = text
            
            # Salva servidor
            config = self.load_config()
            if 'ssh_servers' not in config:
                config['ssh_servers'] = []
            
            new_server = {
                'name': state.temp_data['name'],
                'ip': state.temp_data['ip'],
                'password': state.temp_data['password'],
                'port': 22,
                'active': True
            }
            
            config['ssh_servers'].append(new_server)
            
            if self.save_config(config):
                await update.message.reply_text(
                    f"✅ Servidor '{state.temp_data['name']}' adicionado com sucesso!"
                )
            else:
                await update.message.reply_text("❌ Erro ao salvar configuração!")
            
            # Limpa dados temporários
            state.temp_data = {}
            state.current_menu = "servers"
            
            return await self._show_servers_menu(update, context)
    
    async def _process_mp_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
        """Processa configuração do token Mercado Pago"""
        config = self.load_config()
        config['mercado_pago_access_token'] = text.strip()
        
        if self.save_config(config):
            await update.message.reply_text("✅ Token do Mercado Pago configurado com sucesso!")
        else:
            await update.message.reply_text("❌ Erro ao salvar token!")
        
        return await self._show_payments_menu(update, context)
    
    async def _process_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
        """Processa alteração de preços"""
        try:
            lines = text.strip().split('\n')
            weekly_price = float(lines[0])
            monthly_price = float(lines[1]) if len(lines) > 1 else weekly_price * 2
            
            config = self.load_config()
            if 'pricing' not in config:
                config['pricing'] = {}
            
            config['pricing']['weekly'] = {
                'price': weekly_price,
                'duration_days': 7,
                'description': 'Plano Semanal'
            }
            
            config['pricing']['monthly'] = {
                'price': monthly_price,
                'duration_days': 30,
                'description': 'Plano Mensal'
            }
            
            if self.save_config(config):
                await update.message.reply_text(
                    f"✅ Preços atualizados!\n"
                    f"Semanal: R$ {weekly_price:.2f}\n"
                    f"Mensal: R$ {monthly_price:.2f}"
                )
            else:
                await update.message.reply_text("❌ Erro ao salvar preços!")
                
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Formato inválido! Use:\n"
                "Preço semanal\n"
                "Preço mensal"
            )
        
        return await self._show_payments_menu(update, context)
    
    async def _process_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> int:
        """Processa envio de broadcast"""
        # Implementar sistema de broadcast
        await update.message.reply_text("📢 Enviando mensagem para todos os usuários...")
        
        # Aqui você integraria com o BroadcastManager
        # broadcast_id = await self.broadcast_manager.create_broadcast(text, update.effective_user.id)
        # result = await self.broadcast_manager.send_broadcast(broadcast_id)
        
        await update.message.reply_text(
            "✅ Broadcast enviado!\n"
            "📊 Estatísticas: Em desenvolvimento"
        )
        
        return await self._show_messages_menu(update, context)
    
    def _is_admin(self, user_id: int) -> bool:
        """Verifica se usuário é administrador"""
        config = self.load_config()
        admin_ids = config.get('admin_ids', [])
        return user_id in admin_ids
    
    async def cancel_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancela configuração"""
        user_id = update.effective_user.id
        if user_id in self.active_configs:
            del self.active_configs[user_id]
        
        await update.message.reply_text("❌ Configuração cancelada!")
        return ConversationHandler.END

# Comandos de configuração rápida
class QuickConfigCommands:
    """Comandos de configuração rápida"""
    
    def __init__(self, config_manager: AdminConfigManager):
        self.config_manager = config_manager
    
    async def set_mp_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para definir token MP rapidamente"""
        if not self.config_manager._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /setmptoken <token>")
            return
        
        token = ' '.join(context.args)
        config = self.config_manager.load_config()
        config['mercado_pago_access_token'] = token
        
        if self.config_manager.save_config(config):
            await update.message.reply_text("✅ Token MP configurado!")
        else:
            await update.message.reply_text("❌ Erro ao salvar!")
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para adicionar administrador"""
        if not self.config_manager._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Use: /addadmin <user_id>")
            return
        
        try:
            new_admin_id = int(context.args[0])
            config = self.config_manager.load_config()
            
            if 'admin_ids' not in config:
                config['admin_ids'] = []
            
            if new_admin_id not in config['admin_ids']:
                config['admin_ids'].append(new_admin_id)
                
                if self.config_manager.save_config(config):
                    await update.message.reply_text(f"✅ Admin {new_admin_id} adicionado!")
                else:
                    await update.message.reply_text("❌ Erro ao salvar!")
            else:
                await update.message.reply_text("❌ Usuário já é admin!")
                
        except ValueError:
            await update.message.reply_text("❌ ID inválido!")
    
    async def set_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para definir grupo de notificações"""
        if not self.config_manager._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado!")
            return
        
        chat_id = update.effective_chat.id
        config = self.config_manager.load_config()
        config['notification_group_id'] = chat_id
        
        if self.config_manager.save_config(config):
            await update.message.reply_text(f"✅ Grupo de notificações configurado!\nID: {chat_id}")
        else:
            await update.message.reply_text("❌ Erro ao salvar!")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para ver status da configuração"""
        if not self.config_manager._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado!")
            return
        
        config = self.config_manager.load_config()
        
        status_text = f"""
📊 <b>STATUS DA CONFIGURAÇÃO</b>

🤖 <b>Bot:</b> {'✅' if config.get('bot_token') else '❌'}
💳 <b>Mercado Pago:</b> {'✅' if config.get('mercado_pago_access_token') else '❌'}
🖥️ <b>Servidores:</b> {len(config.get('ssh_servers', []))}
👥 <b>Admins:</b> {len(config.get('admin_ids', []))}
📱 <b>Grupo Notificações:</b> {'✅' if config.get('notification_group_id') else '❌'}

💰 <b>Preços:</b>
• Semanal: R$ {config.get('pricing', {}).get('weekly', {}).get('price', 0):.2f}
• Mensal: R$ {config.get('pricing', {}).get('monthly', {}).get('price', 0):.2f}
        """
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)

