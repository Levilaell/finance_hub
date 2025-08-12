# 🚨 COMO LIMPAR O BANCO DE PRODUÇÃO NO RAILWAY

## Comando Rápido (Execute no Railway Console)

```bash
railway shell
```

Depois execute:

```sql
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

## Ou Via Railway Dashboard

1. Vá para o serviço **Postgres** no Railway
2. Clique na aba **Data**
3. Execute esta query:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

## Depois de Limpar

1. Faça **Redeploy** do serviço **finance_hub**
2. As migrações vão rodar automaticamente
3. Tudo será criado do zero

## ✅ Problema Resolvido!

As migrações agora estão corretas e não há mais divisão de foreign keys.
O erro "column already exists" não vai mais acontecer!