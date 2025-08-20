# 🧪 Cenários de Teste - Django Admin

Documentação completa para testar o sistema de planos, limites e funcionalidades através do Django Admin.

## 🚀 Configuração Inicial

### 1. Preparar Ambiente
```bash
cd backend
python manage.py runserver
# Acesse: http://localhost:8000/admin/
```

### 2. Criar Dados de Teste
```bash
# Criar planos padrão (se não existirem)
python manage.py create_subscription_plans

# Criar superuser (se necessário)
python manage.py createsuperuser --email admin@teste.com
```

---

## 📊 Cenário 1: Teste de Limites de Transações

### **Objetivo**: Verificar comportamento quando usuário atinge limites de transações

#### **Setup**
1. **Admin → Usuários** → Selecione ou crie usuário
2. **Admin → Empresas** → Encontre empresa do usuário
3. **Configurar empresa:**
   - Plano: **Starter** (500 transações/mês)
   - Status: `active`
   - `current_month_transactions`: 0

#### **Teste 1.1: Warning 80%**
1. **Admin → Empresas** → Editar empresa
2. Alterar `current_month_transactions` para **400** (80% de 500)
3. **Testar via comando:**
   ```bash
   python manage.py test_plan_limits --email usuario@teste.com
   ```
4. **Resultado esperado:**
   - ✅ Limite não atingido
   - ⚠️ Warning: "Você já utilizou 80% do seu limite"

#### **Teste 1.2: Warning 90%**
1. Alterar `current_month_transactions` para **450** (90% de 500)
2. **Testar sincronização** no frontend ou via API
3. **Resultado esperado:**
   - ✅ Transação criada com sucesso
   - ⚠️ Warning: "Próximo do limite! Considere upgrade"
   - 💡 Sugestão upgrade: Professional

#### **Teste 1.3: Limite 100%**
1. Alterar `current_month_transactions` para **500** (100% de 500)
2. **Testar criação de transação**
3. **Resultado esperado:**
   - ❌ Status: 429 Too Many Requests
   - ❌ Erro: "Limite de transações atingido"
   - 💡 Upgrade sugerido para Professional

#### **Validação**
```bash
# Comando para simular diferentes percentuais
python manage.py test_plan_limits --email usuario@teste.com --simulate 80
python manage.py test_plan_limits --email usuario@teste.com --simulate 90
python manage.py test_plan_limits --email usuario@teste.com --simulate 100
```

---

## 🏦 Cenário 2: Teste de Limites de Contas Bancárias

### **Objetivo**: Verificar comportamento ao atingir limite de contas bancárias

#### **Setup**
1. **Admin → Empresas** → Selecionar empresa
2. **Configurar:**
   - Plano: **Starter** (1 conta bancária)
   - Status: `active`

#### **Teste 2.1: Dentro do Limite**
1. **Admin → Banking → Bank Accounts** → Verificar contas ativas
2. Se empresa tem 0 contas ativas
3. **Testar conexão** via Pluggy no frontend
4. **Resultado esperado:**
   - ✅ Conexão permitida
   - ✅ Conta bancária criada

#### **Teste 2.2: Limite Atingido**
1. Garantir que empresa já tem **1 conta ativa**
2. **Testar nova conexão** via Pluggy
3. **Resultado esperado:**
   - ❌ Erro: "Limite de contas bancárias atingido"
   - 💡 Sugestão upgrade para Professional (3 contas)

#### **Validação via Comando**
```bash
python manage.py test_plan_limits --email usuario@teste.com
# Verificar: "Can add bank account: False/True"
```

---

## 🤖 Cenário 3: Teste de AI Insights

### **Objetivo**: Verificar funcionalidades de IA por plano

#### **Setup Starter** (Sem IA)
1. **Admin → Empresas** → Configurar:
   - Plano: **Starter**
   - Status: `active`

#### **Teste 3.1: Starter - IA Bloqueada**
1. **Tentar usar AI** no frontend (insights, categorização)
2. **Resultado esperado:**
   - ❌ Funcionalidade bloqueada
   - 💡 "Upgrade para Professional para usar IA"

#### **Setup Professional** (10 requests/mês)
1. **Admin → Empresas** → Alterar:
   - Plano: **Professional**
   - `current_month_ai_requests`: 0

