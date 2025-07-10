# Como Funciona a Conexão Bancária com Pluggy

## Visão Geral

O Pluggy é um **agregador bancário** que permite conectar com bancos brasileiros de forma segura. Ele funciona de forma similar ao que você vê em apps como GuiaBolso, Organizze, ou Mobills.

## Fluxo de Conexão

### 1. Usuário Inicia Conexão
- Clica em "Conectar via Open Banking"
- Seleciona o banco desejado
- Sistema cria um token de conexão único

### 2. Pluggy Connect
- Abre uma janela/popup do Pluggy
- Usuário faz login **diretamente no banco**
- O Pluggy não vê nem armazena a senha
- Banco valida as credenciais

### 3. Autorização
- Usuário autoriza o Pluggy a acessar seus dados
- Pode incluir autenticação 2FA (token, SMS, etc)
- Banco cria um token de acesso temporário

### 4. Sincronização
- Pluggy busca as contas disponíveis
- Importa transações dos últimos 90 dias
- Salva tudo no nosso sistema
- Atualiza periodicamente

## Diferenças do Fluxo Anterior

### ❌ Fluxo Manual (Antigo)
```
1. Usuário seleciona banco
2. Sistema pede agência e conta ← NÃO NECESSÁRIO
3. Usuário digita manualmente ← NÃO NECESSÁRIO
4. Sistema tenta conectar
```

### ✅ Fluxo Pluggy (Correto)
```
1. Usuário seleciona banco
2. Abre Pluggy Connect
3. Usuário faz login no banco
4. Pluggy busca dados automaticamente
```

## Segurança

1. **Credenciais**: Nunca passam pelo nosso sistema
2. **Tokens**: Usamos apenas tokens de acesso temporários
3. **Criptografia**: Toda comunicação é criptografada
4. **Conformidade**: Pluggy é certificado pelo Banco Central

## Dados Obtidos

Após a conexão, o Pluggy fornece:

- **Contas**: Corrente, Poupança, etc
- **Saldos**: Atual e disponível
- **Transações**: Histórico completo
- **Detalhes**: Descrição, categoria, data, valor

## Exemplo Visual

```
[Usuário] → [Nosso App] → [Pluggy Connect] → [Banco]
                ↓                                ↓
           Token criado                   Login direto
                ↓                                ↓
           Abre popup                    Valida credenciais
                ↓                                ↓
         Aguarda retorno                  Autoriza acesso
                ↓                                ↓
           Recebe dados ← [Pluggy API] ← Envia dados
```

## Bancos Suportados

O Pluggy suporta os principais bancos brasileiros:

- Banco do Brasil
- Bradesco
- Caixa Econômica Federal
- Itaú
- Santander
- Nubank
- Inter
- C6 Bank
- E muitos outros...

## Perguntas Frequentes

### Por que não preciso digitar agência e conta?

O Pluggy acessa diretamente o internet banking e obtém todas as suas contas automaticamente.

### É seguro?

Sim! O Pluggy é regulamentado pelo Banco Central e segue todas as normas de segurança do Open Banking.

### Posso conectar múltiplas contas?

Sim! Cada banco conectado pode ter várias contas (corrente, poupança, etc).

### Com que frequência os dados são atualizados?

- Saldo: A cada 4 horas
- Transações: A cada 6 horas
- Manual: Quando você clicar em "Sincronizar"

### O que acontece se eu mudar minha senha do banco?

Você precisará reconectar a conta através do Pluggy Connect.