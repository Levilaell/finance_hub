# Upload de Boletos com OCR

Feature que permite upload de boletos (PDF ou imagem) com extração automática de dados via Google Cloud Vision API.

## Funcionalidades

- Upload de arquivos PDF, PNG, JPG (máx. 5MB)
- Extração automática via OCR:
  - Linha digitável (código de barras)
  - Valor
  - Data de vencimento
  - Beneficiário/Cedente
- Indicador de confiança da extração
- Formulário editável para revisão antes de criar a conta
- Integração com o sistema de Bills existente

---

## Configuração

### 1. Google Cloud Platform

```bash
# Criar conta em https://console.cloud.google.com
# Criar projeto (ex: "caixahub-ocr")

# Habilitar Vision API
gcloud services enable vision.googleapis.com

# Criar Service Account
# IAM & Admin → Service Accounts → Create
# Nome: "caixahub-vision"
# Role: "Cloud Vision API User"
# Criar chave JSON → Download
```

### 2. Variáveis de Ambiente (Railway)

```env
# Copie o conteúdo completo do JSON da service account
GCP_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}
```

### 3. Deploy

```bash
# Rodar migração
python manage.py migrate

# Push para deploy
git push
```

---

## Como Usar

### Frontend

1. Acesse a página **Contas** (`/bills/`)
2. Clique no botão **"Upload Boleto"**
3. Arraste ou selecione um arquivo (PDF, PNG, JPG)
4. Aguarde o processamento (2-5 segundos)
5. Revise os dados extraídos
6. Clique **"Criar Conta"**

### API

#### Upload e OCR

```bash
POST /api/banking/bills/upload_boleto/
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <arquivo>
```

**Resposta:**

```json
{
  "success": true,
  "barcode": "23793381286000000000300000004001843400000100000",
  "amount": "100.00",
  "due_date": "2025-01-15",
  "beneficiary": "Empresa XYZ",
  "confidence": 85.0,
  "needs_review": false,
  "extracted_fields": {
    "barcode_found": true,
    "amount_found": true,
    "date_found": true,
    "beneficiary_found": true
  }
}
```

#### Criar Bill após Revisão

```bash
POST /api/banking/bills/create_from_ocr/
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "payable",
  "description": "Boleto Empresa XYZ",
  "amount": 100.00,
  "due_date": "2025-01-15",
  "customer_supplier": "Empresa XYZ",
  "barcode": "23793381286000000000300000004001843400000100000",
  "ocr_confidence": 85.0
}
```

---

## Dados Extraídos

| Campo | Método de Extração | Confiabilidade |
|-------|-------------------|----------------|
| Linha digitável | Regex 47-48 dígitos | Alta |
| Valor | Regex `R$` ou extraído do barcode | Alta |
| Vencimento | Regex `DD/MM/YYYY` ou extraído do barcode | Alta |
| Beneficiário | Texto após "Cedente" ou "Beneficiário" | Média |

### Cálculo de Confiança

- Barcode encontrado: +40 pontos
- Valor encontrado (texto): +25 pontos / (barcode): +20 pontos
- Data encontrada (texto): +20 pontos / (barcode): +15 pontos
- Beneficiário encontrado: +15 pontos

**Total máximo:** 100 pontos

---

## Arquivos Modificados

### Backend

| Arquivo | Descrição |
|---------|-----------|
| `apps/banking/models.py` | Campos OCR no model Bill |
| `apps/banking/ocr_service.py` | BillOCRService (Google Vision) |
| `apps/banking/serializers.py` | Serializers de upload |
| `apps/banking/views.py` | Endpoints upload_boleto e create_from_ocr |
| `apps/banking/migrations/0012_*.py` | Migração dos campos |
| `requirements.txt` | google-cloud-vision, pdf2image |
| `nixpacks.toml` | poppler-utils para PDF |

### Frontend

| Arquivo | Descrição |
|---------|-----------|
| `components/banking/BillUploadDialog.tsx` | Dialog de upload |
| `services/bills.service.ts` | Métodos uploadBoleto, createFromOCR |
| `lib/api-client.ts` | Método postFormData |
| `app/(dashboard)/bills/page.tsx` | Botão e integração |

---

## Custos

| Item | Custo |
|------|-------|
| Google Cloud Vision | ~$1.50 / 1.000 imagens |
| Por boleto | ~R$0.01 |
| 1.000 boletos/mês | ~R$10 |

**Nota:** GCP oferece $300 de crédito gratuito por 90 dias para novas contas.

---

## Troubleshooting

### OCR não funciona

1. Verificar se `GCP_CREDENTIALS_JSON` está configurado no Railway
2. Verificar se Vision API está habilitada no GCP
3. Verificar logs: `railway logs`

### PDF não processa

1. Verificar se `poppler-utils` foi instalado (nixpacks.toml)
2. Verificar se `pdf2image` está no requirements.txt

### Confiança baixa

- Imagem com baixa resolução
- Boleto com layout não-padrão
- Texto borrado ou cortado

**Solução:** Usuário pode editar os campos manualmente antes de criar a conta.
