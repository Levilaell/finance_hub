# Correção da Discrepância de Status entre Django Admin e Pluggy Dashboard

## Problema Identificado

### Sintoma
- **Django Admin**: Mostra status `UPDATING` para Bank Account
- **Pluggy Dashboard**: Mostra `SUCCESS` 

### Causa Raiz

O problema ocorre porque o Django armazena dois campos de status diferentes:

1. **`status`**: Estado do item (UPDATING, UPDATED, ERROR, etc.)
2. **`execution_status`**: Estado da execução (SUCCESS, PARTIAL_SUCCESS, ERROR, etc.)

Quando o Pluggy Dashboard mostra "SUCCESS", está se referindo ao `executionStatus`, mas o campo `status` permanece como "UPDATING" porque não estava sendo atualizado após uma sincronização bem-sucedida.

## Soluções Implementadas

### 1. Correção no Task de Sincronização

**Arquivo**: `backend/apps/banking/tasks.py`

Adicionada lógica para atualizar o status após sincronização bem-sucedida:

```python
# Update status to UPDATED if sync was successful and we're in UPDATING status
if item.status == 'UPDATING':
    # Check with Pluggy API for latest status
    try:
        latest_item_data = client.get_item(item.pluggy_item_id)
        item.status = latest_item_data.get('status', item.status)
        item.execution_status = latest_item_data.get('executionStatus', item.execution_status)
    except Exception as e:
        # If we can't get from API but sync was successful, update to UPDATED
        if item.execution_status in ['SUCCESS', 'PARTIAL_SUCCESS']:
            item.status = 'UPDATED'
```

### 2. Melhoria no Webhook Handler

**Arquivo**: `backend/apps/banking/tasks.py`

O webhook handler agora atualiza o status quando recebe eventos:

```python
def _handle_item_updated(data: Dict):
    # Update status from webhook data if provided
    if 'status' in data:
        item.status = data['status']
    
    if 'executionStatus' in data:
        item.execution_status = data['executionStatus']
```

### 3. Comando para Corrigir Itens Existentes

**Arquivo**: `backend/apps/banking/management/commands/fix_updating_status.py`

Criado comando para corrigir itens que já estão com status incorreto:

```bash
# Ver quais itens seriam corrigidos (dry run)
python manage.py fix_updating_status --dry-run

# Corrigir itens com sincronização da API
python manage.py fix_updating_status --sync-with-api

# Corrigir apenas baseado no execution_status local
python manage.py fix_updating_status
```

## Como Testar

1. **Para itens existentes com problema**:
   ```bash
   cd backend
   python manage.py fix_updating_status --sync-with-api
   ```

2. **Para novos itens**:
   - A correção já está aplicada e funcionará automaticamente
   - O status será atualizado corretamente após cada sincronização

3. **Monitorar logs**:
   ```bash
   tail -f logs/banking.log | grep "status"
   ```

## Fluxo Correto de Status

1. **Criação**: Item criado com status `CREATED`
2. **Login**: Status muda para `LOGIN_IN_PROGRESS`
3. **Sincronização**: Status muda para `UPDATING`
4. **Conclusão**: 
   - Se `executionStatus` = `SUCCESS` → status deve ser `UPDATED`
   - Se `executionStatus` = `ERROR` → status deve ser `ERROR`

## Prevenção Futura

As correções implementadas garantem que:

1. Após cada sincronização bem-sucedida, o status é verificado e atualizado
2. Webhooks atualizam o status automaticamente
3. Há uma verificação dupla: primeiro tenta obter da API, depois usa lógica local

Isso elimina a discrepância entre o que aparece no Django Admin e no Pluggy Dashboard.