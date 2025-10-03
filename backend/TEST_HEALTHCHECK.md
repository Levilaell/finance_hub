# 🔍 Testar Healthcheck Manualmente

## Problema
Deploy fica em "DEPLOYING" infinitamente, mas app está rodando.

## Teste 1: Verificar se /health/ responde localmente no container

```bash
# Via Railway CLI
railway run curl http://localhost:8080/health/

# Deve retornar:
# {"status":"healthy","database":"connected","python_version":"3.11.10"}
```

## Teste 2: Verificar logs do healthcheck

```bash
railway logs

# Procure por:
# 🏥 HEALTHCHECK: GET /health/ from ...
# ✅ HEALTHCHECK OK: ...
```

Se NÃO aparecer essas linhas, o Railway não está conseguindo fazer a requisição.

## Teste 3: Acessar via domínio público

```bash
curl https://financehub-production.up.railway.app/health/

# Deve retornar:
# {"status":"healthy","database":"connected","python_version":"3.11.10"}
```

## Teste 4: Verificar Settings no Railway

**Railway Dashboard → Settings → Deploy:**

- ✅ Healthcheck Path = `/health/`
- ✅ Healthcheck Timeout = `100` segundos
- ✅ Port = `8080`

**IMPORTANTE:** O healthcheck path precisa ter a barra final: `/health/` (não `/health`)

## Teste 5: Forçar redeploy

```bash
railway redeploy
```

## 🔧 Possíveis Soluções

### Solução 1: Desabilitar Healthcheck Temporariamente

No Railway Dashboard:
1. Settings → Deploy
2. Healthcheck Path → **Deletar** (deixar vazio)
3. Salvar

Isso fará o deploy completar, mas sem verificação de health.

### Solução 2: Aumentar Timeout

- Healthcheck Timeout → `300` (5 minutos)

### Solução 3: Usar porta diferente

Verificar se Railway está esperando porta diferente:
```bash
railway vars

# Ver se PORT está configurado
```

## 🐛 Debug Avançado

### Ver variáveis de ambiente no container:

```bash
railway run env | grep -i railway
```

### Testar healthcheck de dentro do container:

```bash
railway shell

# Dentro do shell:
curl http://localhost:8080/health/
wget -O- http://localhost:8080/health/
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health/').read())"
```

### Ver processos rodando:

```bash
railway run ps aux
```

## 📊 Checklist de Verificação

- [ ] App inicia sem erros
- [ ] Gunicorn escuta em porta 8080
- [ ] `/health/` retorna 200 OK via curl
- [ ] ALLOWED_HOSTS aceita Railway domains
- [ ] Middleware não bloqueia /health/
- [ ] railway.json tem healthcheckPath correto
- [ ] Timeout é suficiente (100s)
- [ ] Logs mostram requisições ao /health/

## ⚠️ Workaround Final

Se nada funcionar, desabilite o healthcheck:

**railway.json:**
```json
{
  "deploy": {
    "startCommand": "bash start.sh",
    "healthcheckPath": null,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

O deploy completará, mas sem validação de health.
