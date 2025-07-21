#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH Bot Premium - Sistema Completo Integrado
Arquivo principal que integra todos os módulos
"""

import os
import sys
import json
import logging
import asyncio
import signal
from datetime import datetime
from typing import Dict, List, Optional


# Importa módulos do bot
from bot_ssh_completo import SSHBot, BotConfig, DatabaseManager
from mercado_pago_integration import PaymentManager
from notification_system import NotificationManager, NotificationConfig, BroadcastManager, UserMessageManager
from admin_config_system import AdminConfigManager, QuickConfigCommands
from webhook_server import WebhookServer, WebhookManager

# Importa dependências do Telegram
from telegram import Bot
from telegram.ext import Application, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class IntegratedSSHBot:
    """Bot SSH integrado com todos os módulos"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # Inicializa componentes
        self.db = DatabaseManager(self.config.database_path)
        self.bot_instance = None
        self.application = None
        
        # Gerenciadores
        self.payment_manager = None
        self.notification_manager = None
        self.broadcast_manager = None
        self.user_message_manager = None
        self.admin_config_manager = None
        self.webhook_server = None
        self.webhook_manager = None
        
        # Estado do sistema
        self.is_running = False
        self.webhook_thread = None
        
    def load_config(self) -> BotConfig:
        """Carrega configuração do arquivo JSON"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Arquivo de configuração {self.config_file} não encontrado. Criando padrão...")
                self.create_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return BotConfig(
                token=data.get('bot_token', ''),
                mercado_pago_access_token=data.get('mercado_pago_access_token', ''),
                admin_ids=data.get('admin_ids', []),
                notification_group_id=data.get('notification_group_id', 0),
                ssh_servers=data.get("ssh_servers", []),
                webhook_url=data.get("webhook_url", ""),
                bot_active=data.get("bot_active", True)
            )
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return BotConfig()
    
    def create_default_config(self):
        """Cria arquivo de configuração padrão"""
        default_config = {
            "bot_token": "SEU_TOKEN_DO_BOT_AQUI",
            "mercado_pago_access_token": "SEU_ACCESS_TOKEN_MP_AQUI",
            "admin_ids": [123456789],
            "notification_group_id": -1001234567890,
            "webhook_url": "https://seu-dominio.com",
            "ssh_servers": [
                {
                    "name": "Servidor Principal",
                    "ip": "SEU-IP-AQUI",
                    "password": "SUA-SENHA-AQUI",
                    "port": 22,
                    "active": True
                }
            ],
            "pricing": {
                "weekly": {
                    "price": 10.00,
                    "duration_days": 7,
                    "description": "Plano Semanal"
                },
                "monthly": {
                    "price": 20.00,
                    "duration_days": 30,
                    "description": "Plano Mensal"
                }
            },
            "messages": {
                "welcome": "🌟 Bem-vindo ao SSH Bot Premium!",
                "test_limit": "❌ Você já criou um teste nas últimas 24 horas.",
                "server_error": "❌ Erro temporário. Tente novamente em alguns minutos."
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Arquivo de configuração padrão criado: {self.config_file}")
    
    async def initialize(self):
        """Inicializa todos os componentes do bot"""
        try:
            logger.info("🚀 Inicializando SSH Bot Premium...")
            
            # Valida configuração
            if not self.config.token:
                raise ValueError("Token do bot não configurado!")
            
            if not self.config.bot_active:
                logger.info("Bot está desativado na configuração. Não será iniciado.")
                return
            
            # Inicializa bot principal
            self.bot_instance = SSHBot(self.config)
            self.application = Application.builder().token(self.config.token).build()
            
            # Inicializa gerenciadores
            await self._initialize_managers()
            
            # Configura handlers
            self._setup_handlers()
            
            # Inicializa webhook se configurado
            if self.config.webhook_url and self.config.mercado_pago_access_token:
                await self._initialize_webhook()
            
            logger.info("✅ Todos os componentes inicializados com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            raise
    
    async def _initialize_managers(self):
        """Inicializa todos os gerenciadores"""
        # Payment Manager
        if self.config.mercado_pago_access_token:
            self.payment_manager = PaymentManager(
                self.config.mercado_pago_access_token,
                self.db,
                sandbox=True  # Mude para False em produção
            )
            logger.info("✅ Payment Manager inicializado")
        
        # Notification Manager
        notification_config = NotificationConfig(
            sales_group_id=self.config.notification_group_id,
            admin_group_id=self.config.notification_group_id,
            enable_sales_notifications=True,
            enable_admin_notifications=True,
            enable_user_notifications=True
        )
        
        bot = Bot(token=self.config.token)
        self.notification_manager = NotificationManager(bot, notification_config, self.db)
        self.broadcast_manager = BroadcastManager(bot, self.db)
        self.user_message_manager = UserMessageManager(bot, self.db)
        logger.info("✅ Notification Managers inicializados")
        
        # Admin Config Manager
        self.admin_config_manager = AdminConfigManager(self.bot_instance, self.db, self.config_file)
        logger.info("✅ Admin Config Manager inicializado")
    
    async def _initialize_webhook(self):
        """Inicializa servidor webhook"""
        try:
            self.webhook_manager = WebhookManager(self.config.webhook_url)
            self.webhook_server = WebhookServer(
                self.bot_instance,
                self.payment_manager,
                self.notification_manager,
                port=5000
            )
            
            # Inicia webhook em thread separada
            self.webhook_thread = self.webhook_server.run_threaded()
            
            webhook_url = self.webhook_manager.get_mercadopago_webhook_url()
            logger.info(f"✅ Webhook server iniciado: {webhook_url}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar webhook: {e}")
    
    def _setup_handlers(self):
        """Configura todos os handlers do bot"""
        # Handlers do bot principal
        self.application.add_handler(CommandHandler("start", self.bot_instance.start_command))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.create_test_callback, pattern="create_test"))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.buy_plan_callback, pattern="^buy_"))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.check_payment_callback, pattern="^check_payment_"))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.my_info_callback, pattern="my_info"))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.admin_panel_callback, pattern="admin_panel"))
        self.application.add_handler(CallbackQueryHandler(self.bot_instance.back_to_menu_callback, pattern="back_to_menu"))
        
        # Handlers de configuração admin
        config_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("config", self.admin_config_manager.start_config)],
            states={
                self.admin_config_manager.CONFIG_MENU: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback)
                ],
                self.admin_config_manager.CONFIG_SERVERS: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_config_manager.handle_text_input)
                ],
                self.admin_config_manager.CONFIG_PAYMENTS: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_config_manager.handle_text_input)
                ],
                self.admin_config_manager.CONFIG_NOTIFICATIONS: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback)
                ],
                self.admin_config_manager.CONFIG_MESSAGES: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.admin_config_manager.handle_text_input)
                ],
                self.admin_config_manager.CONFIG_USERS: [
                    CallbackQueryHandler(self.admin_config_manager.handle_config_callback)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.admin_config_manager.cancel_config)]
        )
        
        self.application.add_handler(config_conv_handler)
        
        # Comandos de configuração rápida
        quick_commands = QuickConfigCommands(self.admin_config_manager)
        self.application.add_handler(CommandHandler("setmptoken", quick_commands.set_mp_token_command))
        self.application.add_handler(CommandHandler("addadmin", quick_commands.add_admin_command))
        self.application.add_handler(CommandHandler("setgroup", quick_commands.set_group_command))
        self.application.add_handler(CommandHandler("status", quick_commands.status_command))
        
        # Comandos adicionais
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("stats", self._stats_command))
        
        logger.info("✅ Handlers configurados")
    
    async def _help_command(self, update, context):
        """Comando de ajuda"""
        if update.effective_user.id in self.config.admin_ids:
            help_text = """
