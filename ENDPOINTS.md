# Documentação dos Endpoints da API

## Visão Geral

Esta aplicação de gerenciamento financeiro oferece uma API RESTful completa com mais de 85 endpoints organizados em módulos funcionais. A API utiliza autenticação JWT e está documentada através do Swagger/ReDoc.

## Endpoints por Módulo

### 🔐 **Autenticação** (`/api/auth/`)

Gerencia todo o fluxo de autenticação e segurança dos usuários.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/auth/health/` | Verifica se o serviço de autenticação está funcionando |
| POST | `/api/auth/register/` | Registra um novo usuário no sistema |
| POST | `/api/auth/login/` | Realiza login e retorna tokens JWT |
| POST | `/api/auth/logout/` | Invalida a sessão atual do usuário |
| POST | `/api/auth/refresh/` | Atualiza o token JWT expirado |
| GET/PUT | `/api/auth/profile/` | Visualiza ou atualiza o perfil do usuário |
| POST | `/api/auth/change-password/` | Permite alterar a senha atual |
| DELETE | `/api/auth/delete-account/` | Remove permanentemente a conta do usuário |
| POST | `/api/auth/password-reset/` | Solicita reset de senha via email |
| POST | `/api/auth/password-reset/confirm/` | Confirma o reset com o token recebido |
| POST | `/api/auth/verify-email/` | Verifica o email do usuário |
| POST | `/api/auth/resend-verification/` | Reenvia email de verificação |
| POST | `/api/auth/2fa/setup/` | Inicia configuração de autenticação 2FA |
| POST | `/api/auth/2fa/enable/` | Ativa a autenticação de dois fatores |
| POST | `/api/auth/2fa/disable/` | Desativa a autenticação de dois fatores |
| GET | `/api/auth/2fa/backup-codes/` | Obtém códigos de backup para 2FA |

### 🏢 **Empresas** (`/api/companies/`)

Gerencia dados empresariais, assinaturas e equipes.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/companies/public/plans/` | Lista planos disponíveis (sem autenticação) |
| GET | `/api/companies/` | Obtém detalhes da empresa atual |
| GET | `/api/companies/profile/` | Perfil completo da empresa |
| PUT | `/api/companies/update/` | Atualiza informações da empresa |
| GET | `/api/companies/subscription/plans/` | Lista planos de assinatura disponíveis |
| POST | `/api/companies/subscription/upgrade/` | Faz upgrade do plano atual |
| POST | `/api/companies/subscription/cancel/` | Cancela a assinatura |
| GET | `/api/companies/users/` | Lista todos os usuários da empresa |
| POST | `/api/companies/users/invite/` | Envia convite para novo usuário |
| DELETE | `/api/companies/users/<int:user_id>/remove/` | Remove usuário da empresa |
| GET/POST | `/api/companies/billing/payment-methods/` | Gerencia métodos de pagamento |
| GET/PUT/DELETE | `/api/companies/billing/payment-methods/<int:payment_method_id>/` | Operações em método específico |
| GET | `/api/companies/billing/history/` | Histórico de pagamentos |
| GET | `/api/companies/billing/invoices/<int:payment_id>/` | Download de faturas |
| GET | `/api/companies/usage-limits/` | Limites de uso do plano atual |

### 🏦 **Banking** (`/api/banking/`)

Módulo principal para gestão financeira e integração bancária.

#### **Recursos CRUD Completos (ViewSets)**

| Recurso | Endpoint Base | Operações Suportadas |
|---------|---------------|---------------------|
| Contas | `/api/banking/accounts/` | GET, POST, PUT, PATCH, DELETE |
| Transações | `/api/banking/transactions/` | GET, POST, PUT, PATCH, DELETE |
| Categorias | `/api/banking/categories/` | GET, POST, PUT, PATCH, DELETE |
| Provedores | `/api/banking/providers/` | GET, POST, PUT, PATCH, DELETE |
| Orçamentos | `/api/banking/budgets/` | GET, POST, PUT, PATCH, DELETE |

#### **Endpoints Especializados**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/dashboard/` | Dashboard com resumo financeiro básico |
| GET | `/api/banking/dashboard/enhanced/` | Dashboard avançado com métricas detalhadas |
| GET | `/api/banking/analytics/time-series/` | Análise temporal de transações |
| GET | `/api/banking/analytics/expense-trends/` | Tendências e padrões de gastos |
| POST | `/api/banking/sync/<int:account_id>/` | Sincroniza dados de conta específica |
| POST | `/api/banking/connect/` | Conecta nova conta bancária |
| GET | `/api/banking/oauth/callback/` | Callback para autenticação OAuth |
| POST | `/api/banking/refresh-token/<int:account_id>/` | Atualiza token de acesso da conta |

