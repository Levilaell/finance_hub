# Relatório de Código Não Utilizado - App Companies

## Resumo Executivo
A app `companies` apresenta várias oportunidades de limpeza de código. A análise identificou campos, métodos, imports e componentes não utilizados ou potencialmente desnecessários.

## 1. Código Não Utilizado

### 1.1 Models (`models.py`)

#### Campo `BILLING_PERIODS` não utilizado
- **Localização**: `models.py:22-25`
- **Tipo**: Constante de classe
- **Status**: Não utilizado - apenas definido, nunca referenciado
- **Recomendação**: Remover completamente

#### Campo `plan_type` pouco utilizado
- **Localização**: `models.py:30`
- **Tipo**: Campo do modelo SubscriptionPlan
- **Status**: Usado apenas no admin e decorators, mas sem lógica real
- **Recomendação**: Avaliar necessidade real ou remover

#### Campos Stripe não implementados
- **Localização**: `models.py:41-42`
- **Campos**: `stripe_price_id_monthly`, `stripe_price_id_yearly`
- **Status**: Definidos mas não há integração Stripe implementada
- **Recomendação**: Remover até implementação real do Stripe

### 1.2 Views (`views.py`)

Todas as views estão sendo utilizadas e mapeadas corretamente em `urls.py`.

### 1.3 Serializers (`serializers.py`)

#### Serializers potencialmente desnecessários
- **`UsageLimitsSerializer`** (linha 52-55): Usado apenas para validação de response, poderia ser removido
- **`SubscriptionStatusSerializer`** (linha 58-65): Similar ao acima, validação poderia ser inline

### 1.4 Signals (`signals.py`)

#### Arquivo praticamente vazio
- **Status**: Contém apenas imports não utilizados e comentários
- **Recomendação**: Remover arquivo completamente até necessidade real

### 1.5 Middleware (`middleware.py`)

#### `PlanLimitsMiddleware` não registrado
- **Localização**: `middleware.py:140-168`
- **Status**: Definido mas NÃO registrado em settings
- **Impacto**: Código morto - nunca executado
- **Recomendação**: Remover ou registrar se necessário

### 1.6 Decorators (`decorators.py`)

#### `requires_plan_feature` não utilizado
- **Localização**: `decorators.py:6-65`
- **Status**: Definido mas não importado/usado em nenhum lugar
- **Recomendação**: Remover completamente

### 1.7 Permissions (`permissions.py`)

#### Permissions não utilizadas
- **Status**: `CompanyOwnerPermission`, `IsCompanyOwner`, `IsCompanyOwnerOrStaff` não são usados
- **Impacto**: Código morto
- **Recomendação**: Remover arquivo completamente

### 1.8 Admin (`admin.py`)

#### Métodos potencialmente desnecessários
- **`subscription_details`** (linha 220-238): Informação redundante
- **`usage_statistics`** (linha 240-252): Parcialmente implementado
- **`bank_accounts_info`** (linha 254-267): Poderia ser simplificado

## 2. Imports Não Utilizados

### 2.1 `models.py`
- `from datetime import timedelta` - linha 4 (usado apenas no save())
- `logging` - configurado mas não usado efetivamente

### 2.2 `signals.py`
- Todos os imports (arquivo deve ser removido)

### 2.3 `decorators.py`
- `from functools import wraps` - usado mas arquivo inteiro não é necessário

### 2.4 `middleware.py`
- `from django.core.cache import cache` - usado apenas em rate limiting que parece temporário

## 3. Código Redundante ou Simplificável

### 3.1 Validações duplicadas
- `CompanyValidationMixin` em `mixins.py` replica lógica que poderia usar permissions
- Verificações de trial em múltiplos lugares (middleware e models)

### 3.2 Lógica complexa desnecessária
- Admin tem muitos métodos de display que poderiam ser properties do modelo
- Middleware `TrialExpirationMiddleware` tem muita lógica que poderia estar em managers

## 4. Estimativa de Impacto

### Linhas de código que podem ser removidas:
- `signals.py`: ~12 linhas
- `permissions.py`: ~72 linhas
- `decorators.py`: ~65 linhas
- `PlanLimitsMiddleware`: ~29 linhas
- Campos não utilizados em models: ~10 linhas
- **Total**: ~188 linhas (aproximadamente 13% do código da app)

## 5. Plano de Ação Recomendado

### Prioridade Alta (remover imediatamente):
1. ✅ Arquivo `signals.py` completamente
2. ✅ Arquivo `permissions.py` completamente
3. ✅ Arquivo `decorators.py` completamente
4. ✅ `PlanLimitsMiddleware` em `middleware.py`
5. ✅ Campo `BILLING_PERIODS` em `models.py`

### Prioridade Média (avaliar e remover):
1. ⚠️ Campos Stripe em `models.py` (se não há planos de integração imediata)
2. ⚠️ Campo `plan_type` (verificar se há requisito de negócio)
3. ⚠️ Serializers de validação desnecessários

### Prioridade Baixa (refatorar quando possível):
1. 🔄 Mover lógica de display do admin para properties do modelo
2. 🔄 Consolidar validações de company em um único lugar
3. 🔄 Simplificar middleware de trial

## 6. Riscos e Considerações

### Antes de remover:
1. **Verificar migrations**: Remover campos de modelo requer nova migration
2. **Verificar testes**: Garantir que não há testes dependendo deste código
3. **Verificar frontend**: Confirmar que frontend não espera campos que serão removidos
4. **Backup**: Fazer backup ou criar branch antes das mudanças

### Código que parece não usado mas É usado:
- `TrialExpirationMiddleware`: Registrado em development.py, MANTER
- `CompanyValidationMixin`: Usado em views.py e banking/views.py, MANTER

## 7. Comandos para Limpeza

```bash
# Remover arquivos não utilizados
rm backend/apps/companies/signals.py
rm backend/apps/companies/permissions.py
rm backend/apps/companies/decorators.py

# Verificar imports não utilizados com flake8
flake8 backend/apps/companies/ --select=F401

# Verificar código não alcançável
python -m pytest --cov=apps.companies --cov-report=html
```

## Conclusão

A app `companies` tem aproximadamente **13% de código morto** que pode ser removido com segurança. A remoção deste código:
- Reduzirá a complexidade de manutenção
- Melhorará a legibilidade
- Eliminará possíveis pontos de confusão
- Reduzirá o tamanho do projeto

**Recomendação final**: Proceder com a limpeza seguindo o plano de prioridades, começando pelos arquivos completamente não utilizados.