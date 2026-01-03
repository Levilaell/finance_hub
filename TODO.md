# TODO - CaixaHub

## Relatórios (Reports)

### Prioridade Alta

- [ ] **PDF/Excel: Incluir comparação em categorias/subcategorias**
  - Arquivo: `backend/apps/reports/services.py:1024-1036`
  - Problema: Colunas de "Período Anterior" e "Variação" ficam vazias para categorias e subcategorias
  - Apenas grupos e resumos mostram valores de comparação

- [ ] **Adicionar logging nos handlers de exceção de export**
  - Arquivo: `backend/apps/reports/views.py:173-176, 242-245`
  - Problema: Erros de geração de PDF/Excel não são logados, dificulta debug em produção

- [ ] **Corrigir timezone para usar horário do Brasil**
  - Arquivo: `backend/apps/reports/views.py:31-32`
  - Problema: Datas sempre convertidas para UTC, pode incluir/excluir transações erradas nas bordas do período

### Prioridade Média

- [ ] **Melhorar cálculo de variação quando valor anterior é zero**
  - Arquivo: `backend/apps/reports/services.py:853-855`
  - Problema: Mostra sempre 100% quando período anterior é zero, pode confundir usuário

- [ ] **Distinguir transações sem categoria de categoria "Uncategorized"**
  - Arquivo: `backend/apps/reports/services.py:570`
  - Problema: Transações sem categoria são agrupadas como "Uncategorized", impossível distinguir

- [ ] **Otimizar performance de evolução de saldos**
  - Arquivo: `backend/apps/reports/services.py:277-290`
  - Problema: Query N+1 (uma query por dia por conta), usar window functions

### Prioridade Baixa

- [ ] Expandir paleta de cores (atualmente só 6 cores, repete se tiver mais contas)
- [ ] Adicionar word-wrap para nomes longos no PDF
- [ ] Adicionar indicador de progresso para exports grandes no frontend
