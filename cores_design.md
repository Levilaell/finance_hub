# Guia de Cores - CaixaHub

## Paleta de Cores Principal

### Tema Dark (Padrão)

#### Cores Base
- **Background**: `hsl(0, 0%, 4%)` - Preto profundo (#0a0a0a)
- **Foreground (Texto)**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Componentes
- **Card Background**: `hsl(260, 30%, 8%)` - Roxo escuro com transparência (#14101a)
- **Card Text**: `hsl(0, 0%, 100%)` - Branco puro
- **Popover Background**: `hsl(260, 30%, 12%)` - Roxo escuro médio (#1a1424)
- **Popover Text**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Ação
- **Primary (Botões principais)**: `hsl(0, 0%, 100%)` - Branco puro
- **Primary Text**: `hsl(0, 0%, 0%)` - Preto puro
- **Secondary (Botões secundários)**: `hsl(0, 0%, 15%)` - Cinza escuro (#262626)
- **Secondary Text**: `hsl(0, 0%, 100%)` - Branco puro
- **Accent (Destaques)**: `hsl(270, 100%, 70%)` - Roxo vibrante para detalhes (#b146ff)
- **Accent Text**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Estado
- **Muted (Desabilitado)**: `hsl(260, 10%, 25%)` - Roxo acinzentado (#393646)
- **Muted Text**: `hsl(260, 5%, 60%)` - Cinza médio
- **Destructive (Erro/Perigo)**: `hsl(346, 87%, 55%)` - Vermelho vibrante
- **Destructive Text**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Interface
- **Border**: `hsl(260, 30%, 18%)` - Roxo escuro para bordas (#2b2439)
- **Input Background**: `hsl(260, 30%, 10%)` - Roxo muito escuro (#16121e)
- **Ring (Foco)**: `hsl(270, 100%, 70%)` - Roxo vibrante para indicador de foco

### Tema Light

#### Cores Base
- **Background**: `hsl(0, 0%, 98%)` - Branco suave (#fafafa)
- **Foreground (Texto)**: `hsl(260, 50%, 10%)` - Roxo muito escuro (#0f0819)

#### Cores de Componentes
- **Card Background**: `hsl(0, 0%, 100%)` - Branco puro
- **Card Text**: `hsl(260, 50%, 10%)` - Roxo muito escuro
- **Popover Background**: `hsl(0, 0%, 100%)` - Branco puro
- **Popover Text**: `hsl(260, 50%, 10%)` - Roxo muito escuro

#### Cores de Ação
- **Primary (Botões principais)**: `hsl(270, 90%, 55%)` - Roxo vibrante (#8b2eff)
- **Primary Text**: `hsl(0, 0%, 100%)` - Branco puro
- **Secondary (Botões secundários)**: `hsl(270, 40%, 96%)` - Roxo muito claro (#f7f4fc)
- **Secondary Text**: `hsl(270, 70%, 30%)` - Roxo escuro
- **Accent (Destaques)**: `hsl(330, 90%, 55%)` - Rosa/Magenta vibrante (#ff2e85)
- **Accent Text**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Estado
- **Muted (Desabilitado)**: `hsl(270, 20%, 94%)` - Roxo muito claro
- **Muted Text**: `hsl(260, 15%, 45%)` - Roxo acinzentado
- **Destructive (Erro/Perigo)**: `hsl(346, 80%, 50%)` - Vermelho vibrante
- **Destructive Text**: `hsl(0, 0%, 100%)` - Branco puro

#### Cores de Interface
- **Border**: `hsl(270, 30%, 88%)` - Roxo claro para bordas
- **Input Background**: `hsl(270, 30%, 95%)` - Roxo muito claro
- **Ring (Foco)**: `hsl(270, 90%, 55%)` - Roxo vibrante para indicador de foco

## Efeitos Especiais

### Gradientes (Uso Mínimo)
- **Gradiente Sutil**: Para elementos decorativos apenas
  - Dark: Branco com transparência `rgba(255, 255, 255, 0.1)` → `rgba(255, 255, 255, 0.05)`
  - Light: Manter cores vibrantes para contraste

### Efeitos de Brilho (Glow)
- **White Glow**: Sombra branca sutil com 10-20% de opacidade
- **Card Glow**: Borda branca com 10% de opacidade no hover
- **Button Glow**: Sombra branca sutil ao hover para elevação

### Animações
- **Shimmer**: Efeito de brilho deslizante (2s loop infinito)
- **Gradient Shift**: Animação de gradiente (6s loop infinito)
- **Spinner**: Rotação 360° com borda Primary (1s loop infinito)

## Uso Recomendado

### Hierarquia Visual
1. **Primary**: CTAs principais, botões de ação importantes
2. **Secondary**: Ações secundárias, navegação
3. **Accent**: Destaques, notificações, elementos decorativos
4. **Muted**: Estados desabilitados, textos secundários
5. **Destructive**: Alertas, erros, ações perigosas

### Acessibilidade
- Todas as combinações de cores foram escolhidas para garantir contraste adequado
- Modo escuro como padrão para reduzir fadiga visual
- Suporte completo para preferência do sistema (light/dark)

### Notas para Implementação
- Usar variáveis CSS (custom properties) para fácil manutenção
- Border radius padrão: `0.5rem`
- Transições suaves entre temas
- Sombras adaptativas para modo escuro