# Documentação Completa da API Pluggy

## Visão Geral

A Pluggy é uma API de Open Finance que permite conectar-se às contas dos usuários para acessar dados financeiros enriquecidos de instituições financeiras. Uma solução simples e robusta para você acessar uma ampla cobertura de dados enriquecidos e de instituições financeiras.

A Pluggy Brasil Instituição de Pagamento LTDA (CNPJ: 37.943.755/0001-30) é autorizada pelo Banco Central do Brasil como Iniciadora de Transação de Pagamento (ITP).

## Conceitos Fundamentais

### Connector (Conector)
Um conector representa um worker que recupera informações de uma instituição. Esta instituição pode representar uma entidade de qualquer setor, como um banco ou qualquer aplicação fintech como MercadoPago ou Nubank.

### User (Usuário)
O usuário final da sua aplicação que requer acesso aos seus dados pessoais através de um conector.

### Item
Um Item é a representação de uma conexão com um Conector específico de uma Instituição e serve como ponto de entrada para acessar o conjunto de produtos recuperados do usuário que deu seu consentimento para coletar seus dados.

## Autenticação

A autenticação na Pluggy é dividida em dois tipos de acesso:

### 1. API Key
Este token de acesso tem tempo de expiração de 2 horas e é destinado a ser usado por aplicações backend para recuperar dados dos usuários.

**Permissões:**
- Ler dados do usuário para todos os produtos (Conta, Transação, Investimento, Identidade, Oportunidade)
- Configurar Webhooks
- Criar, Atualizar e Deletar Items
- Revisar Conectores e árvore de categorias de transações

**Como obter:**
```bash
curl --location --request POST "https://api.pluggy.ai/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

### 2. Connect Token
Este é um token de acesso limitado que expira 30 minutos após a criação. É destinado a ser usado por aplicações Frontend (Web ou Mobile) para autenticar com a Pluggy.

**Como obter:**
```bash
curl --location --request POST "https://api.pluggy.ai/connect_token" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: YOUR_API_KEY" \
  -d '{
    "itemId": "ITEM_ID_TO_UPDATE",
    "options": {
      "webhookUrl": "https://www.myapi.com/notifications",
      "clientUserId": "my-user-id-12345",
      "avoidDuplicates": true
    }
  }'
```

## Endpoints Principais

### Base URL
- **Produção:** `https://api.pluggy.ai`

### Configuração Base
A API da Pluggy é uma API RESTful baseada em requisições e respostas JSON, então todas as requisições devem ter o header Content-Type configurado como application/json.

### Headers Obrigatórios
```
Content-Type: application/json
X-API-KEY: YOUR_API_KEY
```

## Conectores

### Listar Conectores
```
GET /connectors
```

Os dados do conector mudam de tempos em tempos, então é importante sempre recuperar os dados mais recentes da nossa API e evitar armazená-los.

### Tipos de Conectores

1. **Conectores Pluggy (não regulado):**
   - Conectores criados pela Pluggy com tecnologia proprietária
   - Acesso direto às instituições financeiras

2. **Conectores Open Finance (regulado):**
   - Conectores que acessam a estrutura regulada pelo Banco Central
   - Dados compartilhados através do consentimento do usuário

## Items (Conexões)

### Criar Item
```
POST /items
```

Para criar um Item, a maneira mais fácil, polida, testada em batalha e menos propensa a erros para um usuário, é interagir com nosso Pluggy Connect Widget.

### Recuperar Item Específico
```
GET /items/{id}
```

### Atualizar Item
```
PATCH /items/{id}
```

### Deletar Item
```
DELETE /items/{id}
```

### Auto-Sync
Quando um Item é criado, ele terá uma referência aos parâmetros do usuário armazenados e credenciais necessárias para executar a coleta de dados da instituição. Isso permite que a Pluggy execute nosso processo de auto-sync, que implica a cada 24/12/8 horas (baseado na sua assinatura), coletaremos os dados de transação dos últimos dias.

## Contas (Accounts)

