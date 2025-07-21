#!/bin/bash

# SSH Bot Premium - Instalação Rápida
# Script de instalação com um único comando
# Compatível com Python 3.6+

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar se o comando foi executado com sucesso
check_command() {
    if [ $? -eq 0 ]; then
        print_success "$1"
    else
        print_error "Falha em: $1"
        exit 1
    fi
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SSH Bot Premium v2.0                     ║"
echo "║                   Instalação Automática                     ║"
echo "║                                                              ║"
echo "║  Sistema completo de vendas SSH com pagamentos automáticos  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   print_error "Este script deve ser executado como root (use sudo)"
   exit 1
fi

print_status "Iniciando instalação do SSH Bot Premium..."

# Detectar sistema operacional
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Não foi possível detectar o sistema operacional"
    exit 1
fi

print_status "Sistema detectado: $OS $VER"

# Atualizar sistema
print_status "Atualizando sistema..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt update && apt upgrade -y
    check_command "Atualização do sistema"
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum update -y
    check_command "Atualização do sistema"
else
    print_warning "Sistema não testado, continuando..."
fi

# Instalar dependências básicas
print_status "Instalando dependências básicas..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt install -y curl wget git unzip python3 python3-pip python3-venv build-essential
    check_command "Instalação de dependências básicas"
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    yum install -y curl wget git unzip python3 python3-pip gcc gcc-c++ make
    check_command "Instalação de dependências básicas"
fi

# Verificar versão do Python
print_status "Verificando versão do Python..."
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_status "Python $PYTHON_VERSION detectado"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    print_error "Python 3.6 ou superior é necessário. Versão atual: $PYTHON_VERSION"
    exit 1
fi

print_success "Versão do Python compatível"

# Criar diretório do projeto
PROJECT_DIR="/opt/ssh-bot-premium"
print_status "Criando diretório do projeto: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Baixar arquivos do projeto (simulado - você deve substituir pela URL real)
print_status "Baixando arquivos do projeto..."
if [ -f "/tmp/ssh-bot-premium.zip" ]; then
    cp /tmp/ssh-bot-premium.zip .
    unzip -o ssh-bot-premium.zip
    check_command "Extração dos arquivos do projeto"
else
    print_warning "Arquivo do projeto não encontrado, usando arquivos locais..."
    # Aqui você copiaria os arquivos do projeto
fi

# Criar ambiente virtual
print_status "Criando ambiente virtual Python..."
python3 -m venv venv
check_command "Criação do ambiente virtual"

# Ativar ambiente virtual
source venv/bin/activate
check_command "Ativação do ambiente virtual"

# Atualizar pip
print_status "Atualizando pip..."
pip install --upgrade pip
check_command "Atualização do pip"

# Instalar dependências Python
print_status "Instalando dependências Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    check_command "Instalação das dependências Python"
else
    # Instalar dependências manualmente se requirements.txt não existir
    pip install python-telegram-bot requests flask flask-cors
    check_command "Instalação das dependências Python (manual)"
fi

# Criar arquivo de configuração padrão se não existir
if [ ! -f "config.json" ]; then
    print_status "Criando arquivo de configuração padrão..."
    cat > config.json << EOF
{
  "bot_token": "SEU_TOKEN_DO_BOT_AQUI",
  "mercado_pago_access_token": "SEU_ACCESS_TOKEN_MP_AQUI",
  "admin_ids": [123456789],
  "notification_group_id": -1001234567890,
  "webhook_url": "https://seu-dominio.com",
  "bot_active": true,
  "ssh_servers": [
    {
      "name": "Servidor Principal",
      "ip": "SEU-IP-AQUI",
      "password": "SUA-SENHA-AQUI",
      "port": 22,
      "active": true
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
EOF
    check_command "Criação do arquivo de configuração"
fi

# Criar script de inicialização
print_status "Criando script de inicialização..."
cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/ssh-bot-premium
source venv/bin/activate
python3 main_bot.py
EOF

chmod +x start.sh
check_command "Criação do script de inicialização"

# Criar script de parada
print_status "Criando script de parada..."
cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f "python3 main_bot.py"
echo "Bot parado"
EOF

chmod +x stop.sh
check_command "Criação do script de parada"

# Criar script de status
print_status "Criando script de status..."
cat > status.sh << 'EOF'
#!/bin/bash
if pgrep -f "python3 main_bot.py" > /dev/null; then
    echo "✅ Bot está rodando"
    echo "PID: $(pgrep -f 'python3 main_bot.py')"
else
    echo "❌ Bot não está rodando"
fi
EOF

chmod +x status.sh
check_command "Criação do script de status"

# Criar serviço systemd
print_status "Criando serviço systemd..."
cat > /etc/systemd/system/ssh-bot-premium.service << EOF
[Unit]
Description=SSH Bot Premium
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
check_command "Criação do serviço systemd"

# Configurar firewall (se ufw estiver instalado)
if command -v ufw &> /dev/null; then
    print_status "Configurando firewall..."
    ufw allow 22/tcp
    ufw allow 5000/tcp
    print_success "Firewall configurado"
fi

# Definir permissões
print_status "Definindo permissões..."
chown -R root:root $PROJECT_DIR
chmod +x $PROJECT_DIR/*.py
chmod +x $PROJECT_DIR/*.sh
check_command "Definição de permissões"

# Menu de configuração interativa
print_status "Iniciando configuração interativa..."

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                    CONFIGURAÇÃO INICIAL                     ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configurar token do bot
echo -e "${BLUE}1. Token do Bot Telegram${NC}"
echo "Obtenha seu token em: https://t.me/BotFather"
read -p "Digite o token do bot: " BOT_TOKEN

if [ ! -z "$BOT_TOKEN" ]; then
    sed -i "s/SEU_TOKEN_DO_BOT_AQUI/$BOT_TOKEN/g" config.json
    print_success "Token do bot configurado"
fi

# Configurar token do Mercado Pago
echo ""
echo -e "${BLUE}2. Token do Mercado Pago${NC}"
echo "Obtenha seu token em: https://www.mercadopago.com.br/developers"
read -p "Digite o access token do Mercado Pago: " MP_TOKEN

if [ ! -z "$MP_TOKEN" ]; then
    sed -i "s/SEU_ACCESS_TOKEN_MP_AQUI/$MP_TOKEN/g" config.json
    print_success "Token do Mercado Pago configurado"
fi

# Configurar ID do administrador
echo ""
echo -e "${BLUE}3. ID do Administrador${NC}"
echo "Para obter seu ID, envie /start para @userinfobot"
read -p "Digite seu ID do Telegram: " ADMIN_ID

if [ ! -z "$ADMIN_ID" ]; then
    sed -i "s/123456789/$ADMIN_ID/g" config.json
    print_success "ID do administrador configurado"
fi

# Configurar servidor SSH
echo ""
echo -e "${BLUE}4. Servidor SSH Principal${NC}"
read -p "Digite o IP do servidor SSH: " SSH_IP
read -p "Digite a senha do servidor SSH: " SSH_PASSWORD

if [ ! -z "$SSH_IP" ] && [ ! -z "$SSH_PASSWORD" ]; then
    sed -i "s/SEU-IP-AQUI/$SSH_IP/g" config.json
    sed -i "s/SUA-SENHA-AQUI/$SSH_PASSWORD/g" config.json
    print_success "Servidor SSH configurado"
fi

# Configurar webhook URL
echo ""
echo -e "${BLUE}5. URL do Webhook (opcional)${NC}"
echo "Digite a URL do seu domínio para webhook (ex: https://seudominio.com)"
read -p "URL do webhook (deixe vazio para pular): " WEBHOOK_URL

if [ ! -z "$WEBHOOK_URL" ]; then
    sed -i "s|https://seu-dominio.com|$WEBHOOK_URL|g" config.json
    print_success "URL do webhook configurada"
fi

# Perguntar se deseja iniciar o bot automaticamente
echo ""
echo -e "${BLUE}6. Inicialização Automática${NC}"
read -p "Deseja iniciar o bot automaticamente no boot? (s/n): " AUTO_START

if [[ $AUTO_START == "s" || $AUTO_START == "S" ]]; then
    systemctl enable ssh-bot-premium
    print_success "Inicialização automática habilitada"
fi

# Perguntar se deseja iniciar o bot agora
echo ""
echo -e "${BLUE}7. Iniciar Bot${NC}"
read -p "Deseja iniciar o bot agora? (s/n): " START_NOW

if [[ $START_NOW == "s" || $START_NOW == "S" ]]; then
    print_status "Iniciando o bot..."
    systemctl start ssh-bot-premium
    sleep 3
    
    if systemctl is-active --quiet ssh-bot-premium; then
        print_success "Bot iniciado com sucesso!"
    else
        print_error "Falha ao iniciar o bot. Verifique os logs: journalctl -u ssh-bot-premium"
    fi
fi

# Resumo da instalação
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    INSTALAÇÃO CONCLUÍDA                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📁 Diretório do projeto:${NC} $PROJECT_DIR"
echo -e "${BLUE}🔧 Arquivo de configuração:${NC} $PROJECT_DIR/config.json"
echo -e "${BLUE}📋 Arquivo de log:${NC} $PROJECT_DIR/bot.log"
echo ""
echo -e "${BLUE}🎮 Comandos úteis:${NC}"
echo "  • Iniciar bot:    systemctl start ssh-bot-premium"
echo "  • Parar bot:      systemctl stop ssh-bot-premium"
echo "  • Status do bot:  systemctl status ssh-bot-premium"
echo "  • Ver logs:       journalctl -u ssh-bot-premium -f"
echo "  • Configurar:     cd $PROJECT_DIR && python3 setup.py"
echo ""
echo -e "${BLUE}📱 Scripts auxiliares:${NC}"
echo "  • $PROJECT_DIR/start.sh   - Iniciar manualmente"
echo "  • $PROJECT_DIR/stop.sh    - Parar manualmente"
echo "  • $PROJECT_DIR/status.sh  - Ver status"
echo "  • $PROJECT_DIR/update.sh  - Atualizar bot"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "1. Configure o webhook no painel do Mercado Pago"
echo "2. Teste o bot enviando /start no Telegram"
echo "3. Use /config para configurações avançadas"
echo "4. Mantenha o arquivo config.json seguro"
echo ""
echo -e "${GREEN}✅ SSH Bot Premium instalado com sucesso!${NC}"
echo -e "${BLUE}💬 Suporte: @proverbiox9${NC}"

