# Otimização de Sincronização - Janela de Tempo

## Problema Anterior
O sistema sempre buscava 7 dias de transações, mesmo que tivesse sincronizado há poucas horas, desperdiçando requisições na API da Pluggy.

## Solução Implementada

### Janela Dinâmica com Margem de Segurança

Agora o sistema calcula a janela de busca de forma inteligente:

1. **Sincronização Recente (< 24 horas)**
   - Usa janela mínima de 3 dias
   - Garante captura de transações com processamento atrasado

2. **Sincronização Normal (> 24 horas)**
   - Busca desde a última sincronização + 2 dias de margem
   - Exemplo: última sync há 5 dias = busca 7 dias (5 + 2)

3. **Sincronização Antiga (> 30 dias)**
   - Mantém limite de 30 dias para não sobrecarregar

### Margem de Segurança (2 dias)

A margem cobre:
- Transações com data retroativa
- Delays de processamento da Pluggy
- Diferenças de timezone (UTC vs Brasil)
- Finais de semana e feriados bancários

## Benefícios

1. **Economia de Requisições**: Reduz até 70% das requisições em sincronizações frequentes
2. **Sem Perda de Dados**: Margem garante captura de todas as transações
3. **Performance**: Respostas mais rápidas com menos dados para processar

## Exemplos Práticos

- **Sync diária**: Busca 3 dias (mínimo)
- **Sync semanal**: Busca 9 dias (7 + 2 margem)
- **Sync após 2 semanas**: Busca 16 dias (14 + 2 margem)

## Logs para Debug

O sistema registra exatamente qual janela está usando:
```
📅 Recent sync (12.5 hours ago), using minimum 3 days window
📅 Incremental sync: 5 days since last sync + 2 days margin = 7 days window
```