### Listar Contas por Item
```
GET /accounts?itemId={itemId}
```

### Recuperar Conta Específica
```
GET /accounts/{id}
```

Cada item tem um conjunto de Contas relacionadas à conexão do usuário com essa instituição específica. Essas contas representam na Pluggy um Produto que pode ser coletado e atualizado em sincronizações diárias.

## Transações

### Listar Transações por Conta
```
GET /transactions?accountId={accountId}
```

### Recuperar Transação Específica
```
GET /transactions/{id}
```

### Atualizar Categoria da Transação
```
PATCH /transactions/{id}
```

Transações são categorizadas em tempo real após serem coletadas da instituição. Você pode recuperar até 12 meses de dados de transações.

## Investimentos

### Listar Investimentos
```
GET /investments?itemId={itemId}
```

### Recuperar Investimento Específico
```
GET /investments/{id}
```

## Webhooks

Um Webhook é uma ferramenta que permite receber uma notificação para um determinado evento. Permite configurar uma URL HTTPS em nossa plataforma para determinados eventos e você receberá um evento JSON POST nessa URL, com dados específicos do evento.

### Eventos Disponíveis

#### Items:
- `item/created`
- `item/updated`
- `item/error`
- `item/login_succeeded`

#### Transações:
- `transactions/created`
- `transactions/updated`
- `transactions/deleted`

#### Pagamentos:
- `payment_intent/created`
- `payment_intent/completed`
- `payment_intent/error`
- `scheduled_payment/created`
- `scheduled_payment/completed`
- `scheduled_payment/error`
- `scheduled_payment/canceled`

### Criar Webhook
```
POST /webhooks
```

### Configuração de Webhook
Quando enviamos uma notificação webhook, esperamos que a primeira coisa que você faça ao processar o evento seja fazer um GET /items/{id} para recuperar os dados mais recentes.

### Retry Policy
Quando há uma falha, tentamos novamente a notificação até 3 vezes, com um minuto entre as tentativas. Depois disso, a notificação será perdida.

## Pluggy Connect Widget

O Pluggy Connect Widget é uma interface gráfica para conectar contas de usuários.

### Implementação React
```javascript
import { PluggyConnect } from 'react-pluggy-connect';

<PluggyConnect
  connectToken={connectToken}
  includeSandbox={true}
  onClose={() => setIsWidgetOpen(false)}
  onSuccess={onSuccess}
/>
```

### Eventos do Widget
- `onSuccess`: Quando a conexão é bem-sucedida
- `onError`: Quando ocorre um erro
- `onClose`: Quando o widget é fechado

## SDKs Disponíveis

### Node.js SDK
```javascript
import { PluggyClient } from 'pluggy-sdk';

const client = new PluggyClient({
  clientId: CLIENT_ID,
  clientSecret: CLIENT_SECRET,
});

const data = await client.fetchAccounts(itemId);
```

### React SDK
```javascript
import { PluggyConnect } from 'react-pluggy-connect';
```

## Iniciação de Pagamentos

### Payment Initiation
A Pluggy oferece funcionalidades de iniciação de pagamentos via Pix através do Open Finance.

### Smart Transfers
A API Smart Transfers da Pluggy torna os pagamentos instantâneos, fáceis e seguros. O usuário só precisa dar o consentimento uma vez (Preauthorização Smart Transfer) por conta devedora.

## API de Insights

Baseado nas contas conectadas, você pode recuperar insights do usuário, livro de variáveis, análise de renda e padrões recorrentes.

### Endpoint de Insights
```
POST https://insights-api.pluggy.ai/book?itemIds={your-item-id}
```

### KPIs Financeiros Disponíveis
- Fluxo de caixa
- Distribuição de transações de débito/crédito
- Análise de renda
- Padrões recorrentes

## API de Enriquecimento

A API Enrich fornece a capacidade de categorizar seus próprios dados de transações recuperados fora da Pluggy, fornecendo categorização, extração de comerciante e outros indicadores-chave sobre a transação.

## Tratamento de Erros

### Status de Execução

