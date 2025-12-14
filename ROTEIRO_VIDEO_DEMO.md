# Roteiro de Video de Demonstracao - CaixaHub

## Informacoes do Projeto

| Item | Detalhe |
|------|---------|
| **Produto** | CaixaHub - Plataforma de gestao financeira para PMEs |
| **Preco** | R$197/mes (substitui BPO de R$1.500/mes) |
| **Publico** | Donos de pequenas empresas, MEIs, freelancers |
| **Duracao Total** | 90 segundos |
| **Formato** | Gravacao de tela com narracao |
| **Objetivo** | Conversao para trial de 7 dias |

---

## Analise do Produto

### Principais Telas e Fluxos

| Rota | Funcionalidade |
|------|----------------|
| `/accounts` | Conexao bancaria via Open Banking (100+ bancos) |
| `/transactions` | Transacoes com categorizacao automatica + vinculacao com contas |
| `/bills` | Contas a pagar/receber + upload boleto com OCR |
| `/dashboard` | Visao geral: saldos, receitas, despesas, resultado |
| `/reports` | Relatorios com graficos + exportacao PDF/Excel |
| `/categories` | Categorias hierarquicas personalizaveis |
| `/ai-insights` | Score de saude financeira + recomendacoes IA |

### Funcionalidades-Chave para o Video

1. **Conexao Bancaria** - Open Banking com 100+ bancos brasileiros
2. **Categorizacao Inteligente** - Automatica + em massa (aplica a similares)
3. **Contas a Pagar/Receber** - Gestao completa + OCR de boletos
4. **Vinculacao Automatica** - Transacao do banco vincula com conta cadastrada
5. **Relatorios** - Graficos + exportacao PDF/Excel

### AHA Moment

O momento de "uau" acontece quando o usuario ve **centenas de transacoes ja categorizadas automaticamente**, consegue **categorizar em massa** transacoes similares com 1 clique, e ve a **vinculacao automatica** entre o pagamento no banco e a conta a pagar.

E o contraste entre "isso levaria dias no BPO" vs "levou 2 minutos".

---

## Roteiro Cena a Cena (90s)

| Cena | Tela/Rota | Acao na tela | Narracao (texto literal para gravar) | Duracao |
|------|-----------|--------------|--------------------------------------|---------|
| 1 - Hook | Tela preta com texto | Texto aparece: "Quanto voce paga pra alguem organizar suas financas?" | "Quanto voce paga pra alguem organizar suas financas? R$1.000? R$1.500 por mes?" | 5s |
| 2 - Entrada | `/accounts` (vazia) | Mouse clica em "Conectar Banco" | "Com o CaixaHub, voce conecta seu banco em segundos." | 4s |
| 3 - Conexao | Widget Pluggy | Seleciona banco (ex: Nubank), animacao de conexao | "Escolhe seu banco... autoriza via Open Banking... pronto." | 5s |
| 4 - Sync | `/accounts` com conta | Conta aparece com saldo, indicador de sync | "Suas transacoes sao puxadas automaticamente." | 3s |
| 5 - Transacoes | `/transactions` | Scroll suave pela lista, destaque nas categorias coloridas | "Olha so: todas as transacoes ja vem categorizadas. Fornecedores, aluguel, impostos..." | 6s |
| 6 - Categ. Massa | `/transactions` | Clica em transacao > abre modal com "Transacoes Similares" > seleciona todas | "E se quiser mudar? Um clique. O sistema encontra transacoes parecidas e aplica pra todas de uma vez." | 8s |
| 7 - Regra | Modal CategoryConfirm | Checkbox "Criar regra" marcado, clica "Aplicar" | "E ainda cria uma regra. Proxima vez, ja vem certo automaticamente." | 5s |
| 8 - Bills | `/bills` | Visao geral com cards: Total, Pendentes, Atrasadas, A Pagar, A Receber | "Contas a pagar e receber? Tudo organizado. Voce ve o que ta pendente, atrasado, e quanto entra e sai." | 7s |
| 9 - Upload OCR | `/bills` | Clica "Upload Boleto" > arrasta PDF > dados aparecem preenchidos | "Recebeu um boleto? Faz upload e o sistema extrai os dados automaticamente. Valor, vencimento, beneficiario." | 7s |
| 10 - Vinculacao | `/transactions` | Clica no icone de link em transacao > modal mostra conta sugerida > vincula | "E quando o pagamento cai no banco, vincula automatico com a conta. Marcado como pago, sem fazer nada." | 7s |
| 11 - Dashboard | `/dashboard` | Scroll mostrando cards de saldo, receitas, despesas, resultado | "No dashboard voce ve tudo: quanto entrou, quanto saiu, e seu resultado do mes." | 5s |
| 12 - Relatorios | `/reports` | Clica na aba, graficos aparecem | "Precisa de relatorio? Fluxo de caixa, categorias, comparativo..." | 5s |
| 13 - Exportacao | `/reports` | Clica em "Exportar" > "PDF", arquivo baixando | "Exporta pra PDF ou Excel em um clique. Manda pro contador na hora." | 5s |
| 14 - Resultado | Tela com comparativo | Lado a lado: "BPO: R$1.500/mes" vs "CaixaHub: R$197/mes" | "Tudo isso por R$197 por mes. Dez vezes menos que um BPO tradicional." | 5s |
| 15 - Tempo | Tela com icone de relogio | Animacao: "5+ horas economizadas por semana" | "E voce economiza mais de 5 horas toda semana." | 4s |
| 16 - CTA | Landing page com botao | Zoom no botao "Comecar Trial Gratis" | "Teste gratis por 7 dias. Sem cartao. Cancela quando quiser." | 5s |
| 17 - Fechamento | Logo CaixaHub | Logo centralizado com tagline | "CaixaHub. Sua empresa organizada em minutos." | 4s |

