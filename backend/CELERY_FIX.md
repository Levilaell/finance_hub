# Correção do Celery para macOS

## Problema Identificado
O Celery estava configurado mas não processava as tasks enfileiradas. Dois problemas foram encontrados:

1. **Filas Incorretas**: O Celery estava configurado para usar filas específicas (`banking`, `billing`, etc.) mas o worker estava escutando apenas a fila padrão `celery`.

2. **Fork Safety no macOS**: Erro de fork() no macOS com múltiplos processos worker causando crash com a mensagem:
   ```
   objc[xxxxx]: +[NSMutableString initialize] may have been in progress in another thread when fork() was called
   ```

## Solução Aplicada

### Para desenvolvimento local no macOS:
```bash
# Iniciar Celery com pool solo e todas as filas
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES celery -A core worker -l info \
  -Q celery,banking,billing,reports,notifications,ai_insights \
  --pool=solo
```

### Para produção (Linux):
```bash
# Pode usar pool prefork normal
celery -A core worker -l info \
  -Q celery,banking,billing,reports,notifications,ai_insights
```

## Verificação
As transações agora são sincronizadas corretamente:
- 6 transações foram sincronizadas com sucesso
- Celery processa tasks assincronamente
- Sistema tem fallback para sync síncrono quando Celery não está disponível

## Configurações Importantes
- **Arquivo**: `core/celery.py`
- **Filas configuradas**: 
  - `banking` - para tasks de sincronização bancária
  - `billing` - para tasks de cobrança
  - `reports` - para relatórios
  - `notifications` - para notificações
  - `ai_insights` - para insights de IA
  - `celery` - fila padrão

## Comandos Úteis
```bash
# Verificar se Redis está rodando
redis-cli ping

# Verificar fila no Redis
redis-cli LLEN celery
redis-cli LLEN banking

# Testar task manualmente
python manage.py shell
>>> from apps.banking.tasks import sync_bank_account
>>> result = sync_bank_account.delay('item-id')
>>> print(result.state)
```