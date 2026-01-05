# API de Autenticacao

Base URL: `/api/auth/`

## Endpoints

### POST /register/

Registrar novo usuario.

**Autenticacao**: Nao requerida

**Request Body**:
```json
{
  "email": "usuario@email.com",
  "password": "SenhaForte123!",
  "first_name": "Joao",
  "phone": "11999999999",
  "signup_price_id": "price_xxxxx",
  "acquisition_angle": "time"
}
```

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| email | string | Sim | Email unico |
| password | string | Sim | Min 8 chars, requisitos de forca |
| first_name | string | Sim | Nome do usuario |
| phone | string | Nao | Telefone (WhatsApp) |
| signup_price_id | string | Nao | Price ID do Stripe (A/B test) |
| acquisition_angle | string | Nao | Canal de aquisicao |

**Response 201**:
```json
{
  "user": {
    "id": "uuid",
    "email": "usuario@email.com",
    "first_name": "Joao",
    "phone": "11999999999"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

**Erros**:
| Codigo | Descricao |
|--------|-----------|
| 400 | Email ja cadastrado |
| 400 | Senha muito fraca |

---

### POST /login/

Autenticar usuario existente.

**Autenticacao**: Nao requerida

**Request Body**:
```json
{
  "email": "usuario@email.com",
  "password": "SenhaForte123!"
}
```

**Response 200**:
```json
{
  "user": {
    "id": "uuid",
    "email": "usuario@email.com",
    "first_name": "Joao"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

**Erros**:
| Codigo | Descricao |
|--------|-----------|
| 401 | Credenciais invalidas |

---

### GET /profile/

Obter perfil do usuario autenticado.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "id": "uuid",
  "email": "usuario@email.com",
  "first_name": "Joao",
  "last_name": "Silva",
  "phone": "11999999999",
  "timezone": "America/Sao_Paulo",
  "created_at": "2025-01-01T00:00:00Z",
  "has_active_subscription": true
}
```

---

### POST /refresh/

Renovar access token.

**Autenticacao**: Nao requerida (usa refresh token)

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

**Response 200**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

**Erros**:
| Codigo | Descricao |
|--------|-----------|
| 401 | Refresh token invalido ou expirado |

---

### GET /settings/

Obter configuracoes do usuario.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "auto_match_transactions": true
}
```

---

### PATCH /settings/

Atualizar configuracoes do usuario.

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "auto_match_transactions": false
}
```

**Response 200**:
```json
{
  "auto_match_transactions": false
}
```

---

### POST /track-page-view/

Rastrear visualizacao de pagina (analytics).

**Autenticacao**: Bearer Token

**Request Body**:
```json
{
  "page": "/dashboard",
  "referrer": "/login"
}
```

**Response 200**:
```json
{
  "success": true
}
```

---

## Headers

### Autenticacao

```
Authorization: Bearer <access_token>
```

### Content-Type

```
Content-Type: application/json
```

---

## Codigos de Resposta

| Codigo | Significado |
|--------|-------------|
| 200 | Sucesso |
| 201 | Criado com sucesso |
| 400 | Dados invalidos |
| 401 | Nao autenticado |
| 403 | Sem permissao |
| 500 | Erro interno |
