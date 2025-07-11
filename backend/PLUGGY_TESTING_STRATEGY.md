# 🧪 Estratégia de Teste com Pluggy

## 1. Fase de Desenvolvimento (Agora)

### Usar Credenciais SANDBOX do Pluggy
1. Criar conta em https://dashboard.pluggy.ai
2. Obter Client ID e Secret do ambiente Sandbox
3. Configurar no `.env` local:
```env
PLUGGY_CLIENT_ID=seu-sandbox-client-id
PLUGGY_CLIENT_SECRET=seu-sandbox-client-secret
PLUGGY_BASE_URL=https://api.pluggy.ai  # Mesma URL!
```

### O que você PODE fazer no Sandbox:
- ✅ Conectar suas contas bancárias reais
- ✅ Ver suas transações reais
- ✅ Testar todos os fluxos
- ✅ Validar categorização
- ✅ Testar sincronização
- ✅ Até 20 conexões grátis

### O que NÃO precisa de produção:
- Todas as funcionalidades são idênticas
- Os dados são reais (não são mock)
- A integração é a mesma

## 2. Configuração Rápida

```bash
# Backend
cd backend
# Criar arquivo .env
cat > .env << EOF
SECRET_KEY=development-secret-key-123
DEBUG=True
PLUGGY_CLIENT_ID=<cole-aqui-seu-sandbox-id>
PLUGGY_CLIENT_SECRET=<cole-aqui-seu-sandbox-secret>
EOF

# Reiniciar servidor
python manage.py runserver
```

## 3. Fluxo de Teste Completo

### Passo 1: Conectar Banco Real
1. Vá em Contas Bancárias
2. Clique em "Conectar Banco"
3. Escolha seu banco
4. Use suas credenciais reais
5. Complete 2FA se necessário

### Passo 2: Validar Dados
- ✅ Saldo correto?
- ✅ Transações aparecem?
- ✅ Categorização funciona?
- ✅ Sincronização automática?

### Passo 3: Testar Edge Cases
- Múltiplas contas
- Diferentes bancos
- Reconexão
- Erros de autenticação

## 4. Quando Migrar para Produção?

Só mude para credenciais de produção quando:
- [ ] Tiver clientes pagantes
- [ ] Precisar mais de 20 conexões
- [ ] Sistema estiver 100% estável

## 5. Diferença de Configuração

### Desenvolvimento/Staging (Sandbox)
```env
PLUGGY_CLIENT_ID=sandbox_abc123...
PLUGGY_CLIENT_SECRET=sandbox_xyz789...
```

### Produção
```env
PLUGGY_CLIENT_ID=live_abc123...
PLUGGY_CLIENT_SECRET=live_xyz789...
```

**É só isso! O código é o mesmo!**

## 💡 Dica Pro

Use suas 20 conexões sandbox assim:
- 5 para seus testes pessoais
- 5 para beta testers
- 5 para demonstrações
- 5 como reserva

Quando acabar, já terá validado tudo!