#### **Integração Pluggy**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/pluggy/banks/` | Lista bancos disponíveis para conexão |
| POST | `/api/banking/pluggy/connect-token/` | Gera token para widget de conexão |
| POST | `/api/banking/pluggy/callback/` | Processa callback após conexão |
| POST | `/api/banking/pluggy/accounts/<int:account_id>/sync/` | Sincroniza dados via Pluggy |
| POST | `/api/banking/pluggy/accounts/<int:account_id>/disconnect/` | Desconecta conta do Pluggy |
| GET | `/api/banking/pluggy/accounts/<int:account_id>/status/` | Status da conexão |
| POST | `/api/banking/pluggy/webhook/` | Recebe notificações do Pluggy |

### 📊 **Relatórios** (`/api/reports/`)

Sistema de relatórios e análises financeiras.

#### **Recursos CRUD**

| Recurso | Endpoint Base | Descrição |
|---------|---------------|-----------|
| Relatórios | `/api/reports/reports/` | Gerenciamento de relatórios salvos |
| Agendamentos | `/api/reports/schedules/` | Agendamento de relatórios recorrentes |
| Templates | `/api/reports/templates/` | Templates de relatórios personalizados |

#### **Análises e Dashboards**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/reports/quick/` | Relatórios rápidos pré-definidos |
| GET | `/api/reports/analytics/` | Análises financeiras gerais |
| GET | `/api/reports/dashboard/stats/` | Estatísticas resumidas |
| GET | `/api/reports/dashboard/cash-flow/` | Dados de fluxo de caixa |
| GET | `/api/reports/dashboard/category-spending/` | Gastos organizados por categoria |
| GET | `/api/reports/dashboard/income-vs-expenses/` | Comparativo receitas x despesas |
| GET | `/api/reports/ai-insights/` | Insights gerados por IA |

### 🔔 **Notificações** (`/api/notifications/`)

Sistema de notificações e alertas.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/notifications/` | Lista todas as notificações do usuário |
| POST | `/api/notifications/<int:notification_id>/read/` | Marca notificação como lida |
| POST | `/api/notifications/mark-all-read/` | Marca todas como lidas |
| GET | `/api/notifications/count/` | Conta notificações não lidas |
| GET | `/api/notifications/preferences/` | Obtém preferências de notificação |
| PUT | `/api/notifications/preferences/update/` | Atualiza preferências |
| GET | `/api/notifications/websocket/health/` | Status da conexão WebSocket |

### 💳 **Pagamentos** (`/api/payments/`)

Integração com gateways de pagamento.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/payments/checkout/create/` | Cria sessão de checkout |
| POST | `/api/payments/checkout/validate/` | Valida pagamento realizado |
| GET | `/api/payments/subscription-status/` | Status atual da assinatura |
| POST | `/api/payments/webhooks/stripe/` | Webhook para eventos do Stripe |
| POST | `/api/payments/webhooks/mercadopago/` | Webhook para MercadoPago |

### 📚 **Documentação e Admin**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Página inicial da API |
| GET | `/api/` | Lista de endpoints disponíveis |
| GET | `/swagger/` | Interface interativa Swagger UI |
| GET | `/swagger.json` | Schema da API em formato JSON |
| GET | `/swagger.yaml` | Schema da API em formato YAML |
| GET | `/redoc/` | Documentação ReDoc |
| ALL | `/admin/` | Interface administrativa Django |

## Autenticação

A API utiliza autenticação baseada em JWT (JSON Web Tokens):

1. **Login**: Envie credenciais para `/api/auth/login/` para receber os tokens
2. **Headers**: Inclua o token em todas as requisições: `Authorization: Bearer <token>`
3. **Refresh**: Use `/api/auth/refresh/` quando o token expirar

## Limites de Taxa (Rate Limiting)

- **Autenticação**: 10 requisições por minuto
- **API Geral**: 100 requisições por minuto
- **Webhooks**: Sem limite

## Códigos de Status

- **200 OK**: Requisição bem-sucedida
- **201 Created**: Recurso criado com sucesso
- **400 Bad Request**: Dados inválidos
- **401 Unauthorized**: Token ausente ou inválido
- **403 Forbidden**: Sem permissão para o recurso
- **404 Not Found**: Recurso não encontrado
- **429 Too Many Requests**: Limite de requisições excedido
- **500 Internal Server Error**: Erro no servidor

## Exemplos de Uso

### Autenticação
```bash
# Login
curl -X POST http://api.exemplo.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@exemplo.com", "password": "senha123"}'

# Resposta
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q...",
  "user": {
    "id": 1,
    "email": "usuario@exemplo.com",
    "name": "Nome do Usuário"
  }
}
```

### Listar Transações
```bash
curl -X GET http://api.exemplo.com/api/banking/transactions/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..."
```

### Criar Orçamento
```bash
curl -X POST http://api.exemplo.com/api/banking/budgets/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alimentação",
    "amount": 1500.00,
    "period": "monthly"
  }'
```

## Suporte

Para mais informações ou suporte:
- Documentação interativa: `/swagger/`
- Email: suporte@exemplo.com
- Status da API: `/api/auth/health/`