---

## Estrutura Resumida

```
[0:00 - 0:05]  HOOK................. Problema do preco alto
[0:05 - 0:17]  CONEXAO.............. Conectar banco + sync
[0:17 - 0:36]  TRANSACOES........... Lista categorizada + categorizacao em massa + regras
[0:36 - 0:50]  CONTAS............... Bills + upload OCR + vinculacao automatica
[0:50 - 1:05]  VISAO GERAL.......... Dashboard + relatorios + exportacao
[1:05 - 1:19]  BENEFICIO............ Comparativo preco + tempo
[1:19 - 1:30]  CTA.................. Trial gratis + fechamento
```

---

## Funcionalidades Demonstradas

### 1. Conexao Bancaria (Cenas 2-4)
- Widget Pluggy com 100+ bancos
- Sincronizacao automatica de transacoes
- Saldos em tempo real

### 2. Categorizacao Inteligente (Cenas 5-7)
- Transacoes ja vem categorizadas automaticamente
- **Categorizacao em massa**: ao mudar categoria, sistema encontra similares
- **Criacao de regras**: proximas transacoes ja vem categorizadas

### 3. Contas a Pagar/Receber (Cenas 8-9)
- Dashboard com totais: pendentes, atrasadas, a pagar, a receber
- **Upload de boleto com OCR**: extrai valor, vencimento, beneficiario
- Suporte a recorrencia (mensal, semanal, anual)

### 4. Vinculacao Automatica (Cena 10)
- Transacao no banco vincula com conta a pagar/receber
- Sistema sugere contas compativeis (mesmo valor)
- Ao vincular, conta e marcada como paga automaticamente

### 5. Dashboard e Relatorios (Cenas 11-13)
- Visao geral: saldo, receitas, despesas, resultado
- Graficos: fluxo de caixa, categorias, comparativo
- Exportacao PDF/Excel em 1 clique

---

## Notas de Producao

### Configuracoes de Gravacao

- **Resolucao:** 1920x1080 (Full HD)
- **FPS:** 30 ou 60
- **Formato:** MP4 (H.264)
- **Software sugerido:** Loom, OBS, ou ScreenFlow

### Dicas de Gravacao

1. **Cursor sempre visivel** - Use um cursor maior ou com highlight
2. **Zoom suave** - Evite cortes bruscos, prefira transicoes suaves
3. **Velocidade nas transacoes** - Acelere levemente (1.2x) para mostrar volume
4. **Highlight visual** - Use circulo amarelo/verde para indicar onde olhar

### Trilha Sonora

- Musica instrumental leve e tecnologica
- Sem letra (nao compete com narracao)
- Estilo: produtividade/SaaS/tech
- Sugestoes: Epidemic Sound, Artlist (buscar "corporate tech" ou "saas demo")

