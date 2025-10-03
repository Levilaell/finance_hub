# 🔧 Fix: Migration Error

## Problema
```
django.db.utils.ProgrammingError: relation "banking_transaction" does not exist
```

A migration `0002` está tentando rodar antes da `0001_initial`.

## ✅ Solução Rápida (Recomendado)

**Railway Dashboard → PostgreSQL → Reset Database**

1. Railway Dashboard
2. Selecione o PostgreSQL service
3. Settings → Danger Zone
4. "Reset Database" (ou "Delete Service" e criar novo)
5. Fazer redeploy do backend

O start.sh criará tudo do zero corretamente.

## 🔧 Solução Manual (se quiser manter dados)

### Via Railway CLI:

```bash
# Conectar ao banco
railway run python manage.py dbshell

# No psql, limpar tabela de migrations:
DELETE FROM django_migrations WHERE app = 'banking';
\q

# Fake a primeira migration
railway run python manage.py migrate banking 0001 --fake

# Rodar migrations restantes
railway run python manage.py migrate
```

### Ou usar --fake-initial:

```bash
railway run python manage.py migrate --fake-initial
```

## 📋 Prevenir no Futuro

Adicionar ao `start.sh` (linha 51):

```bash
# Try migration with fallback
python manage.py migrate --noinput || \
    python manage.py migrate --fake-initial --noinput || \
    { echo "Migration failed!"; exit 1; }
```

## ⚠️ Por que isso aconteceu?

- O Railway pode ter criado o schema parcialmente em um deploy anterior
- A tabela `django_migrations` registrou a migration como aplicada
- Mas a tabela `banking_transaction` não foi criada
- Resultado: Django pula a 0001 e tenta rodar a 0002

## 🚀 Recomendação

**RESET do banco é mais limpo** - você não tem dados em produção ainda, então é seguro.

No Railway:
1. PostgreSQL service → Settings
2. Scroll down → Reset Database
3. Aguardar reset
4. Backend fará redeploy automático
5. Migrations rodarão do zero sem erro