🤖 <b>SSH Bot Premium - Comandos Admin</b>

📋 <b>Comandos Básicos:</b>
/start - Menu principal
/help - Esta ajuda
/stats - Estatísticas do bot

⚙️ <b>Configuração:</b>
/config - Painel de configuração completo
/status - Status da configuração
/setgroup - Define grupo atual como notificações

🔧 <b>Configuração Rápida:</b>
/setmptoken <token> - Define token Mercado Pago
/addadmin <user_id> - Adiciona administrador

💡 <b>Dicas:</b>
• Use /config para configuração completa
• Configure webhook no painel do Mercado Pago
• Teste pagamentos em ambiente sandbox primeiro
            """
        else:
            help_text = """
🤖 <b>SSH Bot Premium</b>

📋 <b>Comandos Disponíveis:</b>
/start - Menu principal
/help - Esta ajuda

💡 <b>Como usar:</b>
1. Digite /start para acessar o menu
2. Crie sua conta SSH de teste grátis
3. Ou adquira um plano premium

💬 <b>Suporte:</b> @proverbiox9
            """
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def _stats_command(self, update, context):
        """Comando de estatísticas"""
        if update.effective_user.id not in self.config.admin_ids:
            await update.message.reply_text("❌ Acesso negado!")
            return
        
        try:
            users = self.db.get_all_users()
            total_users = len(users)
            
            # Estatísticas básicas (implementar contadores reais)
            premium_users = 0  # Implementar contagem real
            sales_today = 0    # Implementar contagem real
            
            stats_text = f"""
