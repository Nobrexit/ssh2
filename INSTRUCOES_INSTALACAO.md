# 🚀 SSH Bot Premium v2.0 - Instruções de Instalação

## 📦 Arquivos Entregues

Você recebeu um sistema completo com os seguintes arquivos:

### 🔧 Arquivos Principais
- `main_bot.py` - Arquivo principal integrado
- `bot_ssh_completo.py` - Bot principal com interface melhorada
- `mercado_pago_integration.py` - Sistema de pagamentos PIX
- `notification_system.py` - Sistema de notificações e mensagens
- `admin_config_system.py` - Configuração via chat
- `webhook_server.py` - Servidor para receber webhooks

### ⚙️ Arquivos de Configuração
- `config.json` - Configurações principais
- `requirements.txt` - Dependências Python
- `.env` - Variáveis de ambiente

### 📜 Scripts de Automação
- `install.sh` - Script de instalação automática
- `start.sh` - Script para iniciar o bot
- `setup.py` - Configuração interativa
- `update.sh` - Script de atualização

### 📚 Documentação
- `README.md` - Documentação completa
- `INSTRUCOES_INSTALACAO.md` - Este arquivo

## 🚀 Instalação Rápida

### Opção 1: Instalação Automática (Recomendada)

```bash
# 1. Torne o script executável
chmod +x install.sh

# 2. Execute a instalação
./install.sh

# 3. Configure o bot
cd ~/ssh-bot-premium
python3 setup.py

# 4. Inicie o bot
./start.sh
```

### Opção 2: Instalação Manual

```bash
# 1. Criar diretório
mkdir ~/ssh-bot-premium
cd ~/ssh-bot-premium

# 2. Copiar todos os arquivos para o diretório

# 3. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar
python3 setup.py

# 6. Iniciar
python3 main_bot.py
```

## ⚙️ Configuração Obrigatória

### 1. Token do Bot Telegram
1. Acesse @BotFather no Telegram
2. Crie um novo bot com `/newbot`
3. Copie o token fornecido
4. Cole no arquivo `config.json` ou use `python3 setup.py`

### 2. Access Token Mercado Pago
1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie o Access Token (sandbox para testes)
4. Cole no arquivo `config.json`

### 3. Configurar Servidor SSH
1. Tenha acesso root ao servidor SSH
2. Configure IP, usuário e senha no `config.json`
3. Teste a conexão SSH manualmente

### 4. Webhook (Opcional mas Recomendado)
1. Configure um domínio público
2. Aponte para o IP do seu servidor na porta 5000
3. Configure no painel do Mercado Pago:
   - URL: `https://seu-dominio.com/webhook/mercadopago`
   - Eventos: `payment`

## 🎯 Primeiros Passos

### 1. Teste Básico
```bash
# Inicie o bot
./start.sh

# No Telegram, envie /start para o bot
# Teste criação de conta SSH gratuita
```

### 2. Configuração Admin
```bash
# No bot, use:
/config          # Painel completo
/setgroup        # No grupo de notificações
/addadmin 123456 # Adicionar outro admin
/status          # Ver status da configuração
```

### 3. Teste de Pagamento
```bash
# 1. Configure token MP em sandbox
# 2. Teste compra de plano no bot
# 3. Use cartão de teste do MP
# 4. Verifique se webhook funciona
```

## 🔧 Funcionalidades Implementadas

### ✅ Sistema de Vendas
- Pagamentos PIX automáticos via Mercado Pago
- QR Code e Copia e Cola
- Verificação automática de status
- Ativação instantânea de premium

### ✅ Sistema de Notificações
- Notificações de vendas em grupo
- Alertas de novos usuários
- Notificações de erros
- Mensagens em massa (broadcast)

### ✅ Painel Administrativo
- Configuração completa via chat
- Gerenciamento de servidores SSH
- Controle de usuários premium
- Estatísticas em tempo real

### ✅ Interface Melhorada
- Design moderno com emojis
- Botões inline intuitivos
- Mensagens informativas
- Navegação fluida

### ✅ Sistema de Usuários
- Usuários gratuitos (limite 24h)
- Usuários premium (ilimitado)
- Controle de acesso
- Histórico de atividades

## 📱 Como Usar

### Para Usuários Finais:
1. `/start` - Menu principal
2. "🆓 TESTE GRÁTIS" - Conta SSH 6h grátis
3. "💎 COMPRAR PREMIUM" - Planos pagos
4. Recebe dados SSH automaticamente

### Para Administradores:
1. `/config` - Painel de configuração
2. Configure servidores, preços, grupos
3. Monitore vendas e usuários
4. Envie mensagens em massa

## 🚨 Solução de Problemas

### Bot não inicia:
```bash
# Verificar token
grep "bot_token" config.json

# Verificar logs
tail -f bot.log

# Reinstalar dependências
pip install -r requirements.txt
```

### Pagamentos não funcionam:
```bash
# Verificar token MP
grep "mercado_pago" config.json

# Testar webhook
curl https://seu-dominio.com/webhook/test

# Verificar logs de pagamento
grep "PAYMENT" bot.log
```

### SSH não cria contas:
```bash
# Testar conexão
ssh root@SEU_SERVIDOR_IP

# Verificar configuração
grep "ssh_servers" config.json

# Verificar logs SSH
grep "SSH" bot.log
```

## 📊 Estrutura de Preços Padrão

- **Plano Semanal:** R$ 10,00 (7 dias)
- **Plano Mensal:** R$ 20,00 (30 dias)
- **Teste Gratuito:** 6 horas (limite 24h)

*Preços configuráveis via `/config` ou `setup.py`*

## 🔒 Segurança

### Tokens e Senhas:
- Nunca compartilhe tokens
- Use ambiente sandbox para testes
- Rotacione senhas periodicamente

### Servidor:
- Configure firewall (portas 22, 5000)
- Use HTTPS para webhook
- Monitore logs regularmente

## 📞 Suporte

### Contato:
- **Telegram:** @proverbiox9
- **Suporte técnico:** Disponível

### Informações para Suporte:
- Versão: SSH Bot Premium v2.0
- Logs: `tail -50 bot.log`
- Config: `config.json` (sem tokens)
- Sistema: `uname -a`

## 🎉 Pronto para Usar!

Seu SSH Bot Premium v2.0 está completo e pronto para uso comercial!

### Características Únicas:
- ✅ Sistema de vendas 100% automático
- ✅ Interface profissional e moderna
- ✅ Notificações em tempo real
- ✅ Configuração via chat
- ✅ Múltiplos servidores SSH
- ✅ Webhook para processamento automático
- ✅ Painel administrativo completo

### Próximos Passos:
1. Configure todos os tokens
2. Teste em ambiente sandbox
3. Configure webhook em produção
4. Divulgue seu bot
5. Monitore vendas e usuários

**Sucesso com seu novo bot! 🚀**