#### **Teste 3.2: Professional - IA Disponível**
1. **Usar AI insights** no frontend
2. **Verificar contador** via Admin
3. **Resultado esperado:**
   - ✅ IA funciona
   - 📊 `current_month_ai_requests` incrementa

#### **Teste 3.3: Professional - Limite IA**
1. **Admin → Empresas** → Alterar:
   - `current_month_ai_requests`: 10 (100% do limite)
2. **Tentar usar IA** novamente
3. **Resultado esperado:**
   - ❌ "Limite de requisições IA atingido"
   - 💡 Upgrade para Enterprise (ilimitado)

#### **Setup Enterprise** (Ilimitado)
1. **Admin → Empresas** → Alterar:
   - Plano: **Enterprise**

#### **Teste 3.4: Enterprise - IA Ilimitada**
1. **Usar IA** múltiplas vezes
2. **Resultado esperado:**
   - ✅ Sempre disponível
   - 📊 Contador incrementa sem bloqueio

---

## ⏰ Cenário 4: Teste de Trial e Expiração

### **Objetivo**: Verificar comportamento de trials expirados

#### **Setup Trial Ativo**
1. **Admin → Empresas** → Configurar:
   - Status: `trial`
   - `trial_ends_at`: Data futura (ex: +7 dias)
   - Plano: **Professional**

#### **Teste 4.1: Trial Ativo**
1. **Usar sistema** normalmente
2. **Admin → Usuários** → Verificar coluna "Trial/Early Access Days"
3. **Resultado esperado:**
   - ✅ Todas funcionalidades disponíveis
   - 🟢 Mostra "X dias restantes" (verde/laranja/vermelho)

#### **Teste 4.2: Trial Expirando (3 dias)**
1. **Admin → Empresas** → Alterar:
   - `trial_ends_at`: Data em 3 dias
2. **Resultado esperado:**
   - ⚠️ Interface mostra aviso de expiração
   - 🔴 Admin mostra "3 dias" em vermelho

#### **Teste 4.3: Trial Expirado**
1. **Admin → Empresas** → Alterar:
   - `trial_ends_at`: Data no passado
   - Status: `expired`
2. **Tentar usar sistema**
3. **Resultado esperado:**
   - ❌ Funcionalidades bloqueadas
   - 💳 Solicita pagamento/upgrade

#### **Filtros de Trial no Admin**
- **Admin → Usuários** → Filtrar por "Trial Expirando"
  - "Próximos 3 dias"
  - "Próximos 7 dias" 
  - "Expirado"

---

## 🎯 Cenário 5: Early Access

### **Objetivo**: Testar funcionalidades de acesso antecipado

#### **Setup Early Access**
1. **Admin → Empresas** → Configurar:
   - `is_early_access`: ✅ True
   - `early_access_expires_at`: Data futura
   - `used_invite_code`: "BETA2024"
   - Status: `early_access`

#### **Teste 5.1: Early Access Ativo**
1. **Usar sistema** com recursos especiais
2. **Admin** → Verificar visual diferenciado
3. **Resultado esperado:**
   - 🟣 Interface mostra "Early Access"
   - ✨ Recursos especiais disponíveis

#### **Teste 5.2: Early Access Expirado**
1. **Admin → Empresas** → Alterar:
   - `early_access_expires_at`: Data no passado
2. **Resultado esperado:**
   - ⚠️ Sistema solicita upgrade para plano pago
   - 🔴 Admin mostra "Early Access Expired"

#### **Gerenciar Convites**
```bash
python manage.py create_early_access_invites
```
- **Admin → Companies → Early Access Invites**
- Criar, editar, marcar como usado

---

## 💳 Cenário 6: Upgrade e Downgrade de Planos

### **Objetivo**: Testar mudanças de plano e seus efeitos

#### **Teste 6.1: Upgrade Starter → Professional**
1. **Estado inicial:**
   - Plano: Starter (500 transações, 1 conta, sem IA)
   - `current_month_transactions`: 400
2. **Admin → Empresas** → Alterar plano para **Professional**
3. **Resultado esperado:**
   - ✅ Limites aumentam: 500 → 2500 transações
   - ✅ Contas bancárias: 1 → 3
   - ✅ IA habilitada (10 requests/mês)

#### **Teste 6.2: Upgrade Professional → Enterprise**
1. **Estado inicial:**
   - Plano: Professional
   - Próximo do limite em algum recurso
