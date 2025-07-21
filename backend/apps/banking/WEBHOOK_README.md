# Pluggy Webhooks - Guia de Configuração

## Visão Geral

Os webhooks da Pluggy foram implementados para receber notificações em tempo real sobre:
- Criação e atualização de itens (conexões bancárias)
- Erros de autenticação
- Novas transações disponíveis
- Criação e atualização de contas

## Implementação Atual

### 1. Verificação de Segurança (HMAC)
- Os webhooks verificam a assinatura HMAC-SHA256 enviada no header `X-Pluggy-Signature`
- O secret deve ser configurado na variável de ambiente `PLUGGY_WEBHOOK_SECRET`

### 2. Processamento Assíncrono
- Eventos são processados de forma assíncrona para melhor performance
- Sincronização automática é disparada quando necessário

### 3. Eventos Suportados
- `item/created`: Quando uma nova conexão é criada
- `item/updated`: Quando o status de uma conexão muda (ex: LOGIN_IN_PROGRESS → ACTIVE)
- `item/error`: Quando há erro de autenticação
- `transactions/created`: Quando novas transações estão disponíveis
- `account/created`: Quando uma nova conta é detectada
- `account/updated`: Quando informações da conta são atualizadas

## Configuração

### 1. Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# Webhook secret fornecido pela Pluggy
PLUGGY_WEBHOOK_SECRET=seu-webhook-secret-aqui

# URL do backend (para produção, use a URL pública)
BACKEND_URL=http://localhost:8000
```

### 2. Configurar Webhook na Pluggy

Execute o comando Django para configurar automaticamente:

```bash
python manage.py setup_pluggy_webhook
```

Para forçar atualização de um webhook existente:

```bash
python manage.py setup_pluggy_webhook --force
```

### 3. Endpoint do Webhook

O webhook está disponível em:
```
POST /api/banking/pluggy/webhook/
```

## Testes Locais

### 1. Testar Webhook Manualmente

Use o comando de teste para simular eventos:

```bash
# Simular criação de item
python manage.py test_pluggy_webhook item/created

# Simular item ficando ativo
python manage.py test_pluggy_webhook item/updated --status ACTIVE

# Simular erro de autenticação
python manage.py test_pluggy_webhook item/error

# Simular novas transações
python manage.py test_pluggy_webhook transactions/created --account-id sua-conta-id
```

### 2. Usar ngrok para Testes com Pluggy Real

Para testar com a Pluggy em ambiente de desenvolvimento:

1. Instale o ngrok: https://ngrok.com/
2. Execute: `ngrok http 8000`
3. Copie a URL HTTPS fornecida
4. Atualize `BACKEND_URL` no `.env` com a URL do ngrok
5. Execute `python manage.py setup_pluggy_webhook --force`

## Logs e Debugging

Os webhooks registram logs detalhados:

```python
# Ver logs do webhook
tail -f logs/django.log | grep "Pluggy webhook"

# Logs incluem:
# - Eventos recebidos
# - Verificação de assinatura
# - Processamento de cada tipo de evento
# - Erros e exceções
```

## Segurança

1. **Sempre verifique a assinatura**: Em produção, certifique-se de que `PLUGGY_WEBHOOK_SECRET` está configurado
2. **Use HTTPS**: Em produção, o webhook deve estar disponível apenas via HTTPS
3. **IP Whitelist**: Considere adicionar os IPs da Pluggy ao whitelist (opcional)

## Fluxo de Processamento

1. **Webhook recebido** → Verificação de assinatura
2. **Assinatura válida** → Parsing do evento
3. **Processamento do evento**:
   - `item/updated` com status ACTIVE → Sincroniza todas as contas do item
   - `item/error` → Marca contas como erro
   - `transactions/created` → Sincroniza transações da conta específica
4. **Resposta** → HTTP 200 (sucesso) ou 500 (erro)

## Troubleshooting

### Webhook não está sendo chamado
- Verifique se o webhook foi configurado: `python manage.py setup_pluggy_webhook`
- Confirme a URL do webhook no painel da Pluggy
- Em dev, use ngrok para expor localhost

### Erro de assinatura inválida
- Verifique se `PLUGGY_WEBHOOK_SECRET` está correto
- Certifique-se de que está usando o secret fornecido pela Pluggy

### Sincronização não acontece
- Verifique os logs para erros
- Confirme que a conta existe no banco de dados
- Verifique se a conta está ativa (`is_active=True`)

## Próximos Passos

1. Monitorar performance dos webhooks em produção
2. Implementar retry logic para falhas temporárias
3. Adicionar métricas e alertas
4. Considerar fila de processamento para alta escala