### Elementos Graficos Adicionais

| Cena | Elemento |
|------|----------|
| 1 | Texto grande centralizado com animacao fade-in |
| 5 | Setas ou highlights nas categorias coloridas |
| 6 | Destaque no modal de transacoes similares |
| 9 | Animacao mostrando dados sendo preenchidos automaticamente |
| 10 | Badge "Vinculada" aparecendo na transacao |
| 14 | Grafico de barras comparativo (animado) |
| 15 | Icone de relogio com numero "5h+" crescendo |
| 16 | Botao pulsando levemente |
| 17 | Logo com tagline em fade |

---

## Checklist Pre-Gravacao

### Dados de Demonstracao
- [ ] Conta de demonstracao populada com dados realistas
- [ ] Pelo menos 100+ transacoes categorizadas
- [ ] Transacoes similares existentes (para demonstrar categorizacao em massa)
- [ ] Multiplas contas bancarias conectadas
- [ ] Contas a pagar/receber cadastradas (algumas pendentes, algumas atrasadas)
- [ ] Pelo menos 1 boleto PDF pronto para upload
- [ ] Transacao nao vinculada que tenha conta compativel

### Ambiente
- [ ] Navegador em modo incognito (sem extensoes)
- [ ] Notificacoes do sistema desativadas
- [ ] Microfone testado (qualidade de audio e crucial)
- [ ] Tela limpa, sem abas desnecessarias

---

## Texto Completo da Narracao

> Quanto voce paga pra alguem organizar suas financas? R$1.000? R$1.500 por mes?
>
> Com o CaixaHub, voce conecta seu banco em segundos. Escolhe seu banco... autoriza via Open Banking... pronto. Suas transacoes sao puxadas automaticamente.
>
> Olha so: todas as transacoes ja vem categorizadas. Fornecedores, aluguel, impostos...
>
> E se quiser mudar? Um clique. O sistema encontra transacoes parecidas e aplica pra todas de uma vez. E ainda cria uma regra. Proxima vez, ja vem certo automaticamente.
>
> Contas a pagar e receber? Tudo organizado. Voce ve o que ta pendente, atrasado, e quanto entra e sai.
>
> Recebeu um boleto? Faz upload e o sistema extrai os dados automaticamente. Valor, vencimento, beneficiario.
>
> E quando o pagamento cai no banco, vincula automatico com a conta. Marcado como pago, sem fazer nada.
>
> No dashboard voce ve tudo: quanto entrou, quanto saiu, e seu resultado do mes.
>
> Precisa de relatorio? Fluxo de caixa, categorias, comparativo... Exporta pra PDF ou Excel em um clique. Manda pro contador na hora.
>
> Tudo isso por R$197 por mes. Dez vezes menos que um BPO tradicional. E voce economiza mais de 5 horas toda semana.
>
> Teste gratis por 7 dias. Sem cartao. Cancela quando quiser.
>
> CaixaHub. Sua empresa organizada em minutos.

**Tempo total de narracao:** ~90 segundos

---

## Versao Resumida (60s)

Para uma versao mais curta, remova as cenas 6-7 (categorizacao em massa) e 9 (upload OCR):

| Cena | Narracao | Duracao |
|------|----------|---------|
| 1 | "Quanto voce paga pra organizar suas financas? Mil? Mil e quinhentos por mes?" | 5s |
| 2-4 | "Com o CaixaHub, conecta seu banco em segundos. Transacoes puxadas automaticamente." | 8s |
| 5 | "Tudo ja vem categorizado. Fornecedores, aluguel, impostos..." | 6s |
| 8 | "Contas a pagar e receber organizadas. Ve o que ta pendente, atrasado." | 6s |
| 10 | "Pagamento no banco? Vincula automatico com a conta. Marcado como pago." | 6s |
| 11-12 | "Dashboard com tudo. Relatorios prontos. Exporta em um clique." | 8s |
| 14-15 | "Tudo por R$197. Dez vezes menos que BPO. Economiza 5 horas por semana." | 7s |
| 16-17 | "Teste gratis 7 dias. Sem cartao. CaixaHub." | 6s |

**Total: ~52 segundos**