2. **Alterar para Enterprise**
3. **Resultado esperado:**
   - ✅ Todos limites ficam "ilimitados" (99999)
   - ✅ Todas features habilitadas

#### **Teste 6.3: Downgrade Enterprise → Professional**
1. **Estado inicial:**
   - Plano: Enterprise
   - Uso alto (ex: 5000 transações, 5 contas)
2. **Alterar para Professional**
3. **Comportamento a verificar:**
   - ❓ Sistema permite? (discussão de regra de negócio)
   - ❓ Como trata contas excedentes?

---

## 📊 Cenário 7: Monitoramento e Relatórios

### **Objetivo**: Testar dashboards e relatórios do admin

#### **Setup Dados Variados**
```bash
# Criar várias empresas com diferentes estados
python manage.py create_user_company
```

#### **Teste 7.1: Resumo de Assinaturas**
1. **Admin → Usuários** → Selecionar múltiplos usuários
2. **Actions** → "Mostrar resumo de assinaturas"
3. **Resultado esperado:**
   - 📊 Estatísticas por plano
   - 📊 Distribuição por status
   - ⚠️ Trials expirando

#### **Teste 7.2: Filtros Avançados**
- **Admin → Usuários** → Testar filtros:
  - Por plano de assinatura
  - Por status de assinatura
  - Por trial expirando (3/7 dias)
  - Sem empresa

#### **Teste 7.3: Dashboard Individual**
1. **Admin → Usuários** → Abrir usuário específico
2. **Verificar seção "Detalhes da Assinatura"**
3. **Resultado esperado:**
   - 📋 Info completa da empresa
   - 💰 Detalhes do plano e preços
   - 📊 Uso atual vs limites
   - 💳 Status de pagamento

---

## 🔧 Comandos de Debug e Validação

### **Comandos Úteis para Testes**
```bash
# Testar limites específicos
python manage.py test_plan_limits --email usuario@teste.com

# Simular uso percentual
python manage.py test_plan_limits --email usuario@teste.com --simulate 90

# Verificar contadores
python manage.py debug_usage_counter --email usuario@teste.com

# Corrigir contadores (se necessário)
python manage.py fix_duplicate_counter

# Criar empresas para usuários órfãos
python manage.py create_user_company

# Verificar planos
python manage.py list_plans_for_stripe
```

### **Endpoints API para Teste Manual**
```bash
# Verificar limites via API
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/companies/current/

# Testar criação de transação (pode falhar por limite)
curl -X POST -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "description": "Teste"}' \
  http://localhost:8000/api/banking/transactions/
```

---

## ✅ Checklist de Validação

### **Para cada cenário testado, verificar:**

#### **Interface Admin**
- [ ] Status visual correto (cores, ícones)
- [ ] Campos calculados atualizados
- [ ] Filtros funcionando
- [ ] Actions em massa funcionando

#### **Frontend/API**
- [ ] Mensagens de erro apropriadas
- [ ] Warnings de limite exibidos
- [ ] Funcionalidades bloqueadas quando necessário
- [ ] Sugestões de upgrade aparecem

#### **Banco de Dados**
- [ ] Contadores atualizados corretamente
- [ ] Flags de notificação corretas
- [ ] Status de plano consistente

#### **Comportamento do Sistema**
- [ ] Limites respeitados
- [ ] Features habilitadas/desabilitadas por plano
- [ ] Upgrades/downgrades funcionando
- [ ] Early access funcionando

---

## 🚨 Problemas Comuns e Soluções

### **Contadores Incorretos**
```bash
python manage.py fix_duplicate_counter --dry-run
python manage.py fix_duplicate_counter
```

### **Usuário Sem Empresa**
```bash
python manage.py create_user_company --email usuario@teste.com
```

### **Planos Desatualizados**
```bash
python manage.py create_subscription_plans
```

### **Cache de Limites**
- Reiniciar servidor Django
- Verificar Redis (se usando)

---

## 📝 Notas para Testes

1. **Sempre fazer backup** antes de alterar dados importantes
2. **Usar dados de teste** separados da produção
3. **Verificar logs** durante os testes para erros
4. **Testar tanto via Admin quanto via API/Frontend**
5. **Documentar comportamentos inesperados** para correção

**Status: 📋 Documento criado - Ready para testes!**