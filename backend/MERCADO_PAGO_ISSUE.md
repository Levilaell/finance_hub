# Problema: Transações Recentes do Mercado Pago não Aparecem na API Pluggy

## Diagnóstico Completo - 26/09/2025 23:38

### Situação
- Transação de R$ 0,15 enviada do Mercado Pago para o Inter hoje (26/09)
- Transação aparece corretamente no Inter (receptor)
- Transação NÃO aparece no Mercado Pago (emissor)

### Evidências

#### 1. Status das Contas
| Conta | Saldo | Status | Observação |
|-------|-------|--------|------------|
| Inter | R$ 0,15 | UPDATED | Recebeu transação, aparece corretamente |
| Mercado Pago | R$ 0,00 | UPDATED | Enviou transação, NÃO aparece |

#### 2. Teste com API Pluggy Diretamente

**Últimos 7 dias**: 0 transações
**Últimos 30 dias**: 0 transações
**Últimos 90 dias**: 7 transações (mais recente: 12/08/2025)

```
Transação mais recente do Mercado Pago na API:
2025-08-12T22:00:22.207Z - R$ 0.01 - Transferência Pix recebida LEV
```

#### 3. Ações Realizadas
1. ✅ Update manual do item via API
2. ✅ Aguardou processamento
3. ✅ Webhooks recebidos corretamente
4. ✅ Consultou diferentes períodos
5. ❌ Nenhuma transação recente retornada

### Conclusão

**O problema está na API da Pluggy/Conector Mercado Pago:**
- A API não retorna transações do Mercado Pago dos últimos 45 dias
- Saldos são atualizados corretamente
- Webhooks funcionam normalmente
- Sistema está funcionando corretamente

### Possíveis Causas

1. **Delay no Conector**: Mercado Pago pode ter delay maior para disponibilizar transações
2. **Limitação da API**: Pode haver restrições específicas para o conector Mercado Pago
3. **Cache/Processamento**: Transações podem estar em fila de processamento

### Recomendações

#### Imediatas
1. Aguardar 24-48h para ver se as transações aparecem
2. Testar com transações maiores (> R$ 1,00)
3. Verificar se é problema específico de transações Pix

#### Para Suporte Pluggy
Informar:
- Item ID: 8d221441-e0f5-46de-ad76-7cda4889ae79
- Account ID: 43fb1d7c-b0fb-4e86-a3c3-1aecc59eeffe
- Última transação visível: 12/08/2025
- Transações esperadas: Setembro/2025

### Workaround Temporário
Enquanto o problema não é resolvido:
1. Confiar apenas em saldos para Mercado Pago
2. Usar extrato manual para reconciliação
3. Monitorar se transações antigas eventualmente aparecem

### Código de Teste
```python
# Para verificar se transações aparecem posteriormente
python manage.py diagnose_transactions --account-id 43c587c7-7233-4e5a-81e5-c6897f73bde3 --days 90
```