# Checklist de Deploy - Webhooks Assíncronos

## ✅ O que foi implementado

### Arquivos Criados/Modificados
- ✅ `apps/banking/tasks.py` - Tasks Celery para processar webhooks
- ✅ `apps/banking/webhooks.py` - Handler modificado para resposta imediata
- ✅ `WEBHOOKS_SETUP.md` - Documentação completa
- ✅ `check_celery.py` - Script de verificação
- ✅ `railway.toml` - Configuração Railway
- ✅ `Procfile` - Já existente com worker configurado

### Mudanças no Código
- ✅ Webhook handler retorna 200 OK em < 100ms
- ✅ Processamento delegado para Celery tasks
- ✅ Logging de tempo de resposta adicionado
- ✅ Idempotência mantida via eventId
- ✅ Retry automático em tasks críticas (3x)

## 🚀 Checklist de Deploy no Railway

### 1. Verificar Variáveis de Ambiente

No Railway, certifique-se que estas variáveis estão configuradas:

```bash
# OBRIGATÓRIO para Celery
REDIS_URL=redis://...  # Railway fornece automaticamente se adicionar Redis

# RECOMENDADO para segurança
PLUGGY_WEBHOOK_SECRET=seu_secret_aqui  # Pegar no dashboard Pluggy
```

### 2. Adicionar Serviço Redis

1. No Railway dashboard, vá em "New" → "Database" → "Add Redis"
2. A variável `REDIS_URL` será adicionada automaticamente
3. Conecte o Redis ao seu projeto backend

### 3. Configurar Celery Worker

#### Opção A: Serviço Separado (Recomendado)

1. No Railway, adicione um novo serviço:
   - Clique em "New" → "Empty Service"
   - Nome: "Celery Worker"
   - Root Directory: `backend`
   - Build Command: (deixe vazio, usa o mesmo build)
   - Start Command: `celery -A core worker --loglevel=info --concurrency=2`

2. Configure as mesmas variáveis de ambiente do serviço web

#### Opção B: Process Manager (Alternativa)

Se Railway não suportar múltiplos serviços, modifique o `Procfile`:

```procfile
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT & celery -A core worker --loglevel=info --concurrency=2
```

⚠️ **Nota**: Opção A é preferível para melhor escalabilidade.

### 4. Verificar Deploy

Após deploy, verifique os logs:

```bash
railway logs
```

Procure por:
```
✓ [INFO] celery@worker ready.
✓ [INFO] Received webhook: item/updated
✓ [INFO] Webhook accepted and queued. Response time: 45.23ms
✓ [INFO] [TASK] Processing item_updated for item abc123
```

### 5. Testar Webhook

Você pode testar manualmente com curl:

```bash
curl -X POST https://seu-app.railway.app/api/banking/webhooks/pluggy/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "item/updated",
    "itemId": "test-123",
    "eventId": "evt-456"
  }'
```

Deve retornar:
```json
{
  "status": "ok",
  "processed": true,
  "async": true,
  "event_type": "item/updated",
  "response_time_ms": 52.34
}
```

### 6. Monitorar no Dashboard Pluggy

Acesse o dashboard da Pluggy e verifique:
- ✅ Status "Completo" nos webhooks
- ✅ Coluna "Tentativas" mostra apenas 1 (não 3)
- ✅ Tempo de conclusão < 1 segundo

## 🔧 Troubleshooting

### Problema: Worker não aparece nos logs

**Solução:**
```bash
# Verificar se Redis está conectado
railway variables | grep REDIS_URL

# Verificar se worker service existe
railway services
```

### Problema: Webhooks ainda falham

**Possíveis causas:**
1. Worker não está rodando → Verificar logs do serviço worker
2. Redis não conectado → Adicionar Redis database no Railway
3. Erro nas tasks → Verificar logs com `railway logs | grep ERROR`

**Debug:**
```bash
# Conectar ao ambiente Railway e rodar check
railway run python backend/check_celery.py
```

### Problema: Tempo de resposta > 5s

Isso **não deve mais acontecer**, pois o handler retorna imediatamente.

Se ainda ocorrer:
1. Verifique logs de tempo de resposta
2. Pode ser problema de rede/infraestrutura Railway
3. Considere aumentar recursos do serviço

## 📊 Métricas Esperadas

Após implementação:

| Métrica | Antes | Depois |
|---------|-------|--------|
| Tempo de resposta webhook | 3-10s | < 100ms |
| Taxa de sucesso | ~70% | 100% |
| Webhooks não entregues | Comum | Zero |
| Tentativas por webhook | 2-3 | 1 |

## ✅ Checklist Final

Antes de considerar completo:

- [ ] Redis adicionado ao projeto Railway
- [ ] Worker service criado e rodando
- [ ] Variável `REDIS_URL` configurada
- [ ] Logs mostram "celery@worker ready"
- [ ] Teste manual de webhook retorna < 100ms
- [ ] Dashboard Pluggy mostra webhooks completos
- [ ] Nenhum webhook com 3 tentativas nas últimas 24h

## 🎯 Próximos Passos (Opcional)

Para melhorar ainda mais:

1. **Monitoring**: Adicionar Sentry para tracking de erros em tasks
2. **Rate Limiting**: Limitar processamento de webhooks duplicados
3. **Dead Letter Queue**: Capturar tasks que falham após 3 retries
4. **Metrics Dashboard**: Criar dashboard com métricas de webhooks

## 📚 Referências

- [Documentação completa](./WEBHOOKS_SETUP.md)
- [Pluggy Webhooks](https://docs.pluggy.ai/docs/webhooks)
- [Railway Docs](https://docs.railway.app/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#tips-and-best-practices)
