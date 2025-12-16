# Sistema de Categorias e Subcategorias - Finance Hub

## Estrutura dos Modelos

### Modelo Category

**Localização:** `backend/apps/banking/models.py:237-267`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `user` | ForeignKey | Usuário dono da categoria |
| `name` | CharField(100) | Nome da categoria |
| `type` | CharField | `'income'` (receita) ou `'expense'` (despesa) |
| `color` | CharField | Cor em hexadecimal (ex: `#d946ef`) |
| `icon` | CharField | Emoji representativo (ex: `🛒`) |
| `is_system` | Boolean | Se é categoria do sistema (não pode ser deletada) |
| `parent` | ForeignKey(self) | Referência para categoria pai (subcategorias) |
| `created_at` | DateTime | Data de criação |
| `updated_at` | DateTime | Data de atualização |

### Modelo CategoryRule

**Localização:** `backend/apps/banking/models.py:465-516`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `user` | ForeignKey | Usuário dono da regra |
| `pattern` | CharField | Padrão de texto normalizado |
| `match_type` | CharField | `'prefix'`, `'contains'` ou `'fuzzy'` |
| `category` | ForeignKey | Categoria a ser aplicada |
| `is_active` | Boolean | Se a regra está ativa |
| `applied_count` | Integer | Quantas vezes foi aplicada |

---

## Hierarquia de Categorias

```
Categoria Pai (parent=null)
├── Subcategoria 1 (parent=categoria_pai)
├── Subcategoria 2 (parent=categoria_pai)
└── Subcategoria 3 (parent=categoria_pai)
```

### Regras de Hierarquia

- **Máximo 2 níveis:** Apenas pai → filho (subcategorias não podem ter subcategorias)
- **Herança de tipo:** Subcategorias herdam o tipo (`income`/`expense`) do pai
- **Mesmo usuário:** Pai e filho devem pertencer ao mesmo usuário
- **Validação de tipo:** O tipo do pai deve corresponder ao tipo informado

---

## Mapeamento Pluggy

### Arquivo de Categorias

**Localização:** `backend/apps/banking/pluggy_categories.json`

Contém **130 categorias** do Pluggy com traduções português/inglês:

```json
{
  "id": "01010000",
  "description": "Salary",
  "descriptionTranslated": "Salário",
  "parentId": "01000000",
  "parentDescription": "Income"
}
```

### Estrutura Hierárquica Pluggy

```
Receitas (01000000)
├── Salário (01010000)
├── Aposentadoria (01020000)
├── Freelance (01030000)
├── Auxílio governamental (01040000)
└── Receita não recorrente (01050000)

Compras (03000000)
├── Supermercado (03010000)
├── Vestuário (03020000)
├── Eletrônicos (03030000)
├── Farmácia (03040000)
└── Pet shop (03050000)

Transferências (05000000)
├── Transferência - PIX (05070000)
├── Transferência - TED (05080000)
└── Transferências para terceiros (05090000)
    ├── PIX (05090004)
    ├── DOC (05090003)
    └── Cartão de débito (05090002)

Serviços (06000000)
├── Celular/Telefone (06010000)
├── Internet (06020000)
├── Streaming (06030000)
└── Educação (06040000)

Alimentação (07000000)
├── Restaurantes (07010000)
├── Fast food (07020000)
├── Delivery (07030000)
└── Padaria/Café (07040000)
```

---

## Como Funciona a Categorização

### 1. Categorização Automática (Sincronização)

```
Transação do Pluggy
       ↓
pluggy_category (string original em inglês)
       ↓
get_or_create_category()
       ↓
Traduz para português (via pluggy_categories.json)
       ↓
Aplica ícone e cor automaticamente
       ↓
Cria ou reutiliza Category do usuário
       ↓
Salva em user_category (FK)
```

**Localização:** `backend/apps/banking/services.py:430-478`

### 2. Categorização Manual (Usuário)

1. Usuário altera categoria via interface
2. Sistema salva em `user_category` (ForeignKey)
3. Propriedade `effective_category` retorna categoria do usuário quando definida

### 3. Regras Automáticas (CategoryRule)

| Tipo de Match | Descrição | Exemplo |
|---------------|-----------|---------|
| `prefix` | Início da descrição (12 primeiros caracteres) | "MERCADO PAG" |
| `contains` | Padrão aparece em qualquer lugar | "NETFLIX" |
| `fuzzy` | Similaridade >= 70% (SequenceMatcher) | "MERCDO PAGMTO" ≈ "MERCADO PAGAMENTO" |

