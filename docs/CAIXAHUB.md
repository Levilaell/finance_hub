# CaixaHub

Plataforma de gestão financeira automatizada para PMEs brasileiras.

## O que é o CaixaHub?

O CaixaHub é uma plataforma que automatiza a organização financeira de pequenas e médias empresas, substituindo planilhas manuais e serviços de BPO (Business Process Outsourcing) por uma solução integrada com Open Banking e inteligência artificial.

### Proposta de Valor

- Substitui serviços de BPO (~R$1.500/mês) por uma plataforma automatizada (R$197/mês)
- Elimina trabalho manual de organização de extratos e categorização
- Oferece visibilidade financeira em tempo real
- Economia de 5+ horas semanais de trabalho manual

---

## Funcionalidades Principais

### 1. Conexão Bancária e Sincronização

- Integração Open Finance via Pluggy com 100+ bancos brasileiros
- Suporte a múltiplas contas (corrente, poupança, cartão de crédito)
- Sincronização automática diária de transações
- Webhooks para notificações em tempo real
- Monitoramento de status de conexão

### 2. Categorização Inteligente

**Categorização Automática com IA:**
- Mapeamento de 100+ categorias brasileiras com ícones
- Tradução automática das categorias do Pluggy

**Categorias Hierárquicas:**
- Estrutura de 2 níveis (Categoria Pai > Subcategoria)
- Exemplo: Fornecedores > Carne e Pescados
- Compatível com DRE

**Regras de Categorização:**
- Aprende com categorizações manuais
- Três algoritmos: prefixo, contém, fuzzy matching (70%+ similaridade)
- Aplicação em lote para transações similares
- Dashboard de gerenciamento de regras

### 3. Gestão de Transações

- Histórico completo com filtros avançados
- Filtros por data, conta, categoria, tipo (receita/despesa)
- Categorização manual com preview de transações similares
- Vinculação de contas a pagar/receber
- Exportação para Excel

### 4. Contas e Saldos

- Saldo em tempo real por conta
- Tipos de conta suportados:
  - Conta corrente
  - Conta poupança
  - Cartão de crédito (com limite)
  - Empréstimos
  - Investimentos
- Evolução de saldo ao longo do tempo
- Números de conta mascarados para segurança

### 5. Contas a Pagar e Receber

**Gestão de Títulos:**
- Contas a Pagar e Contas a Receber
- Status: Pendente, Parcialmente Pago, Pago, Cancelado
- Suporte a recorrência (mensal, semanal, anual)

**Upload com OCR:**
- Upload de PDF ou imagem de boleto
- Extração automática: código de barras, valor, vencimento, beneficiário
- Score de confiança na extração
- Edição manual antes da criação

**Vinculação Título-Transação:**
- Algoritmo de match automático
- Score de relevância (0-100) baseado em data, descrição e categoria
- Vinculação/desvinculação manual

### 6. Relatórios e Análises

**Tipos de Relatório:**
- Fluxo de Caixa (receitas vs despesas)
- Breakdown por Categoria
- Evolução de Saldos
- Resumo Mensal (receitas, despesas, economia, médias)
- Análise de Tendências (6-24 meses)
- Comparação de Períodos

**Recursos:**
- Granularidade: diário, semanal, mensal, anual
- Gráficos interativos
- Indicadores de tendência
- Filtros por período
- Exportação de dados

### 7. Insights com IA

- **Score de Saúde Financeira:** 0-10
- **Status:** Excelente, Bom, Regular, Ruim
- **Alertas Inteligentes:**
  - Classificação por tipo e severidade
  - Recomendações acionáveis
- **Análise de Período:** Automática
- **Histórico de Insights:** Visualização de tendências

### 8. Autenticação e Usuários

- Registro e login por email
- Autenticação JWT
- Reset de senha com token
- Log de atividades (IP, tentativas de login)
- Suporte a fuso horário (padrão: America/Sao_Paulo)

### 9. Assinatura e Pagamento

- Integração completa com Stripe
- Período de trial gratuito
- Status de assinatura (trialing, active, past_due, cancelled)
- Múltiplos planos para testes A/B

### 10. Perfil da Empresa

- Dados da empresa (nome, CNPJ, setor)
- Tipos: MEI, Microempresa, EPP, Limitada, S.A.
- 20+ setores de atividade
- Validação de CNPJ

---

## Integrações

| Integração | Finalidade |
|------------|------------|
| **Pluggy** | Open Finance - conexão com 100+ bancos brasileiros |
| **Google Cloud Vision** | OCR para extração de dados de boletos |
| **Stripe** | Processamento de pagamentos e assinaturas |
| **OpenAI** | Geração de insights financeiros com IA |
| **Sentry** | Monitoramento de erros e performance |

---

## Segurança

- Autenticação JWT com refresh tokens
- Senhas criptografadas
- Configuração CORS
- Rate limiting nas APIs
- Log de atividades com IP
- Validação de uploads (PDF, PNG, JPG, máx 5MB)
- Validação de assinatura de webhooks

---

## Performance

- Cache Redis para dados frequentes
- Tarefas assíncronas com Celery
- Sincronização em background
- Webhooks para updates em tempo real
- Paginação para grandes volumes
- Otimização de queries (select_related/prefetch_related)

---

## Diferenciais

1. **Automação Completa** - Da conexão bancária aos relatórios
2. **IA para Categorização** - Aprende com o comportamento do usuário
3. **Foco no Brasil** - Bancos brasileiros, CNPJ, português nativo
4. **Custo-Benefício** - 10x mais barato que BPO tradicional
5. **Categorias Hierárquicas** - Estrutura organizacional flexível
6. **Match Inteligente** - Vinculação automática título-transação
7. **Sync em Tempo Real** - Dados sempre atualizados
8. **Multi-Banco** - Dashboard unificado para todas as contas
9. **Insights Acionáveis** - Análise de saúde financeira com IA

---

## Estrutura do Projeto

```
finance_hub/
├── backend/           # Django API
│   ├── accounts/      # Autenticação e usuários
│   ├── categories/    # Categorias e regras
│   ├── bank/          # Conexões bancárias e transações
│   ├── bills/         # Contas a pagar/receber
│   ├── reports/       # Relatórios e analytics
│   └── ai_insights/   # Insights com IA
├── frontend/          # Next.js App
│   ├── app/           # Páginas e rotas
│   ├── components/    # Componentes React
│   └── lib/           # Utilitários e API client
└── docs/              # Documentação
```

---