📊 <b>ESTATÍSTICAS DO BOT</b>

👥 <b>Usuários:</b>
• Total: {total_users}
• Premium: {premium_users}
• Gratuitos: {total_users - premium_users}

💰 <b>Vendas:</b>
• Hoje: {sales_today}
• Este mês: Em desenvolvimento
• Total: Em desenvolvimento

🖥️ <b>Servidores:</b>
• Configurados: {len(self.config.ssh_servers)}
• Ativos: {len([s for s in self.config.ssh_servers if s.get('active', True)])}

⚙️ <b>Sistema:</b>
• Status: ✅ Online
• Webhook: {'✅ Ativo' if self.webhook_server else '❌ Inativo'}
• Uptime: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """
            
            await update.message.reply_text(stats_text, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao obter estatísticas: {e}")
    
    async def run(self):
        """Executa o bot"""
        try:
            await self.initialize()
            
            # Configura handlers de sinal para shutdown graceful
            def signal_handler(signum, frame):
                logger.info("🛑 Sinal de parada recebido. Finalizando...")
                self.is_running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            self.is_running = True
            
            # Notifica inicialização
            if self.notification_manager:
                await self.notification_manager.notify_system_error(
                    "SISTEMA", 
                    "🚀 SSH Bot Premium iniciado com sucesso!"
                )
            
            logger.info("🚀 SSH Bot Premium v2.0 iniciado com sucesso!")
            logger.info(f"📊 Total de usuários: {len(self.db.get_all_users())}")
            
            # Executa bot
            await self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Finaliza o bot graciosamente"""
        try:
            logger.info("🛑 Finalizando SSH Bot Premium...")
            
            # Para webhook se estiver rodando
            if self.webhook_thread and self.webhook_thread.is_alive():
                logger.info("🛑 Parando servidor webhook...")
                # O webhook server para automaticamente quando a thread principal termina
            
            # Notifica finalização
            if self.notification_manager:
                await self.notification_manager.notify_system_error(
                    "SISTEMA",
                    "🛑 SSH Bot Premium finalizado"
                )
            
            logger.info("✅ Bot finalizado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro durante finalização: {e}")

def main():
    """Função principal"""
    try:
        # Verifica argumentos da linha de comando
        config_file = "config.json"
        if len(sys.argv) > 1:
            config_file = sys.argv[1]
        
        # Cria e executa bot
        bot = IntegratedSSHBot(config_file)
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