**Localização:** `backend/apps/banking/services.py:1365-1567`

### Fluxo de Aplicação de Regras

```
Nova transação sincronizada
       ↓
Busca CategoryRules ativas do usuário
       ↓
Normaliza descrição (remove acentos, lowercase)
       ↓
Testa cada regra (ordenadas por data de criação)
       ↓
Primeira regra que match → aplica categoria
       ↓
Incrementa applied_count da regra
```

---

## Mapeamento de Ícones

**Localização:** `backend/apps/banking/services.py:71-247`

| Categoria | Ícone |
|-----------|-------|
| Salário | 💰 |
| Aposentadoria | 👴 |
| Freelance | 💼 |
| Supermercado | 🛒 |
| Vestuário | 👔 |
| Eletrônicos | 📱 |
| Restaurante | 🍽️ |
| Fast food | 🍔 |
| Delivery | 🛵 |
| Transporte | 🚗 |
| Combustível | ⛽ |
| Uber/99 | 🚕 |
| Saúde | 🏥 |
| Farmácia | 💊 |
| Educação | 🎓 |
| Streaming | 📺 |
| Internet | 🌐 |
| Aluguel | 🏠 |
| Energia | 💡 |
| Água | 💧 |
| Investimentos | 📈 |
| PIX | 🔄 |
| TED/DOC | 🏦 |

---

## Mapeamento de Cores

**Localização:** `backend/apps/banking/services.py:250-427`

| Tipo de Categoria | Cor | Hex |
|-------------------|-----|-----|
| Receitas | Verde | `#10b981` |
| Salário | Verde escuro | `#059669` |
| Alimentação | Laranja | `#f59e0b` |
| Restaurantes | Laranja escuro | `#f97316` |
| Compras | Rosa | `#ec4899` |
| Investimentos | Azul | `#0ea5e9` |
| Transferências | Índigo | `#6366f1` |
| PIX | Roxo | `#8b5cf6` |
| Empréstimos | Vermelho | `#dc2626` |
| Impostos | Vermelho escuro | `#b91c1c` |
| Serviços | Cinza | `#6b7280` |

---

## Comandos de Gerenciamento

### Criar Categorias Padrão

```bash
python manage.py create_default_categories --user-id=<UUID>
```

Cria 28 categorias padrão (16 despesas, 12 receitas) para um usuário.

### Atribuir Categorias

```bash
python manage.py assign_categories [--dry-run]
```

Atribui categorias a transações que não possuem categoria definida.

### Traduzir Categorias

```bash
python manage.py translate_categories [--dry-run]
```

Traduz nomes de categorias do inglês para português usando `pluggy_categories.json`.

### Atualizar Cores

```bash
python manage.py update_category_colors [--dry-run]
```

Atualiza cores das categorias baseado no mapeamento definido.

### Atualizar Ícones

```bash
python manage.py update_category_icons [--dry-run]
```

Atualiza ícones (emojis) das categorias baseado no mapeamento definido.

---

## Frontend

### Página de Categorias

**Localização:** `frontend/app/(dashboard)/categories/page.tsx`

**Funcionalidades:**
- Separação entre abas de Receitas e Despesas
- Visualização hierárquica (categorias pai com subcategorias expandíveis)
- CRUD completo (criar, editar, deletar)
- Seletor visual de 16 cores preset
- Seletor visual de 24 emojis preset
- Badge "Sistema" para categorias protegidas
- Confirmação antes de deletar

### Constantes de UI

**Localização:** `frontend/lib/category-constants.ts`

```typescript
PRESET_COLORS: [
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#84cc16', '#22c55e', '#10b981', '#14b8a6',
  '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
  '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'
]

PRESET_ICONS: [
  '🏠', '🚗', '🍔', '🛒', '💊', '🎓', '🎮', '✈️',
  '💰', '📱', '👔', '🎁', '🏥', '⚡', '🎬', '🏋️',
  '🐕', '📚', '💼', '🔧', '🎵', '☕', '🌐', '📁'
]

DEFAULT_COLOR: '#d946ef'
DEFAULT_ICON: '📁'
```

### Modal de Confirmação de Categoria

**Localização:** `frontend/components/banking/CategoryConfirmModal.tsx`

Ao categorizar uma transação manualmente:
1. Busca transações similares (últimos 6 meses)
2. Mostra matches com score de similaridade
3. Permite selecionar quais atualizar em lote
4. Opção de criar regra para futuras transações

