# Categorias Hierárquicas

## Resumo

Implementação de estrutura hierárquica de categorias no CaixaHub, permitindo organização em 2 níveis: **Categoria Pai > Subcategoria**.

Exemplo: `Fornecedores > Carne e Pescados`

## Funcionalidades

### Backend

| Componente | Arquivo | Descrição |
|------------|---------|-----------|
| Validações | `backend/apps/banking/serializers.py` | 3 validações no `CategorySerializer` |
| Subcategorias aninhadas | `backend/apps/banking/serializers.py` | `subcategories` via SerializerMethodField |
| Filtro de categorias pai | `backend/apps/banking/views.py` | GET retorna apenas categorias pai |

#### Validações implementadas:

1. **Mesmo usuário**: Parent deve pertencer ao mesmo usuário
2. **Mesmo tipo**: Parent deve ser do mesmo tipo (income/expense)
3. **Máximo 2 níveis**: Parent não pode ter parent (evita subcategoria de subcategoria)

#### Estrutura da resposta da API:

```json
GET /api/banking/categories/

[
  {
    "id": "uuid",
    "name": "Fornecedores",
    "type": "expense",
    "color": "#ef4444",
    "icon": "📦",
    "is_system": false,
    "parent": null,
    "subcategories": [
      {
        "id": "uuid",
        "name": "Carne e Pescados",
        "type": "expense",
        "color": "#f97316",
        "icon": "📁",
        "is_system": false,
        "parent": "uuid-do-pai"
      }
    ]
  }
]
```

### Frontend

| Componente | Arquivo | Descrição |
|------------|---------|-----------|
| Interface TypeScript | `frontend/types/banking.ts` | Campo `subcategories?: Category[]` |
| Página de categorias | `frontend/app/(dashboard)/categories/page.tsx` | UI hierárquica completa |

#### Funcionalidades da UI:

- Lista hierárquica com subcategorias indentadas
- Subcategorias exibem apenas quadrado colorido (sem ícone)
- Botão "+" em cada categoria pai para criar subcategoria
- Campo "Categoria Pai" no formulário de criação/edição
- Tipo herdado automaticamente do pai (campo desabilitado)
- Campo ícone oculto ao criar subcategoria
- Confirmação ao excluir categoria com subcategorias (aviso de exclusão em cascata)

## Como Testar

### Pré-requisitos

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # ou venv\Scripts\activate no Windows
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Cenários de Teste

#### 1. Criar categoria pai

1. Acesse `http://localhost:3000/categories`
2. Clique em **"Nova Categoria"**
3. Preencha:
   - Nome: `Fornecedores`
   - Tipo: `Despesa`
   - Cor: escolha uma
   - Ícone: escolha um
4. Clique em **"Salvar"**
5. **Esperado**: Categoria aparece na lista de Despesas

#### 2. Criar subcategoria

1. Localize a categoria "Fornecedores" na lista
2. Clique no botão **"+"** ao lado dela
3. Preencha:
   - Nome: `Carne e Pescados`
   - Categoria Pai: já vem preenchido
   - Tipo: já vem preenchido (Despesa) e desabilitado
   - Cor: escolha uma
   - Ícone: **não aparece** (comportamento esperado)
4. Clique em **"Salvar"**
5. **Esperado**:
   - Subcategoria aparece indentada abaixo de "Fornecedores"
   - Subcategoria tem apenas quadrado colorido (sem ícone)

#### 3. Validação de tipo

1. Clique em **"Nova Categoria"**
2. Selecione Tipo: `Receita`
3. Selecione Categoria Pai: uma categoria de `Despesa`
4. **Esperado**: Lista de categorias pai mostra apenas categorias de Receita

#### 4. Validação de profundidade

1. Crie uma subcategoria (ex: "Carne e Pescados")
2. Tente criar nova categoria com parent = "Carne e Pescados"
3. **Esperado**: Erro "Não é permitido criar subcategoria de subcategoria"

#### 5. Exclusão com subcategorias

1. Clique no botão de lixeira da categoria "Fornecedores"
2. **Esperado**: Modal de confirmação com aviso amarelo:
   > "Atenção: Esta categoria possui X subcategoria(s) que também serão excluídas."
3. Confirme a exclusão
4. **Esperado**: Categoria pai e todas subcategorias são removidas

#### 6. Editar subcategoria

1. Clique no botão de edição de uma subcategoria
2. Altere o nome e a cor
3. **Esperado**: Alterações são salvas, ícone continua não aparecendo

## Arquivos Modificados

```
backend/
├── apps/banking/
│   ├── serializers.py    # CategorySerializer + CategoryChildSerializer
│   └── views.py          # CategoryViewSet.get_queryset()

frontend/
├── types/
│   └── banking.ts        # interface Category { subcategories?: Category[] }
└── app/(dashboard)/categories/
    └── page.tsx          # UI hierárquica completa
```

## Decisões Técnicas

| Decisão | Justificativa |
|---------|---------------|
| Máximo 2 níveis | Simplicidade para DRE, atende 99% dos casos |
| Subcategoria sem ícone | Diferenciação visual, menos poluição |
| CASCADE na exclusão | Comportamento padrão do Django, com aviso na UI |
| Ícone armazenado no banco | Mantém compatibilidade, apenas não exibe na UI |
| Tipo herdado do pai | Evita inconsistência de dados |

## Próximos Passos (Fora do Escopo Atual)

- [ ] DRE com expansão de categorias > subcategorias
- [ ] Regras de categorização automática por subcategoria
- [ ] Migração de categorias existentes para estrutura hierárquica
