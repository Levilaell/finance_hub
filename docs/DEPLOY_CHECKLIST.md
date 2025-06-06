# 📋 Checklist de Deploy para Produção

## 🔧 Infraestrutura Necessária

### 1. **Servidor/Cloud** 
- [ ] AWS EC2 / DigitalOcean / Google Cloud
- [ ] Mínimo: 2 vCPUs, 4GB RAM
- [ ] Ubuntu 22.04 LTS

### 2. **Domínio e SSL**
- [ ] Domínio registrado
- [ ] Certificado SSL (Let's Encrypt)
- [ ] Configurar DNS

### 3. **Banco de Dados**
- [ ] PostgreSQL 15+ (RDS ou instalado)
- [ ] Backups automáticos configurados
- [ ] Replicação (opcional)

### 4. **Redis**
- [ ] Redis 7+ (ElastiCache ou instalado)
- [ ] Persistência configurada
- [ ] Senha forte

### 5. **Storage**
- [ ] AWS S3 ou equivalente para arquivos
- [ ] CDN para assets estáticos (CloudFront)

## 📝 Configurações de Produção

### 1. **Variáveis de Ambiente**
```bash
# Copiar .env.example e configurar todas as variáveis
cp backend/.env.example backend/.env.production
```

### 2. **Segurança Django**
- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` única e segura
- [ ] `ALLOWED_HOSTS` configurado
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativado

### 3. **Integração Open Banking**
- [ ] Credenciais reais da API bancária
- [ ] Certificados de segurança
- [ ] Webhooks configurados

### 4. **Monitoramento**
- [ ] Sentry configurado
- [ ] Logs centralizados
- [ ] Alertas configurados
- [ ] Health checks

## 🚀 Deploy

### Opção 1: Docker (Recomendado)
```bash
# Build e deploy
docker-compose -f docker-compose.production.yml up -d

# Executar migrações
docker-compose exec backend python manage.py migrate

# Coletar arquivos estáticos
docker-compose exec backend python manage.py collectstatic --noinput

# Criar superusuário
docker-compose exec backend python manage.py createsuperuser
```

### Opção 2: Deploy Manual
```bash
# No servidor
git clone https://github.com/seu-usuario/finance_management.git
cd finance_management/backend

# Instalar dependências
pip install -r requirements.txt

# Configurar nginx
sudo cp nginx/nginx.conf /etc/nginx/sites-available/caixadigital
sudo ln -s /etc/nginx/sites-available/caixadigital /etc/nginx/sites-enabled/

# Configurar systemd
sudo cp scripts/caixadigital.service /etc/systemd/system/
sudo systemctl enable caixadigital
sudo systemctl start caixadigital

# SSL com Let's Encrypt
sudo certbot --nginx -d api.seu-dominio.com
```

## 🔒 Segurança Adicional

### 1. **Firewall**
```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 2. **Fail2ban**
```bash
sudo apt install fail2ban
# Configurar para Django/Nginx
```

### 3. **Backups**
```bash
# Agendar backup diário
0 2 * * * /scripts/backup.sh
```

## 📊 Testes Pré-Deploy

### 1. **Testes Automatizados**
```bash
cd backend
python manage.py test
```

### 2. **Checklist Manual**
- [ ] Login/Logout funcionando
- [ ] Criação de conta bancária
- [ ] Sincronização bancária
- [ ] Geração de relatórios
- [ ] Notificações email
- [ ] WebSockets funcionando
- [ ] 2FA funcionando

## 🎯 Pós-Deploy

### 1. **Monitoramento Inicial**
- [ ] Verificar logs por 24h
- [ ] Testar todas as funcionalidades
- [ ] Monitorar performance
- [ ] Verificar backups

### 2. **Documentação**
- [ ] Atualizar README com URL de produção
- [ ] Documentar processo de deploy
- [ ] Criar runbook para incidentes

## 💰 Custos Estimados (Mensal)

### AWS
- EC2 t3.medium: ~$30
- RDS PostgreSQL: ~$25
- ElastiCache Redis: ~$15
- S3 + CloudFront: ~$10
- **Total: ~$80/mês**

### DigitalOcean
- Droplet 4GB: $24
- Managed Database: $15
- Spaces (S3): $5
- **Total: ~$44/mês**

## 🚨 Contatos de Emergência

- **DevOps**: seu-email@example.com
- **DBA**: dba@example.com
- **Suporte AWS/DO**: [links]

## 📅 Cronograma Sugerido

1. **Semana 1**: Configurar infraestrutura
2. **Semana 2**: Deploy e testes
3. **Semana 3**: Monitoramento e ajustes
4. **Semana 4**: Go-live com usuários beta