---

## API Endpoints

### Categorias

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/categories/` | Listar categorias |
| POST | `/api/banking/categories/` | Criar categoria |
| GET | `/api/banking/categories/{id}/` | Detalhe da categoria |
| PATCH | `/api/banking/categories/{id}/` | Atualizar categoria |
| DELETE | `/api/banking/categories/{id}/` | Deletar categoria |

**Query params:**
- `type`: Filtrar por `'income'` ou `'expense'`

### Regras de Categorização

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/banking/category-rules/` | Listar regras |
| POST | `/api/banking/category-rules/` | Criar regra |
| GET | `/api/banking/category-rules/{id}/` | Detalhe da regra |
| PATCH | `/api/banking/category-rules/{id}/` | Atualizar regra |
| DELETE | `/api/banking/category-rules/{id}/` | Deletar regra |
| GET | `/api/banking/category-rules/stats/` | Estatísticas |

### Transações (relacionado a categorias)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| PATCH | `/api/banking/transactions/{id}/` | Atualizar categoria |
| GET | `/api/banking/transactions/{id}/similar/` | Buscar similares |

---

## Exemplos de Uso

### Criar Categoria (Backend)

```python
from apps.banking.models import Category

categoria = Category.objects.create(
    user=user,
    name="Assinaturas",
    type="expense",
    color="#8b5cf6",
    icon="📺",
    is_system=False
)
```

### Criar Subcategoria (Backend)

```python
subcategoria = Category.objects.create(
    user=user,
    name="Netflix",
    type="expense",
    parent=categoria,  # FK para categoria pai
    color="#e50914",
    icon="🎬"
)
```

### Criar Categoria (API)

```http
POST /api/banking/categories/
Content-Type: application/json

{
  "name": "Assinaturas",
  "type": "expense",
  "color": "#8b5cf6",
  "icon": "📺"
}
```

### Criar Subcategoria (API)

```http
POST /api/banking/categories/
Content-Type: application/json

{
  "name": "Netflix",
  "type": "expense",
  "parent": "uuid-da-categoria-pai",
  "color": "#e50914",
  "icon": "🎬"
}
```

### Categorizar Transação com Regra (API)

```http
PATCH /api/banking/transactions/{id}/
Content-Type: application/json

{
  "user_category_id": "uuid-da-categoria",
  "create_rule": true,
  "similar_transaction_ids": ["uuid-1", "uuid-2"]
}
```

### Criar Regra Manual (API)

```http
POST /api/banking/category-rules/
Content-Type: application/json

{
  "pattern": "netflix",
  "match_type": "contains",
  "category": "uuid-da-categoria"
}
```

---

## Para que Serve

1. **Organização Financeira:** Agrupa transações por tipo de gasto/receita para melhor visualização
2. **Relatórios e Gráficos:** Base para análises visuais (pizza, barras, tendências)
3. **Automação:** Categoriza automaticamente transações futuras com padrões similares
4. **Personalização:** Usuário pode criar categorias próprias com cores e ícones
5. **Insights de IA:** Alimenta o sistema de insights para recomendações inteligentes
6. **Orçamentos:** Permite definir limites de gastos por categoria
7. **Metas:** Acompanhamento de objetivos financeiros por categoria

---

## Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    SINCRONIZAÇÃO PLUGGY                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Pluggy envia transação com categoria em inglês              │
│  2. Sistema verifica se existe CategoryRule ativa               │
│     → Se SIM: aplica categoria da regra                         │
│     → Se NÃO: continua para auto-categorização                  │
│  3. Traduz categoria usando pluggy_categories.json              │
│  4. Busca/cria Category do usuário                              │
│  5. Aplica ícone e cor automaticamente                          │
│  6. Salva transação com user_category                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CATEGORIZAÇÃO MANUAL                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Usuário abre transação na interface                         │
│  2. Seleciona nova categoria                                    │
│  3. Sistema busca transações similares                          │
│  4. Usuário escolhe aplicar em lote (opcional)                  │
│  5. Usuário escolhe criar regra (opcional)                      │
│  6. Sistema atualiza transações e cria regra                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RELATÓRIOS E INSIGHTS                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Agrupa transações por categoria                             │
│  2. Gera gráficos de distribuição                               │
│  3. Calcula tendências por categoria                            │
│  4. Alimenta sistema de IA para insights                        │
│  5. Permite comparação entre períodos                           │
└─────────────────────────────────────────────────────────────────┘
```
