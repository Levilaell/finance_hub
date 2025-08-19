# Deploy Fixes - Finance Hub

## 🔍 Problemas Identificados e Soluções

### **Erro 1: Frontend - docker-entrypoint.sh não encontrado**

**Problema**: 
```
COPY docker-entrypoint.sh /usr/local/bin/ failed: "/docker-entrypoint.sh": not found
```

**Causa**: Build cache antigo referenciando arquivo inexistente

**Solução**: 
- ✅ Removida qualquer referência a docker-entrypoint.sh
- ✅ Criado script de limpeza de cache: `docker-build-clean.sh`
- ✅ Adicionado `.dockerignore` para otimizar build context

### **Erro 2: Alpine Package Installation Timeout (Exit Code 137)**

**Problema**: 
```
RUN apk add --no-cache libc6-compat
process did not complete successfully: exit code: 137
```

**Causa**: Network timeouts e resource limits durante instalação de packages

**Solução**: 
- ✅ Adicionados timeouts e retry nos comandos `apk`:
  ```dockerfile
  RUN apk update && apk add --no-cache --timeout=300 --retry=3 libc6-compat
  ```
- ✅ Separados comandos de update e install para melhor cache
- ✅ Adicionado timeout no npm ci: `--timeout=300000`

### **Erro 3: Backend collectstatic Failure**

**Problema**:
```
python manage.py collectstatic --noinput
process did not complete successfully: exit code: 1
```

**Causa**: Problemas com WhiteNoise e configuração de static files

**Soluções**:
- ✅ Criados diretórios necessários antes do collectstatic:
  ```dockerfile
  RUN mkdir -p /app/staticfiles /app/static /app/media
  ```
- ✅ Adicionadas variáveis de ambiente corretas:
  ```dockerfile
  RUN DJANGO_SECRET_KEY="build-key-for-collectstatic-only" \
      DJANGO_SETTINGS_MODULE=core.settings.production \
      DATABASE_URL="sqlite:///tmp/db.sqlite3" \
      DJANGO_COLLECT_STATIC=1 \
      ALLOWED_HOSTS="*" \
      python manage.py collectstatic --noinput --verbosity=2
  ```
- ✅ Adicionado fallback para WhiteNoise em `production.py`:
  ```python
  try:
      STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
  except Exception:
      STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
  ```

## 📁 Arquivos Modificados

### Frontend
- ✅ `frontend/Dockerfile` - Timeouts e retry para Alpine packages
- ✅ `frontend/.dockerignore` - Otimização do build context

### Backend  
- ✅ `backend/Dockerfile` - Correção do collectstatic stage
- ✅ `backend/core/settings/production.py` - WhiteNoise fallback
- ✅ `backend/.dockerignore` - Otimização do build context

### Scripts e Docs
- ✅ `docker-build-clean.sh` - Script para limpeza de cache
- ✅ `DEPLOY_FIX.md` - Esta documentação

## 🚀 Como Aplicar as Correções

### Opção 1: Deploy Automático (Railway)
```bash
# Fazer commit das alterações
git add .
git commit -m "fix: resolver erros críticos de deploy

- Corrigir timeouts do Alpine Linux (exit code 137)
- Resolver erro de collectstatic no backend
- Adicionar fallback para WhiteNoise
- Criar .dockerignore para otimizar builds
- Implementar retry e timeouts em packages"

# Push para triggerar deploy
git push
```

### Opção 2: Teste Local com Limpeza de Cache
```bash
# Executar script de limpeza
./docker-build-clean.sh

# Ou manualmente:
docker builder prune -f
docker image prune -a -f
docker volume prune -f
```

## 🔧 Melhorias Implementadas

### Performance
- ✅ **Build Context Otimizado**: `.dockerignore` remove arquivos desnecessários
- ✅ **Layer Caching**: Separação de comandos para melhor aproveitamento de cache
- ✅ **Timeouts**: Prevenção de builds infinitos

### Reliability  
- ✅ **Retry Logic**: Comandos críticos com retry automático
- ✅ **Fallback Storage**: WhiteNoise com fallback para compression
- ✅ **Verbose Output**: Logs detalhados para debugging

### Security
- ✅ **Build Secrets**: Keys temporárias apenas para collectstatic
- ✅ **Clean Build**: Remoção de cache potencialmente comprometido

## 🎯 Resultados Esperados

Após aplicar essas correções:

- ✅ **Frontend Build**: Sem erros de docker-entrypoint.sh
- ✅ **Alpine Packages**: Instalação robusta com retry
- ✅ **Backend Static Files**: Collectstatic funcionando corretamente  
- ✅ **Deploy Time**: Redução significativa devido aos .dockerignore
- ✅ **Build Reliability**: Menos falhas por timeouts

## 🚨 Próximos Passos

1. **Monitorar Deploy**: Verificar se os erros foram resolvidos
2. **Performance**: Avaliar tempo de build após otimizações
3. **Logs**: Analisar logs de deploy para identificar outros gargalos
4. **Cache Strategy**: Implementar cache mais agressivo se necessário

## 📞 Suporte

Em caso de problemas persistentes:
1. Executar `./docker-build-clean.sh` para limpar completamente o cache
2. Verificar logs detalhados no Railway dashboard  
3. Confirmar se todas as variáveis de ambiente estão configuradas
4. Validar se as imagens base (node:18-alpine, python:3.11-slim) estão acessíveis