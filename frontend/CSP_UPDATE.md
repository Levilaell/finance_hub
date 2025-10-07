# Content Security Policy - Atualização para Meta Pixel

## 🔧 Problema Identificado

O Meta Pixel estava sendo **bloqueado pelo CSP** do site:

```
Refused to load the script 'https://connect.facebook.net/en_US/fbevents.js'
because it violates the following Content Security Policy directive: "script-src..."

Refused to load the image 'https://www.facebook.com/tr?id=...'
because it violates the following Content Security Policy directive: "img-src..."
```

## ✅ Solução Aplicada

Adicionei os domínios do Facebook/Meta ao **Content Security Policy** em `next.config.js`:

### Domínios Adicionados:

1. **`script-src`**: `https://connect.facebook.net`
   - Permite carregar o script `fbevents.js`

2. **`img-src`**: `https://www.facebook.com`
   - Permite o pixel tracking via imagem (fallback no `<noscript>`)

3. **`connect-src`**: `https://www.facebook.com` + `https://*.facebook.com`
   - Permite requisições AJAX/Fetch para enviar eventos
   - Cobre todos os subdomínios do Facebook

## 📝 Mudanças no Arquivo

**Arquivo:** `next.config.js`

```javascript
// ANTES
"script-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com"
"img-src 'self' data: blob: https://*.pluggy.ai https://*.pluggycdn.com https://lh3.googleusercontent.com"
"connect-src 'self' ... https://api.stripe.com"

// DEPOIS
"script-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com https://connect.facebook.net"
"img-src 'self' data: blob: https://*.pluggy.ai https://*.pluggycdn.com https://lh3.googleusercontent.com https://www.facebook.com"
"connect-src 'self' ... https://api.stripe.com https://www.facebook.com https://*.facebook.com"
```

## 🚀 Próximos Passos

1. **Commit e deploy** as mudanças
2. **Aguarde o deploy** completar
3. **Teste novamente** com:
   - Meta Pixel Helper
   - DevTools Network tab
   - Meta Events Manager

## ✅ Checklist Pós-Deploy

- [ ] Acesse o site em produção
- [ ] Abra DevTools → Network
- [ ] Filtre por `tr?` ou `facebook`
- [ ] Recarregue a página
- [ ] ✅ Deve ver requisições para `facebook.com/tr` sem erros de CSP
- [ ] Verifique o Meta Pixel Helper - não deve mais ter warning de CSP
- [ ] Teste no Meta Events Manager

## 🔒 Segurança

Os domínios adicionados são **oficiais da Meta** e seguros:

- `connect.facebook.net` - CDN oficial para scripts do Meta Pixel
- `www.facebook.com` - Endpoint oficial para tracking

Estes são os domínios padrão recomendados pela própria documentação do Meta Pixel.

## 📚 Referências

- [Meta Pixel Documentation](https://developers.facebook.com/docs/meta-pixel/)
- [CSP and Third-Party Scripts](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
