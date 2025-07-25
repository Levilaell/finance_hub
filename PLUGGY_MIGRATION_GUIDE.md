# Guia de Migração - Integração Pluggy

Este guia descreve como migrar o sistema atual para a nova arquitetura seguindo a documentação oficial da Pluggy.

## 📋 Resumo das Mudanças

### Backend (Django)
- **Novos Models**: Estrutura completamente nova seguindo os conceitos da Pluggy
- **Novos Endpoints**: API RESTful completa para gerenciamento de Items, Accounts e Transactions
- **Webhooks**: Suporte completo para webhooks da Pluggy
- **Tasks Assíncronas**: Processamento em background com Celery

### Frontend (Next.js)
- **Novos Tipos**: TypeScript types alinhados com a API Pluggy
- **Nova Store**: Zustand store reestruturada
- **Novo Service**: Camada de serviço atualizada
- **Nova UI**: Componentes atualizados com melhor UX

## 🚀 Passos para Migração

### 1. Backend - Preparação

```bash
# Navegue para o diretório backend
cd backend

# Crie backup do banco de dados atual
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

### 2. Backend - Aplicar Nova Estrutura

```bash
# Crie as migrações para os novos models
python manage.py makemigrations banking --name pluggy_integration_v2

# Aplique as migrações
python manage.py migrate banking

# Execute o script de migração de dados
python manage.py shell < apps/banking/migration_script.py
```

### 3. Backend - Atualizar URLs

Edite `backend/apps/banking/urls.py`:
```python
# Importe as novas URLs
from .urls_new import urlpatterns as new_urlpatterns

# Adicione as novas rotas
urlpatterns = new_urlpatterns
```

### 4. Backend - Configurar Celery

Adicione as novas tasks em `backend/apps/banking/tasks.py`:
```python
from .tasks_new import *
```

### 5. Backend - Configurar Webhooks

Configure a URL do webhook no Pluggy Dashboard:
```
https://your-domain.com/api/banking/webhooks/pluggy/
```

### 6. Frontend - Atualizar Tipos

Substitua em todos os arquivos que usam tipos de banking:
```typescript
// Antes
import { BankAccount, Transaction } from '@/types/banking.types';

// Depois
import { BankAccount, Transaction } from '@/types/banking-new.types';
```

### 7. Frontend - Atualizar Services

Substitua em todos os arquivos:
```typescript
// Antes
import { bankingService } from '@/services/banking.service';

// Depois
import { bankingService } from '@/services/banking-new.service';
```

### 8. Frontend - Atualizar Store

Substitua em todos os componentes:
```typescript
// Antes
import { useBankingStore } from '@/store/banking-store';

// Depois
import { useBankingStore } from '@/store/banking-new-store';
```

### 9. Frontend - Atualizar Páginas

Substitua a página de contas:
```bash
# Remova a página antiga
rm frontend/app/\(dashboard\)/accounts/page.tsx

# Renomeie a nova página
mv frontend/app/\(dashboard\)/accounts-new/page.tsx frontend/app/\(dashboard\)/accounts/page.tsx
```

## 🔧 Configurações Necessárias

### Backend - Settings

Adicione em `settings.py`:
```python
# Pluggy Settings
PLUGGY_CLIENT_ID = env('PLUGGY_CLIENT_ID')
PLUGGY_CLIENT_SECRET = env('PLUGGY_CLIENT_SECRET')
PLUGGY_BASE_URL = env('PLUGGY_BASE_URL', default='https://api.pluggy.ai')
PLUGGY_CONNECT_URL = env('PLUGGY_CONNECT_URL', default='https://connect.pluggy.ai')
PLUGGY_USE_SANDBOX = env.bool('PLUGGY_USE_SANDBOX', default=False)
PLUGGY_WEBHOOK_SECRET = env('PLUGGY_WEBHOOK_SECRET', default='')
```

### Frontend - Environment

Adicione em `.env.local`:
```env
# Não são mais necessárias variáveis da Pluggy no frontend
# Toda autenticação é feita pelo backend
```

## 📊 Principais Conceitos da Nova Arquitetura

### 1. PluggyConnector
- Representa um banco/instituição financeira
- Armazena informações sobre capacidades (MFA, OAuth, Open Finance)
- Cache local dos conectores disponíveis

### 2. PluggyItem
- Representa uma conexão ativa com uma instituição
- Gerencia status e ciclo de vida da conexão
- Rastreia erros e necessidade de reautenticação

### 3. BankAccount
- Conta bancária específica dentro de um Item
- Suporta diferentes tipos (BANK, CREDIT, INVESTMENT, etc)
- Armazena saldo e metadados específicos

### 4. Transaction
- Transações financeiras com categorização automática
- Suporte completo para Open Finance
- Metadados ricos (merchant, payment data, etc)

## 🔄 Fluxo de Conexão

1. **Criar Connect Token**: Backend gera token para o widget
2. **Abrir Widget**: Frontend abre Pluggy Connect com o token
3. **Callback**: Backend processa o callback com o item_id
4. **Criar Item/Accounts**: Backend cria registros locais
5. **Sync Inicial**: Task assíncrona busca transações

## 🚨 Pontos de Atenção

### Autenticação
- Tokens são gerenciados apenas pelo backend
- Frontend nunca tem acesso às credenciais da Pluggy

### Sincronização
- Items precisam estar em status UPDATED para sincronizar
- Open Finance tem limites de requisições mensais
- MFA pode ser necessário periodicamente

### Webhooks
- Configure IP whitelist se necessário (177.71.238.212)
- Implemente validação de assinatura em produção
- Processe webhooks de forma assíncrona

## 📝 Checklist de Validação

- [ ] Migrações aplicadas com sucesso
- [ ] Dados antigos migrados corretamente
- [ ] Webhooks configurados e testados
- [ ] Frontend conectando contas com sucesso
- [ ] Sincronização de transações funcionando
- [ ] Categorização automática ativa
- [ ] Tratamento de erros (MFA, login errors)
- [ ] Gerenciamento de consentimento (Open Finance)

## 🐛 Troubleshooting

### Erro: "Invalid credentials"
- Item precisa ser reconectado via widget
- Use o modo "update" do Pluggy Connect

### Erro: "Rate limit exceeded"
- Comum em conectores Open Finance
- Aguarde próximo mês ou delete items não utilizados

### Erro: "Item not ready for sync"
- Aguarde item estar em status UPDATED
- Verifique se MFA é necessário

## 📚 Referências

- [Documentação Pluggy](https://docs.pluggy.ai)
- [Pluggy Connect Guide](https://docs.pluggy.ai/docs/pluggy-connect-introduction)
- [Webhooks Guide](https://docs.pluggy.ai/docs/webhooks)
- [Open Finance Guide](https://docs.pluggy.ai/docs/open-finance-regulated)