#### SUCCESS
Significa que todos os produtos (contas, transações, etc.) foram recuperados corretamente da instituição e estão prontos para serem recuperados.

#### PARTIAL_SUCCESS
O produto foi recuperado corretamente, mas pode ser melhorado com alguma ação do usuário.

#### LOGIN_ERROR
Não foi possível fazer login, retorna um status LOGIN_ERROR. Nenhum produto foi recuperado e não podemos tentar novamente a conexão: exigimos que o usuário atualize suas credenciais.

### Estrutura de Erro
```javascript
type ExecutionErrorResult = {
  code: ExecutionErrorCodes
  message: string
  providerMessage?: string
  attributes?: Record<string, string>
}
```

## Conectores Especiais

### Caixa Econômica Federal
Este conector requer que o usuário autorize um novo dispositivo (Pluggy) dentro do seu aplicativo móvel Caixa. Tenha em mente que a partir do momento em que o usuário insere suas credenciais, pode levar até 30 minutos para completar o processo de login.

### Banco Safra
Para conectar uma conta, este conector requer que o usuário autorize um novo dispositivo (Pluggy - yyy-mm-dd hh-mm) através do aplicativo móvel Safra.

## Ambiente de Testes (Sandbox)

### Como Acessar o Sandbox
Usando nosso ambiente de produção, você pode acessar conectores Live e Sandbox. Por padrão, fornecemos conectores reais para instituições suportadas, para testes você pode recuperar conectores sandbox fornecendo sandbox=true na requisição.

### Pluggy Bank (Conector Sandbox)
Para fins de teste, você pode experimentar sua integração usando nosso conector Sandbox (que representa nosso ambiente Sandbox). Isso permitirá que você veja como as transações são atualizadas diariamente e teste todas as conexões válidas possíveis e fluxos errôneos.

### Fluxos de Teste Disponíveis
Você encontrará diferentes fluxos:
1. Fluxo básico (também incluímos fluxo especial Caixa)
2. Fluxo básico Business
3. MFA 1-step
4. MFA 2-step
5. Contas conjuntas (fluxo Bradesco Conta Conjunta)
6. Fluxo QR Login

### Credenciais de Teste
Você pode usar as seguintes credenciais quando necessário:

**Usuário:**
- `user-ok`: Nome de usuário correto
- `user-bad`: Nome de usuário incorreto
- `user-mfa`: Usuário que requer segunda etapa de autenticação

**Senha:**
- `password-ok`: Senha correta
- `password-bad`: Senha incorreta

**Token/SMS:** `123456` (Parâmetro MFA correto)

### Testes com Alto Volume de Transações
Em casos onde é necessário testar grandes quantidades de transações no resultado, você pode usar o nome de usuário user-ok-perf ou user-ok-perf-XXx para recriar esta situação. XX representa o multiplicador para o número de transações a serem recuperadas. Por exemplo, se você escolher 1000 como XX, o nome de usuário resultante seria user-ok-perf-1000x, para multiplicar o resultado por este número.

### Fluxo Especial Caixa (Sandbox)
Este é um caso especial que emula o fluxo Caixa Econômica Federal. Uma vez que esta etapa é concluída, há dois cenários possíveis:
1. Se o usuário atualizar o item dentro do tempo a ser aguardado, o resultado da execução será USER_AUTHORIZATION_NOT_GRANTED e uma mensagem para lembrar o tempo a ser aguardado até que a autorização seja concedida da Caixa (no caso Sandbox, o tempo é 2 minutos)
2. Se o usuário atualizar o item após a espera terminar, os dados da conta serão recuperados com sucesso e o relatório de execução será SUCCESS

### Fluxo Conta Conjunta (Bradesco)
Este é um caso especial que emula o fluxo Bradesco Conta Conjunta. Quando usa o widget, o usuário será apresentado para escolher primeiro entre uma "Conta única" ou uma "Conta conjunta".

**Testando "conta única":**
- A requisição é a mesma que sandbox MFA 1-step
- As credenciais bancárias e MFA são enviadas juntas

