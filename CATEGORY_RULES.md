# Categorização Automática por Padrão de Transação

Sistema inteligente de categorização que aprende com as escolhas do usuário e aplica automaticamente a transações similares.

## Funcionalidade

Ao categorizar uma transação manualmente, o sistema:

1. **Busca transações similares** - Por merchant, prefixo ou similaridade fuzzy
2. **Mostra modal com preview** - Lista transações encontradas com checkboxes
3. **Aplica em lote** - Categoria aplicada às transações selecionadas
4. **Cria regra automática** - Opção de categorizar transações futuras automaticamente

---

## Arquitetura

### Backend

#### Model: CategoryRule

```python
class CategoryRule(models.Model):
    pattern = models.CharField(max_length=200)      # Padrão de texto
    match_type = models.CharField(...)              # 'prefix' | 'contains' | 'fuzzy'
    category = models.ForeignKey(Category)          # Categoria a aplicar
    is_active = models.BooleanField(default=True)   # Permite desativar
    applied_count = models.IntegerField(default=0)  # Contador de uso
```

#### Service: CategoryRuleService

| Método | Descrição |
|--------|-----------|
| `normalize_text()` | Remove acentos, lowercase, strip |
| `find_similar_transactions()` | Algoritmo de similaridade 3 níveis |
| `create_rule_from_transaction()` | Cria regra a partir de transação |
| `apply_rules_to_transaction()` | Aplica regras a novas transações |

**Algoritmo de Similaridade:**
1. **Merchant match** (score: 1.0) - Mesmo `merchant_name`
2. **Prefix match** (score: 0.9) - Prefixo comum >= 8 caracteres
3. **Fuzzy match** (score: variável) - Similaridade >= 70%

#### Correção no Sync

O sync de transações agora:
- Preserva `user_category` existente (não sobrescreve categorizações manuais)
- Aplica CategoryRules a transações novas antes do fallback Pluggy

#### API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/banking/transactions/{id}/similar/` | GET | Lista transações similares |
| `/api/banking/transactions/{id}/` | PATCH | Atualiza com opções extras |
| `/api/banking/category-rules/` | GET | Lista regras do usuário |
| `/api/banking/category-rules/` | POST | Cria nova regra |
| `/api/banking/category-rules/{id}/` | PATCH | Atualiza regra |
| `/api/banking/category-rules/{id}/` | DELETE | Remove regra |

**PATCH /transactions/{id}/ - Campos extras:**
```json
{
  "user_category_id": "uuid",
  "apply_to_similar": true,
  "create_rule": true,
  "similar_transaction_ids": ["uuid1", "uuid2"]
}
```

### Frontend

#### CategoryConfirmModal

Modal que aparece ao categorizar uma transação:
- Lista transações similares com checkboxes (pré-selecionadas)
- Mostra tipo de match e % de similaridade
- Toggle "Criar regra para futuras transações"
- Botões: Cancelar | Aplicar só nesta | Aplicar + criar regra

#### Transactions Page

- Integração do modal ao selecionar categoria
- Atualização local das transações afetadas
- Se não houver similares, aplica direto sem modal

#### Settings > Automação

Nova seção "Regras de Categorização Automática":
- Lista todas as regras criadas
- Mostra: padrão, tipo de match, categoria, contador de aplicações
- Toggle para ativar/desativar regra
- Botão para excluir regra

---

## Como Testar

### 1. Aplicar Migration

```bash
cd backend
python manage.py migrate banking
```

### 2. Testar Fluxo Básico

1. Acesse `/transactions`
2. Escolha uma transação não categorizada (ex: "UBER TRIP 123")
3. Selecione uma categoria (ex: "Transporte")
4. Modal deve aparecer se houver transações similares
5. Verifique que transações como "UBER TRIP 456" aparecem na lista
6. Marque "Criar regra para futuras transações"
7. Clique "Aplicar"
8. Verifique que categoria foi aplicada às transações selecionadas

### 3. Testar Regra Automática

1. Acesse `/settings` > aba "Automação"
2. Verifique que a regra criada aparece na lista
3. Execute um sync de transações (ou aguarde webhook)
4. Novas transações com padrão similar devem receber a categoria automaticamente
5. Contador `applied_count` incrementa a cada aplicação

### 4. Testar Gerenciamento de Regras

1. **Desativar regra:** Toggle na lista
   - Sync não aplica mais a regra
   - Transações já categorizadas mantêm categoria

2. **Reativar regra:** Toggle novamente
   - Próximo sync volta a aplicar

3. **Excluir regra:** Botão X
   - Regra removida permanentemente
   - Transações já categorizadas mantêm categoria

### 5. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| Sem transações similares | Modal não abre, categoria aplicada direto |
| Transação sem merchant_name | Usa descrição para matching |
| Descrição muito curta (<5 chars) | Não cria regra de prefixo |
| Remover categoria | Aplica direto sem modal |
| Padrão duplicado | Atualiza regra existente |

---

## Arquivos Modificados

### Backend
- `backend/apps/banking/models.py` - Model CategoryRule
- `backend/apps/banking/services.py` - CategoryRuleService
- `backend/apps/banking/views.py` - ViewSet e actions
- `backend/apps/banking/serializers.py` - Serializers
- `backend/apps/banking/urls.py` - Rotas
- `backend/apps/banking/migrations/0013_categoryrule.py` - Migration

### Frontend
- `frontend/types/banking.ts` - Tipos TypeScript
- `frontend/services/banking.service.ts` - Métodos da API
- `frontend/components/banking/CategoryConfirmModal.tsx` - Modal
- `frontend/components/banking/index.ts` - Export
- `frontend/app/(dashboard)/transactions/page.tsx` - Integração
- `frontend/app/(dashboard)/settings/page.tsx` - Gerenciamento

---

## Dependências

- `unidecode` (Python) - Normalização de texto sem acentos
- `difflib.SequenceMatcher` (stdlib) - Fuzzy matching

Nenhuma nova dependência externa necessária.
