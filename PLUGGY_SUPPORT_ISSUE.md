# Problema de Sincronização com Items OUTDATED - Suporte Pluggy

## Resumo do Problema

Estamos enfrentando um problema onde não conseguimos sincronizar transações novas quando um Item está com status `OUTDATED`. Ao tentar atualizar o Item para obter dados recentes, o banco (Inter) sempre retorna status `WAITING_USER_ACTION`, exigindo reautenticação do usuário.

## Detalhes Técnicos

### Ambiente
- **API**: Pluggy API (Produção)
- **Banco afetado**: Inter (Connector ID do Item: a0beeaac-806b-410f-b814-fbb8fe517d54)
- **Framework**: Django + Python asyncio
- **Cliente HTTP**: httpx com autenticação via client_id/client_secret

### Fluxo Atual

1. **Primeira sincronização**: Funciona perfeitamente
   - Item criado via Pluggy Connect
   - Busca 90 dias de histórico
   - Todas as transações são sincronizadas corretamente

2. **Sincronizações subsequentes**: Falham em capturar novas transações
   - Item fica com status `OUTDATED` após alguns minutos
   - Novas transações não aparecem nas consultas à API
   - Tentativa de atualizar o Item resulta em `WAITING_USER_ACTION`

### Código de Exemplo

#### 1. Verificação de status e tentativa de atualização:

```python
async def sync_account():
    # Verificar status do Item
    async with PluggyClient() as client:
        item = await client.get_item(item_id)
        item_status = item.get('status')
        logger.info(f"Current item status: {item_status}")
        
        if item_status == 'OUTDATED':
            # Tentar atualizar o Item
            # PATCH /items/{item_id} com body vazio
            response = await client.patch(
                f"{self.base_url}/items/{item_id}",
                json={},
                headers=self._get_headers()
            )
            # Retorna status: UPDATING
            
            # Mas logo em seguida recebemos webhook:
            # event: "item/waiting_user_action"
```

#### 2. Logs do problema real:

```
INFO 2025-07-23 02:57:13,462 Current item status: OUTDATED
INFO 2025-07-23 02:57:15,006 Item update triggered, new status: UPDATING
INFO 2025-07-23 02:57:17,143 Waiting for update... Status: UPDATING (2s)
INFO 2025-07-23 02:57:18,483 Webhook received: item/waiting_user_action
WARNING 2025-07-23 02:57:19,276 Update triggered WAITING_USER_ACTION
```

#### 3. Resultado da busca de transações com Item OUTDATED:

```python
# Buscando transações dos últimos 30 dias
response = await client.get_transactions(
    account_id='0414b113-227f-472c-aae2-b48bf4b4f0d1',
    from_date='2025-06-23',
    to_date='2025-07-24',
    page=1,
    page_size=500
)

# Resultado: 49 transações encontradas
# MAS todas são antigas - nenhuma transação nova dos últimos minutos
# As transações novas só aparecem após o usuário reautenticar
```

## Perguntas para o Suporte

1. **É esperado que Items com status OUTDATED sempre exijam reautenticação ao tentar atualizar?**
   - Isso acontece com todos os bancos ou é específico do Inter?
   - Existe alguma forma de atualizar um Item OUTDATED sem triggerar WAITING_USER_ACTION?

2. **Como obter transações recentes sem forçar atualização do Item?**
   - Existe algum parâmetro especial na API de transações?
   - Os webhooks deveriam notificar sobre novas transações mesmo com Item OUTDATED?

3. **Qual a melhor prática para lidar com Items OUTDATED?**
   - Devemos sempre notificar o usuário para reautenticar?
   - Existe um tempo médio até Items ficarem OUTDATED?
   - É possível prevenir que Items fiquem OUTDATED?

4. **Sobre a sincronização incremental:**
   - Quando um Item está OUTDATED, a API retorna apenas transações em cache?
   - Existe diferença entre buscar com Item UPDATED vs OUTDATED?

## Solução Atual (Paliativa)

Por enquanto, implementamos:

```python
if item_status == 'OUTDATED':
    # Tentar atualizar apenas se OUTDATED
    try:
        update_result = await force_item_update(item_id)
        if update_result.get('status') == 'WAITING_USER_ACTION':
            # Notificar usuário que precisa reconectar
            return {
                'status': 'waiting_user_action',
                'message': 'Reconexão necessária'
            }
    except:
        # Continuar com dados desatualizados
        pass

# Buscar com janela de tempo estendida (30 dias)
# Para tentar capturar o máximo possível
```

## Impacto no Usuário

- Usuário faz transações no banco
- Tenta sincronizar no nosso app
- Recebe mensagem "0 transações sincronizadas"
- Precisa reconectar a conta manualmente para ver transações novas
- Experiência ruim e confusa

## Informações Adicionais

- **Item ID**: a0beeaac-806b-410f-b814-fbb8fe517d54
- **Account ID**: 0414b113-227f-472c-aae2-b48bf4b4f0d1
- **Connector**: Inter
- **Última atualização bem-sucedida**: Primeira conexão
- **Webhooks configurados**: Sim, recebendo corretamente

## Logs Completos

Posso fornecer logs completos de:
- Tentativas de atualização do Item
- Webhooks recebidos
- Consultas de transações antes/depois
- Estados do Item ao longo do tempo

Agradeço qualquer orientação sobre como melhorar a experiência de sincronização incremental.

## Contato

**Email**: [seu-email]
**Client ID**: [seu-client-id]
**Ambiente**: Produção