# Solução para Sincronização de Transações

## Problema

Após a primeira sincronização bem-sucedida, as sincronizações subsequentes retornavam "0 transações sincronizadas" mesmo quando havia novas transações no banco.

## Causa Raiz

1. **Items OUTDATED**: Quando um Item da Pluggy fica muito tempo sem ser atualizado, ele entra em status OUTDATED
2. **Cache de Transações**: Items OUTDATED retornam apenas transações em cache, não buscam novas do banco
3. **WAITING_USER_ACTION**: Tentar forçar atualização do Item dispara necessidade de reautenticação

## Solução Implementada

### 1. Janela de Tempo Expandida

Modificamos a lógica de sincronização incremental para sempre usar uma janela mínima de 7 dias:

```python
# Antes: janela muito pequena (1-3 dias)
# Agora: mínimo de 7 dias
days_back = max(7, days_since_sync + 3)
```

Isso garante que mesmo com delays de processamento da Pluggy, não perdemos transações.

### 2. Mensagens Informativas

Quando não há novas transações, o sistema agora informa:
- Quantos dias foram verificados
- Se o Item está OUTDATED
- Sugestão de reconexão quando apropriado

### 3. Fluxo de Reconexão

Implementamos um fluxo completo de reconexão que:
1. Detecta quando o banco pede reautenticação (WAITING_USER_ACTION)
2. Mostra dialog explicativo ao usuário
3. Gera token de reconexão com o `item_id` existente
4. Usa parâmetro `updateItem` no Pluggy Connect
5. Após reconexão bem-sucedida, sincroniza automaticamente

## Como Funciona Agora

### Sincronização Normal
1. Busca transações dos últimos 7+ dias
2. Se encontrar novas, sincroniza normalmente
3. Se não encontrar, informa período verificado

### Quando Item está OUTDATED
1. Sistema detecta status OUTDATED
2. Não tenta forçar atualização (evita WAITING_USER_ACTION)
3. Sugere reconexão ao usuário
4. Usuário pode continuar usando, mas sem novas transações

### Processo de Reconexão
1. Usuário clica em "Sincronizar"
2. Se receber erro WAITING_USER_ACTION, abre dialog
3. Usuário clica em "Reconectar"
4. Faz login no banco via Pluggy Connect
5. Item é atualizado e volta a sincronizar normalmente

## Benefícios

1. **Sem Perda de Dados**: Janela expandida garante captura de todas transações
2. **Transparência**: Usuário sabe exatamente o que está acontecendo
3. **Controle**: Usuário decide quando reconectar
4. **Estabilidade**: Evita loops de WAITING_USER_ACTION

## Limitações da Pluggy

- Items ficam OUTDATED após alguns dias sem atualização
- Forçar atualização pode disparar reautenticação
- Delay de minutos/horas para processar transações recentes
- Necessidade periódica de reconexão é normal e esperada