**Testando "conta conjunta":**
- Você deve incluir um parâmetro MFA 1-step, com o valor mock: '000000'
- Este é o mesmo fluxo do Connect widget

### Fluxo QR Login
Este é um caso que originalmente simula um fluxo similar ao Inter QR. Nenhuma credencial é necessária. Uma vez iniciado, o item entrará em status WAITING_USER_ACTION e retornará um código QR para o usuário escanear.

### Open Finance Sandbox
Para conectar usando nossa conexão sandbox, você será obrigado a enviar um CPF com o valor "76109277673" e ao acessar a Instituição Financeira de "Mock Bank" você pode usar os seguintes parâmetros:
- **CPF:** `76109277673`
- **Instituição:** Mock Bank

### Habilitando Sandbox no Widget
Para incluir o modo sandbox para testes, defina includeSandbox como true no objeto window.pluggy.

### Limitações do Ambiente de Desenvolvimento
O ambiente de Desenvolvimento (Development) tem um limite de criação de 100 itens.

### Diferenças entre Sandbox e Produção
- **Auto-sync:** O recurso de auto-sync está disponível apenas para aplicações de Produção. Pode ser configurado para executar a cada 24, 12 ou 8 horas baseado na sua assinatura
- **Conectores:** No sandbox, você acessa conectores de teste que simulam comportamentos reais
- **Dados:** Os dados são simulados mas seguem a mesma estrutura da produção

### Como Listar Conectores Sandbox
```bash
GET /connectors?sandbox=true
```

### Postman e Sandbox
Você pode acessar nossa Coleção Postman para testar todos os nossos endpoints. Você só precisa definir as variáveis de ambiente CLIENT_ID e CLIENT_SECRET na aba Environments do Postman.

## Segurança

Usamos uma combinação do Padrão de Criptografia Avançada (AES 256) e uma Camada de Segurança de Transporte (TLS) para manter os dados seguros, provendo uma infraestrutura em linha com os mais altos padrões do mercado.

### LGPD
Nossa solução é totalmente aderente às exigências da LGPD. Somos transparentes com o usuário e todos os dados transacionados são obtidos mediante seu consentimento.

## Categorização de Transações

### Categorias Automáticas
As transações são categorizadas automaticamente em tempo real usando machine learning.

### Categorias Personalizadas
É possível atualizar a categoria de uma transação específica via API.

### Feedback de Categorização
Este endpoint permite que os clientes atualizem a categoria de uma transação, forçando-a a sempre retornar a mesma categoria e ignorando a categorização fornecida pela Pluggy. O mais importante é que isso fornece feedback à Pluggy sobre uma transação que pode estar mal categorizada.

## Limitações e Considerações

### Rate Limits
A API possui limitações de taxa que variam por endpoint e tipo de autenticação.

### Timeouts
Sua API deve responder com 2XX em menos de 5 segundos para webhooks.

### Retenção de Dados
Os dados são mantidos conforme as políticas de retenção e podem variar por tipo de produto.

## Recursos Adicionais

### Postman Collection
A Pluggy fornece uma coleção do Postman para testar todos os endpoints.

### Repositório Quickstart
Disponível no GitHub para ajudar a começar com integrações.

### Suporte
Para questões técnicas e suporte, consulte a documentação oficial ou entre em contato com o suporte da Pluggy.

## Cobertura de Conectores

A Pluggy suporta uma ampla variedade de instituições financeiras brasileiras, incluindo:

- Bancos tradicionais (Bradesco, Itaú, Caixa, Banco do Brasil, etc.)
- Bancos digitais (Nubank, Inter, C6 Bank, etc.)
- Fintechs (MercadoPago, PicPay, etc.)
- Corretoras de investimentos
- Cartões de crédito

Para uma lista completa e atualizada, consulte o endpoint `/connectors` ou a documentação de cobertura de conectores.

---

*Esta documentação foi compilada a partir das fontes oficiais da Pluggy API. Para informações mais recentes e detalhadas, consulte sempre a documentação oficial em docs.pluggy.ai.*