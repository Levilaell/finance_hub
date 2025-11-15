# Sistema de Tracking de Atividade de Usuários

Este sistema permite rastrear todas as ações importantes dos usuários, incluindo login, conexões bancárias e sincronizações.

## Funcionalidades

### 1. Eventos Rastreados Automaticamente

O sistema registra automaticamente os seguintes eventos:

- **Login/Logout**: Capturado via Django signals
- **Conexões Bancárias**:
  - Criação de conexão
  - Atualização de conexão
  - Exclusão de conexão
- **Sincronizações**:
  - Início de sincronização
  - Conclusão de sincronização
  - Falha na sincronização

### 2. Informações Capturadas

Para cada evento, o sistema registra:
- Usuário
- Tipo de evento
- Endereço IP
- User Agent (navegador/dispositivo)
- Timestamp
- Metadados adicionais (ex: ID da conexão, tipo de sync, erros, etc.)

## Como Usar

### Visualizar Logs no Admin

1. Acesse o Django Admin em `/admin/`
2. Vá para "Authentication" > "User Activity Logs"
3. Você verá todos os eventos com:
   - Filtros por tipo de evento e data
   - Busca por usuário, IP ou user agent
   - Visualização colorida dos tipos de evento
   - Metadados formatados em JSON

### Comando de Estatísticas

Para visualizar estatísticas agregadas via linha de comando:

```bash
# Estatísticas dos últimos 30 dias (padrão)
python manage.py user_activity_stats

# Estatísticas dos últimos 7 dias
python manage.py user_activity_stats --days 7

# Filtrar por usuário específico
python manage.py user_activity_stats --user joao@email.com

# Filtrar por tipo de evento
python manage.py user_activity_stats --event-type login

# Combinar filtros
python manage.py user_activity_stats --days 14 --user joao@email.com
```

O comando exibe:
- Total de eventos
- Eventos por tipo
- Top 10 usuários mais ativos
- Estatísticas de login
- Atividade de conexões bancárias
- Atividade de sincronização (com taxa de sucesso)
- Últimos 10 eventos

### Registrar Eventos Manualmente

Se você precisar registrar eventos customizados em outras partes do código:

```python
from apps.authentication.models import UserActivityLog
from apps.authentication.signals import get_client_ip

# Registrar um evento
UserActivityLog.log_event(
    user=request.user,
    event_type='custom_event',  # deve estar em EVENT_TYPES
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', ''),
    # Metadados adicionais
    custom_field='valor',
    outro_campo=123
)
```

## Tipos de Eventos Disponíveis

- `login` - Login do usuário
- `logout` - Logout do usuário
- `bank_connection_created` - Conexão bancária criada
- `bank_connection_updated` - Conexão bancária atualizada
- `bank_connection_deleted` - Conexão bancária excluída
- `sync_started` - Sincronização iniciada
- `sync_completed` - Sincronização concluída
- `sync_failed` - Sincronização falhou
- `password_reset_requested` - Solicitação de reset de senha
- `password_changed` - Senha alterada
- `profile_updated` - Perfil atualizado

## Consultas Úteis no Admin ou Shell

### Usuários que logaram nos últimos 7 dias
```python
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import UserActivityLog

last_week = timezone.now() - timedelta(days=7)
recent_logins = UserActivityLog.objects.filter(
    event_type='login',
    created_at__gte=last_week
).values('user__email').distinct()
```

### Usuários que criaram conexões mas nunca sincronizaram
```python
users_with_connections = UserActivityLog.objects.filter(
    event_type='bank_connection_created'
).values_list('user', flat=True).distinct()

users_who_synced = UserActivityLog.objects.filter(
    event_type='sync_started'
).values_list('user', flat=True).distinct()

never_synced = set(users_with_connections) - set(users_who_synced)
```

### Taxa de sucesso de sincronização por usuário
```python
from django.db.models import Count, Q

sync_stats = UserActivityLog.objects.filter(
    event_type__in=['sync_started', 'sync_completed', 'sync_failed']
).values('user__email').annotate(
    started=Count('id', filter=Q(event_type='sync_started')),
    completed=Count('id', filter=Q(event_type='sync_completed')),
    failed=Count('id', filter=Q(event_type='sync_failed'))
)
```

## Performance

O modelo `UserActivityLog` está otimizado com:
- Índices nas colunas mais consultadas (user, event_type, created_at)
- Índice composto para consultas comuns
- Campos apenas leitura no admin para evitar edições acidentais

## Manutenção

### Limpeza de Logs Antigos

Para manter o banco de dados limpo, você pode criar um cronjob ou tarefa Celery para deletar logs antigos:

```python
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import UserActivityLog

# Deletar logs com mais de 90 dias
cutoff_date = timezone.now() - timedelta(days=90)
UserActivityLog.objects.filter(created_at__lt=cutoff_date).delete()
```

## Privacidade e LGPD

O sistema captura endereços IP e user agents para fins de segurança e auditoria. Certifique-se de:

1. Informar os usuários na política de privacidade
2. Implementar retenção de dados apropriada
3. Permitir que usuários solicitem exclusão de seus dados
4. Proteger acesso aos logs (apenas admins)
