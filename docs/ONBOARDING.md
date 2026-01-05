# Onboarding Tour

Tour interativo para novos usuários do CaixaHub usando [Driver.js](https://driverjs.com/).

## Fluxo

```
Checkout Success (trial) → seta flag → /dashboard → Tour (3 passos) → /accounts
```

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `config.ts` | Steps, textos e configuração do Driver.js |
| `useOnboarding.ts` | Hook React com lógica do tour |
| `styles.css` | Estilos customizados (mobile-first) |

## Uso

```tsx
import { useOnboarding } from '@/lib/onboarding/useOnboarding';

function MyComponent() {
  const { shouldShowTour, startTour, resetTour } = useOnboarding();

  // Iniciar tour
  if (shouldShowTour()) {
    startTour();
  }

  // Resetar para mostrar novamente
  resetTour();
}
```

## localStorage Keys

| Chave | Descrição |
|-------|-----------|
| `caixahub_show_tour` | Flag para iniciar tour (setada no checkout) |
| `caixahub_tour_done` | Marca tour como concluído |

## Comportamento

- **Novo usuário (trial):** Vê o tour automaticamente
- **Reativação (active):** NÃO vê o tour
- **Fechar no meio:** Tour aparece novamente no próximo acesso
- **Completar tour:** Não aparece mais (até resetar)
- **Refazer tour:** Botão em `/how-to-use`

## Customização

### Editar passos
Modifique `TOUR_STEPS` em `config.ts`.

### Editar estilos
Modifique `styles.css` (usa `!important` para sobrescrever Driver.js).

### Adicionar novo elemento ao tour
1. Adicione `data-tour="nome"` no elemento HTML
2. Adicione step em `config.ts` com `element: '[data-tour="nome"]'`
