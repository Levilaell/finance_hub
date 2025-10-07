# Meta Pixel - Guia de Debug

## ⚠️ Sobre o Warning do Pixel Helper

Se você vê a mensagem: **"Pixel Helper found your Meta Pixel, but the pixel has not been activated for this event"**, isso pode ser um **falso positivo**. O pixel pode estar funcionando corretamente mesmo com esse warning.

## 🔍 Como Verificar se o Pixel Está Funcionando

### Método 1: Chrome DevTools (Mais Confiável)

1. Abra o Chrome DevTools (`F12` ou `Cmd+Option+I` no Mac)
2. Vá para a aba **Network**
3. Filtre por: `facebook.com/tr` ou simplesmente `tr?`
4. Recarregue a página
5. **Você DEVE ver requisições para:**
   - `https://www.facebook.com/tr?id=24169428459391565&ev=PageView`

Se você vê essas requisições, **o pixel está funcionando!** ✅

### Método 2: Console Logs (Desenvolvimento)

Em ambiente de desenvolvimento, abra o Console no DevTools e procure por:
```
[Meta Pixel] Initializing pixel...
[Meta Pixel] Pixel initialized with ID: 24169428459391565
[Meta Pixel] PageView tracked for: /
```

### Método 3: Meta Events Manager (Oficial)

1. Acesse: https://business.facebook.com/events_manager
2. Selecione seu Pixel ID: `24169428459391565`
3. Clique em **"Test Events"**
4. Copie a URL do seu site e cole na ferramenta
5. Navegue pelo site
6. Você verá os eventos em tempo real se estiver funcionando ✅

## 🚫 Causas Comuns do Warning (Mesmo Funcionando)

### 1. **Bloqueadores de Anúncios**
- **uBlock Origin**, **AdBlock**, **Brave Shield**, etc.
- **Solução**: Desative temporariamente para testar

### 2. **Privacy Extensions**
- **Privacy Badger**, **Ghostery**, etc.
- **Solução**: Desative temporariamente para testar

### 3. **Navegador em Modo Privado**
- Alguns navegadores bloqueiam trackers por padrão
- **Solução**: Teste em janela normal

### 4. **Gestão de Consentimento (LGPD/GDPR)**
- Se você tem um banner de cookies, o pixel pode estar aguardando consentimento
- **Solução**: Aceite os cookies e recarregue

### 5. **Service Workers**
- Podem interferir com requisições de rede
- **Solução**: Desative temporariamente no DevTools

### 6. **Bug do Pixel Helper**
- A extensão tem bugs conhecidos
- **Solução**: Confie no DevTools Network tab ao invés do Helper

## ✅ Checklist de Verificação

- [ ] Verifique requisições em `Network > facebook.com/tr`
- [ ] Veja os logs no Console (desenvolvimento)
- [ ] Teste no Meta Events Manager (oficial)
- [ ] Desative bloqueadores de anúncios
- [ ] Teste em navegador sem extensões
- [ ] Verifique se aceitou cookies (se houver banner)

## 🔧 Solução de Problemas

### Pixel não carrega de jeito nenhum:

1. Verifique se o componente `<PixelTracker />` está no `layout.tsx`
2. Certifique-se que está em uma página `'use client'`
3. Verifique se não há erros no Console do navegador

### Pixel carrega mas não dispara PageView:

1. Verifique os logs do console em desenvolvimento
2. Confirme que `window.fbq` existe no console
3. Teste manualmente: `window.fbq('track', 'PageView')` no console

### Eventos customizados não funcionam:

```typescript
import { trackLead } from '@/lib/meta-pixel';

// Teste no console primeiro
window.fbq('track', 'Lead', { value: 10, currency: 'BRL' });

// Se funcionar, use a função helper
trackLead({ value: 10, currency: 'BRL' });
```

## 📞 Suporte

Se mesmo após todas essas verificações o pixel não estiver enviando dados:

1. Verifique no Meta Business Manager se o Pixel está ativo
2. Confirme que o Pixel ID está correto: `24169428459391565`
3. Verifique se o domínio está verificado no Meta Business Manager
4. Entre em contato com o suporte do Meta
