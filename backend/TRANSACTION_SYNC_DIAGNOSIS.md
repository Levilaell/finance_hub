# Diagnóstico de Sincronização de Transações - Pluggy

## Resumo do Problema
O usuário fez uma transação de R$ 0,15 do Mercado Pago para o Inter hoje (26/09/2025), mas a transação não aparece no sistema mesmo após sincronização manual.

## Problemas Identificados e Corrigidos

### 1. ✅ Campo `bank_data` nulo causando erro
**Problema**: O campo `bank_data` no modelo `BankAccount` não aceitava valores nulos, causando erro ao sincronizar contas.

**Solução**:
- Modificado `services.py` para garantir que `bank_data` nunca seja `None`
- Criada migration `0003_allow_null_bank_data.py` para permitir valores nulos

### 2. ✅ Webhooks não mapeados
**Problema**: Eventos `transactions/created`, `transactions/updated`, `item/login_succeeded` não estavam mapeados no webhook handler.

**Solução**: Adicionados handlers para todos os eventos da Pluggy

### 3. ✅ Sincronização de contas falhando
**Problema**: Quando o webhook tentava sincronizar transações, as contas ainda não existiam.

**Solução**: Modificados handlers para sempre sincronizar contas antes de transações

### 4. ✅ Implementação de atualização de item
**Problema**: Sincronizações manuais subsequentes não funcionavam sem atualizar o item na Pluggy primeiro.

**Solução**: Implementado `trigger_item_update()` para forçar atualização antes de sincronizar

## Problema Principal: Transações não disponíveis na API da Pluggy

### Diagnóstico Final
Após todas as correções, o diagnóstico revelou:

**Inter (Recebedor)**:
- Saldo: R$ 0,15 ✅ (atualizado corretamente)
- Status: UPDATED
- Transações últimos 2 dias: 1 (Pix enviado R$ 18,10 em 25/09)
- **Transação de R$ 0,15 recebida hoje: NÃO aparece na API**

**Mercado Pago (Pagador)**:
- Saldo: R$ 0,00 ✅ (atualizado corretamente)
- Status: UPDATING
- Transações últimos 2 dias: 0
- **Transação de R$ 0,15 enviada hoje: NÃO aparece na API**

### Conclusão
**A API da Pluggy não está retornando as transações mais recentes**, mesmo que os saldos tenham sido atualizados corretamente. Possíveis causas:

1. **Delay na disponibilização de transações**: A Pluggy pode atualizar saldos antes de disponibilizar o histórico de transações
2. **Cache da API**: As transações podem estar em cache e não refletirem mudanças recentes
3. **Processamento assíncrono**: Saldos e transações podem ser processados em momentos diferentes

## Comandos de Diagnóstico Criados

### 1. `test_manual_sync`
Testa sincronização manual com atualização de item.
```bash
python manage.py test_manual_sync --connection-id <id>
```

### 2. `force_sync`
Força sincronização de todas as conexões ativas.
```bash
python manage.py force_sync [--skip-update]
```

### 3. `diagnose_transactions`
Compara transações da Pluggy com banco de dados local.
```bash
python manage.py diagnose_transactions --days 2
```

## Recomendações

### Curto Prazo
1. **Aguardar**: Esperar alguns minutos/horas para a Pluggy processar e disponibilizar as transações
2. **Webhook de transações**: Configurar webhooks para `transactions/created` para sincronização automática
3. **Polling periódico**: Implementar job que sincroniza transações a cada X minutos

### Médio Prazo
1. **Cache de transações**: Implementar cache local para reduzir chamadas à API
2. **Reconciliação**: Sistema para identificar e corrigir discrepâncias entre saldos e transações
3. **Notificações**: Alertar usuário quando novas transações forem detectadas

### Contato com Pluggy
Considerar contatar o suporte da Pluggy para entender:
- Tempo médio de disponibilização de transações após ocorrerem
- Se há endpoint específico para transações em tempo real
- Se há limitações conhecidas para bancos específicos (Mercado Pago, Inter)

## Status dos Bancos (Atualizado 26/09 23:35)

| Banco | Status | Saldo | Transações Sync | Observações |
|-------|--------|-------|-----------------|-------------|
| Inter | UPDATED | R$ 0,15 | OK ✅ | Transação R$ 0,15 recebida aparece corretamente |
| Mercado Pago | UPDATING | R$ 0,00 | Problema ❌ | API Pluggy não retorna nenhuma transação recente |
| Nubank | UPDATED | R$ 0,00 | OK | Sem transações recentes |

### Atualização 26/09 23:35

**Problema Resolvido - Webhook Loop**:
- ✅ Corrigido loop infinito de webhooks modificando handlers para não triggar updates

**Inter (Receptor) - FUNCIONANDO**:
- Transação "Pix recebido - Levi Lael Coelho Silva R$ 0,15" aparece corretamente
- Data: 2025-09-26 22:39:32
- Sincronização funcionando perfeitamente

**Mercado Pago (Pagador) - PROBLEMA NA API PLUGGY**:
- API da Pluggy retorna 0 transações para últimos 2 dias
- Saldo está correto (R$ 0,00)
- Problema aparenta ser específico do conector Mercado Pago na Pluggy
- Sincronização manual encontrou 7 transações antigas mas nenhuma recente

## Logs Relevantes
- Webhooks estão chegando corretamente via ngrok
- Sincronização está funcionando mas retornando 0 transações recentes
- Saldos são atualizados corretamente
- Date range está correto (365 dias)