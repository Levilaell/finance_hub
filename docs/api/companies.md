# API de Companies

Base URL: `/api/companies/`

## Endpoints

### GET /detail/

Obter detalhes da empresa do usuario.

**Autenticacao**: Bearer Token

**Response 200**:
```json
{
  "id": "uuid",
  "name": "Minha Empresa LTDA",
  "cnpj": "12345678000199",
  "company_type": "mei",
  "business_sector": "services",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-12-18T10:00:00Z"
}
```

**Response 404 (sem empresa)**:
```json
{
  "detail": "Company not found"
}
```

---

## Campos

### company_type

| Valor | Descricao |
|-------|-----------|
| mei | Microempreendedor Individual |
| me | Microempresa |
| epp | Empresa de Pequeno Porte |
| ltda | Sociedade Limitada |
| sa | Sociedade Anonima |
| other | Outro |

### business_sector

| Valor | Descricao |
|-------|-----------|
| retail | Comercio/Varejo |
| services | Servicos |
| industry | Industria |
| technology | Tecnologia |
| healthcare | Saude |
| education | Educacao |
| food | Alimentacao |
| construction | Construcao |
| automotive | Automotivo |
| agriculture | Agricultura |
| other | Outro |

---

## Validacoes

### CNPJ

- Deve ter exatamente 14 digitos
- Apenas numeros (sem pontuacao)
- Unico por empresa ativa

```python
def validate_cnpj(value):
    digits = re.sub(r'\D', '', value)
    if len(digits) != 14:
        raise ValidationError('CNPJ deve ter 14 digitos')
```

---

## Relacionamento

A empresa e criada automaticamente quando o usuario habilita AI Insights:

```python
# backend/apps/ai_insights/views.py
@action(methods=['post'], detail=False)
def enable(self, request):
    company, created = Company.objects.get_or_create(
        owner=request.user,
        defaults={
            'company_type': request.data.get('company_type'),
            'business_sector': request.data.get('business_sector')
        }
    )
    # ...
```

---

## Notas

- Cada usuario possui no maximo 1 empresa (OneToOne)
- Empresa e criada via AI Insights, nao diretamente
- CNPJ e opcional na criacao inicial
- Dados sao usados para personalizar analises de IA
