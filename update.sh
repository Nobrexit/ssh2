#!/bin/bash

# SSH Bot Premium - Script de Atualização

set -e

# Cores para output
RED=\'\\033[0;31m\'
GREEN=\'\\033[0;32m\'
YELLOW=\'\\033[1;33m\'
BLUE=\'\\033[0;34m\'
NC=\'\\033[0m\' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   print_error "Este script deve ser executado como root (use sudo)"
   exit 1
fi

PROJECT_DIR="/opt/ssh-bot-premium"

print_status "Iniciando atualização do SSH Bot Premium..."

cd $PROJECT_DIR

# Parar o bot
print_status "Parando o bot..."
systemctl stop ssh-bot-premium || true

# Fazer backup da configuração atual
print_status "Fazendo backup da configuração atual..."
cp config.json config.json.bak

# Baixar a versão mais recente (simulado)
print_status "Baixando a versão mais recente do bot..."
# Em um cenário real, você faria um git pull ou baixaria um novo zip do seu repositório
# Exemplo: git pull origin main
# Para este exemplo, vamos simular a atualização copiando os arquivos do diretório de trabalho

# Copiar arquivos atualizados (simulação)
cp /home/ubuntu/ssh-bot-premium/* . || true

# Restaurar configuração
print_status "Restaurando configuração..."
mv config.json.bak config.json

# Reinstalar dependências (garantir que tudo está atualizado)
print_status "Reinstalando dependências Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install python-telegram-bot requests flask flask-cors

# Reiniciar o bot
print_status "Reiniciando o bot..."
systemctl daemon-reload
systemctl start ssh-bot-premium

print_success "SSH Bot Premium atualizado com sucesso!"
print_status "Verifique o status do bot com: systemctl status ssh-bot-premium"


