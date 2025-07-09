# Caixa Digital - Sistema de Gestão Financeira

Sistema completo de gestão financeira para pequenas e médias empresas brasileiras, com integração Open Banking, categorização por IA e relatórios avançados.

## 🚀 Início Rápido

### Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.11+ (apenas para desenvolvimento local sem Docker)
- Node.js 18+ (apenas para desenvolvimento local sem Docker)

### Instalação com Docker (Recomendado)

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/caixa-digital.git
cd caixa-digital
```

2. Execute o script de configuração rápida:
```bash
./scripts/quick_start.sh
```

Ou use o Makefile:
```bash
make quick-start
```

### URLs de Acesso

Após a instalação, acesse:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **Mailhog (E-mails)**: http://localhost:8025
- **pgAdmin**: http://localhost:5050
- **Redis Commander**: http://localhost:8081

### Credenciais Padrão

- **Admin**: admin@caixadigital.com.br / admin123
- **pgAdmin**: admin@caixadigital.com.br / admin

## 📁 Estrutura do Projeto

```
caixa-digital/
├── backend/                # API Django REST Framework
│   ├── apps/              # Aplicações Django
│   │   ├── authentication/  # Autenticação e 2FA
│   │   ├── banking/        # Integração bancária
│   │   ├── categories/     # Categorização com IA
│   │   ├── companies/      # Multi-tenancy
│   │   ├── notifications/  # Notificações
│   │   ├── payments/       # Pagamentos
│   │   └── reports/        # Relatórios
│   ├── core/              # Configurações Django
│   └── requirements.txt   # Dependências Python
├── frontend/              # Aplicação Next.js
│   ├── app/              # App Router
│   ├── components/       # Componentes React
│   ├── lib/              # Utilitários
│   └── package.json      # Dependências Node
├── nginx/                # Configurações Nginx
├── scripts/              # Scripts auxiliares
└── docker-compose.yml    # Orquestração Docker
```

## 🛠️ Desenvolvimento

### Comandos Úteis

```bash
# Ver logs
make logs
# ou
docker-compose logs -f

# Acessar shell Django
make shell
# ou
docker-compose exec backend python manage.py shell

# Executar migrações
make migrate
# ou
docker-compose exec backend python manage.py migrate

# Criar migrações
make makemigrations
# ou
docker-compose exec backend python manage.py makemigrations

# Executar testes
make test
# ou
docker-compose exec backend python manage.py test

# Parar containers
make down
# ou
docker-compose down
```

### Variáveis de Ambiente

Copie os arquivos de exemplo e configure:

```bash
cp backend/.env.example backend/.env
# Edite backend/.env com suas configurações
```

Principais variáveis:

- `SECRET_KEY`: Chave secreta do Django
- `DB_*`: Configurações do PostgreSQL
- `REDIS_URL`: URL do Redis
- `OPENAI_API_KEY`: Chave da API OpenAI
- `BELVO_*`: Credenciais Belvo (Open Banking)
- `STRIPE_*`: Credenciais Stripe (Pagamentos)

## 🌟 Funcionalidades

### Autenticação
- Login com e-mail
- Autenticação de dois fatores (2FA)
- Recuperação de senha
- Verificação de e-mail

### Gestão Bancária
- Conexão com múltiplas contas bancárias
- Sincronização automática via Open Banking
- Suporte para Belvo e Pluggy
- Tipos de conta: Corrente, Poupança, Empresarial, Digital

### Transações
- Importação automática
- Categorização por IA
- Filtros avançados
- Exportação para CSV/Excel
- Tags e notas personalizadas

### Categorias
- Categorias padrão: Receita, Despesa, Transferência
- Subcategorias personalizáveis
- Regras de categorização automática
- Aprendizado com IA

### Relatórios
- Dashboard financeiro
- Fluxo de caixa
- Análise por categorias
- Tendências e projeções
- Exportação PDF/Excel

### Multi-tenancy
- Múltiplas empresas por usuário
- Convites para equipe
- Controle de permissões
- Dados isolados por empresa

### Assinaturas
- Planos: Inicial, Profissional, Empresarial
- Integração com Stripe e MercadoPago
- Trial de 30 dias
- Upgrades/downgrades automáticos

## 🚀 Deploy em Produção

### Com Docker

1. Configure as variáveis de ambiente:
```bash
cp backend/.env.production.example backend/.env.production
# Edite com suas configurações de produção
```

2. Construa e inicie:
```bash
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

### SSL/HTTPS

O projeto inclui configuração para Certbot/Let's Encrypt:

```bash
# Primeira vez
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email seu@email.com -d caixadigital.com.br -d www.caixadigital.com.br

# Renovação automática já configurada
```

## 🧪 Testes

```bash
# Backend
make test-backend

# Com cobertura
docker-compose exec backend coverage run --source='.' manage.py test
docker-compose exec backend coverage report

# Frontend
docker-compose exec frontend npm test
```

## 📚 Documentação API

A documentação da API está disponível em:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

- Documentação: [docs.caixadigital.com.br](https://docs.caixadigital.com.br)
- E-mail: suporte@caixadigital.com.br
- Issues: [GitHub Issues](https://github.com/seu-usuario/caixa-digital/issues)

## 🏗️ Status do Projeto

- [x] Autenticação e 2FA
- [x] Integração Open Banking
- [x] Categorização por IA
- [x] Multi-tenancy
- [x] Sistema de assinaturas
- [x] Relatórios básicos
- [ ] App mobile
- [ ] Integração fiscal
- [ ] Dashboard avançado com gráficos
- [ ] Previsões financeiras com ML

---

Desenvolvido com ❤️ para o mercado brasileiro