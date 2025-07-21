# 🚀 SSH Bot Premium v2.0

Sistema completo de vendas SSH com pagamentos automáticos via PIX, notificações em tempo real e painel administrativo avançado.

## 📋 Índice

- [Características](#-características)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#️-instalação)
- [Configuração](#️-configuração)
- [Uso](#-uso)
- [Comandos](#-comandos)
- [API e Webhooks](#-api-e-webhooks)
- [Manutenção](#-manutenção)
- [Troubleshooting](#-troubleshooting)
- [Suporte](#-suporte)

## 🌟 Características

### 💳 Sistema de Pagamentos
- ✅ Integração completa com Mercado Pago
- ✅ Pagamentos PIX automáticos
- ✅ QR Code e Copia e Cola
- ✅ Verificação automática de status
- ✅ Ativação instantânea após pagamento

### 🔔 Sistema de Notificações
- ✅ Notificações de vendas em tempo real
- ✅ Alertas de novos usuários
- ✅ Notificações de erros do sistema
- ✅ Mensagens em massa (broadcast)
- ✅ Mensagens personalizadas

### ⚙️ Painel Administrativo
- ✅ Configuração via chat do bot
- ✅ Gerenciamento de servidores SSH
- ✅ Controle de usuários e premium
- ✅ Estatísticas em tempo real
- ✅ Sistema de relatórios

### 🖥️ Gerenciamento SSH
- ✅ Múltiplos servidores
- ✅ Criação automática de contas
- ✅ Controle de expiração
- ✅ Balanceamento de carga
- ✅ Monitoramento de status

### 👥 Sistema de Usuários
- ✅ Usuários gratuitos (limite 24h)
- ✅ Usuários premium (ilimitado)
- ✅ Controle de acesso
- ✅ Histórico de atividades
- ✅ Sistema de banimento

## 📋 Pré-requisitos

### Sistema
- **SO:** Linux (Ubuntu 18.04+ recomendado)
- **Python:** 3.6 ou superior
- **Memória:** Mínimo 512MB RAM
- **Disco:** Mínimo 1GB livre

## 🛠️ Instalação

### Instalação Automática (Recomendada)

Execute o script de instalação com um único comando. Ele irá instalar as dependências, configurar o ambiente, e iniciar o bot:

```bash
# Download e execução do script de instalação
curl -sSL https://raw.githubusercontent.com/seu-repo/quick_install.sh | bash
```

Após a instalação, o script irá guiá-lo pela configuração inicial e iniciará o bot automaticamente.

## ⚙️ Configuração

### 1. Configuração Inicial

Após a instalação, o script de instalação irá guiá-lo pela configuração inicial do bot, solicitando as informações necessárias como token do bot, token do Mercado Pago, ID do administrador, etc.

### 2. Arquivo de Configuração

O arquivo `config.json` contém todas as configurações:
```json
{
  "bot_token": "SEU_TOKEN_AQUI",
  "mercado_pago_access_token": "SEU_ACCESS_TOKEN_AQUI",
  "admin_ids": [123456789],
  "notification_group_id": -1001234567890,
  "webhook_url": "https://seu-dominio.com",
  "ssh_servers": [
    {
      "name": "Servidor Principal",
      "ip": "192.168.1.100",
      "password": "senha123",
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
  }
}
```

### 3. Configuração do Webhook

Para receber notificações automáticas do Mercado Pago:

1. **Configure no painel do MP:**
   - URL: `https://seu-dominio.com/webhook/mercadopago`
   - Eventos: `payment`

2. **Teste o webhook:**
   ```bash
   curl https://seu-dominio.com/webhook/test
   ```

### 4. Grupos de Notificação

1. Crie um grupo no Telegram
2. Adicione o bot ao grupo
3. Use `/setgroup` no grupo
4. O bot configurará automaticamente

## 🎮 Uso

### Iniciando o Bot

```bash
# Método 1: Script de inicialização
./start.sh

# Método 2: Execução direta
source venv/bin/activate
python3 main_bot.py

# Método 3: Como serviço (systemd)
sudo systemctl start ssh-bot-premium
```

### Fluxo de Uso

#### Para Usuários Finais:
1. `/start` - Acessa o menu principal
2. "🆓 TESTE GRÁTIS" - Cria conta SSH de 6h
3. "💎 COMPRAR PREMIUM" - Escolhe plano e paga
4. Recebe dados SSH automaticamente

#### Para Administradores:
1. `/config` - Acessa painel administrativo
2. Configura servidores, preços, etc.
3. Monitora vendas e usuários
4. Envia mensagens em massa

## 📱 Comandos

### Comandos Públicos

| Comando | Descrição |
|---------|-----------|
| `/start` | Menu principal do bot |
| `/help` | Ajuda e informações |

### Comandos Administrativos

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/config` | Painel de configuração completo | `/config` |
| `/status` | Status da configuração atual | `/status` |
| `/stats` | Estatísticas do bot | `/stats` |
| `/setgroup` | Define grupo atual como notificações | `/setgroup` |
| `/addadmin` | Adiciona novo administrador | `/addadmin 123456789` |
| `/setmptoken` | Define token do Mercado Pago | `/setmptoken TEST-123...` |

### Callbacks Inline

O bot utiliza botões inline para navegação:
- `create_test` - Criar teste SSH
- `buy_weekly` - Comprar plano semanal
- `buy_monthly` - Comprar plano mensal
- `check_payment_*` - Verificar pagamento
- `my_info` - Informações do usuário
- `admin_panel` - Painel administrativo

## 🔌 API e Webhooks

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/webhook/mercadopago` | POST | Recebe notificações do MP |
| `/webhook/test` | GET/POST | Teste de webhook |
| `/health` | GET | Health check |
| `/stats` | GET | Estatísticas básicas |

### Estrutura do Webhook MP

```json
{
  "id": 12345,
  "live_mode": true,
  "type": "payment",
  "date_created": "2023-01-01T00:00:00.000Z",
  "application_id": 123456789,
  "user_id": 123456789,
  "version": 1,
  "api_version": "v1",
  "action": "payment.updated",
  "data": {
    "id": "payment_id_here"
  }
}
```

### Testando Webhooks

```bash
# Teste básico
curl -X GET https://seu-dominio.com/webhook/test

# Teste com dados
curl -X POST https://seu-dominio.com/webhook/mercadopago \
  -H "Content-Type: application/json" \
  -d '{"type":"payment","data":{"id":"123456"}}'
```

## 🔧 Manutenção

### Logs

```bash
# Ver logs em tempo real
tail -f bot.log

# Ver logs específicos
grep "ERROR" bot.log
grep "PAYMENT" bot.log

# Rotacionar logs
mv bot.log bot.log.old
```

### Backup

```bash
# Backup completo
tar -czf backup-$(date +%Y%m%d).tar.gz \
  config.json \
  bot_database.db \
  bot.log

# Backup automático (crontab)
0 2 * * * cd /home/user/ssh-bot-premium && ./backup.sh
```

### Atualização

```bash
# Atualizar dependências
./update.sh

# Atualizar código
git pull origin main
pip install -r requirements.txt
```

### Monitoramento

```bash
# Status do processo
ps aux | grep main_bot.py

# Uso de recursos
htop

# Conexões de rede
netstat -tulpn | grep :5000

# Espaço em disco
df -h
```

## 🚨 Troubleshooting

### Problemas Comuns

#### Bot não inicia
```bash
# Verificar token
grep "bot_token" config.json

# Verificar dependências
pip list | grep telegram

# Verificar logs
tail -20 bot.log
```

#### Pagamentos não funcionam
```bash
# Verificar token MP
grep "mercado_pago" config.json

# Testar API MP
curl -H "Authorization: Bearer SEU_TOKEN" \
  https://api.mercadopago.com/v1/payment_methods

# Verificar webhook
curl https://seu-dominio.com/webhook/test
```

#### SSH não cria contas
```bash
# Testar conexão SSH
ssh root@SEU_SERVIDOR_IP

# Verificar configuração
grep "ssh_servers" config.json

# Verificar logs de SSH
grep "SSH" bot.log
```

### Códigos de Erro

| Código | Descrição | Solução |
|--------|-----------|---------|
| `TOKEN_INVALID` | Token do bot inválido | Verificar token no @BotFather |
| `MP_TOKEN_INVALID` | Token MP inválido | Verificar token no painel MP |
| `SSH_CONNECTION_FAILED` | Falha na conexão SSH | Verificar IP/senha do servidor |
| `WEBHOOK_ERROR` | Erro no webhook | Verificar URL e conectividade |
| `DATABASE_ERROR` | Erro no banco de dados | Verificar permissões do arquivo |

### Logs de Debug

Para ativar logs detalhados:

```python
# No arquivo main_bot.py
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Estrutura do Projeto

```
ssh-bot-premium/
├── main_bot.py                 # Arquivo principal
├── bot_ssh_completo.py         # Bot principal
├── mercado_pago_integration.py # Integração MP
├── notification_system.py      # Sistema de notificações
├── admin_config_system.py      # Configuração admin
├── webhook_server.py           # Servidor webhook
├── config.json                 # Configurações
├── requirements.txt            # Dependências

├── quick_install.sh            # Script de instalação rápida (tudo em um)
├── bot_database.db             # Banco de dados SQLite
├── bot.log                     # Arquivo de logs
└── README.md                   # Esta documentação
```

## 🔒 Segurança

### Boas Práticas

1. **Tokens e Senhas:**
   - Nunca commite tokens no Git
   - Use variáveis de ambiente
   - Rotacione tokens periodicamente

2. **Servidor:**
   - Use HTTPS para webhook
   - Configure firewall adequadamente
   - Mantenha sistema atualizado

3. **SSH:**
   - Use senhas fortes
   - Configure fail2ban
   - Monitore logs de acesso

4. **Bot:**
   - Limite comandos admin
   - Valide entrada de usuários
   - Monitore atividades suspeitas

### Configuração de Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # Webhook
sudo ufw enable

# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## 📈 Performance

### Otimizações

1. **Banco de Dados:**
   - Índices nas consultas frequentes
   - Limpeza periódica de dados antigos
   - Backup regular

2. **Webhook:**
   - Rate limiting
   - Queue para processamento
   - Timeout adequado

3. **Bot:**
   - Pool de conexões
   - Cache de configurações
   - Processamento assíncrono

### Monitoramento

```bash
# CPU e Memória
top -p $(pgrep -f main_bot.py)

# Conexões de rede
ss -tulpn | grep python

# Tamanho do banco
ls -lh bot_database.db
```

## 🆘 Suporte

### Canais de Suporte

- **Telegram:** @proverbiox9
- **Email:** suporte@seudominio.com
- **GitHub Issues:** Para bugs e melhorias

### Informações para Suporte

Ao solicitar suporte, inclua:

1. **Versão do bot:** `v2.0`
2. **Sistema operacional:** `uname -a`
3. **Versão Python:** `python3 --version`
4. **Logs relevantes:** Últimas 50 linhas
5. **Configuração:** `config.json` (sem tokens)
6. **Descrição do problema:** Detalhada

### FAQ

**P: O bot não responde aos comandos**
R: Verifique se o token está correto e se o bot está online.

**P: Pagamentos não são processados automaticamente**
R: Verifique se o webhook está configurado corretamente no Mercado Pago.

**P: Como adicionar mais servidores SSH?**
R: Use `/config` → Servidores → Adicionar Servidor.

**P: Como fazer backup dos dados?**
R: Copie os arquivos `config.json` e `bot_database.db`.

**P: O bot consome muita memória**
R: Reinicie o bot periodicamente ou configure um cron job.

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

**Uso Comercial:** Permitido apenas com licença válida.
**Redistribuição:** Proibida sem autorização expressa.
**Modificação:** Permitida para uso próprio.

## 🎯 Roadmap

### v2.1 (Próxima versão)
- [ ] Dashboard web administrativo
- [ ] API REST completa
- [ ] Integração com outros gateways
- [ ] Sistema de afiliados
- [ ] Relatórios avançados

### v2.2 (Futuro)
- [ ] Suporte a múltiplas moedas
- [ ] Sistema de cupons
- [ ] Integração com Discord
- [ ] App mobile administrativo
- [ ] IA para suporte automático

## 🙏 Agradecimentos

- **Telegram Bot API:** Pela excelente documentação
- **Mercado Pago:** Pela API robusta de pagamentos
- **Comunidade Python:** Pelas bibliotecas utilizadas
- **Beta Testers:** Pelos feedbacks valiosos

---

**SSH Bot Premium v2.0** - Sistema completo de vendas SSH
Desenvolvido com ❤️ para a comunidade brasileira.

*Última atualização: Janeiro 2025*



### Atualização do Bot

Para atualizar o bot para a versão mais recente, execute o seguinte comando no diretório do projeto:

```bash
sudo /opt/ssh-bot-premium/update.sh
```

Este script irá parar o bot, fazer backup da sua configuração, baixar as atualizações, reinstalar as dependências e reiniciar o bot.


