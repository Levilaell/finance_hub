# Como Processar Erros de Validação do Backend

## O Problema
O backend está retornando corretamente as mensagens de erro, mas o frontend mostra apenas "Falha no Cadastro".

## Resposta do Backend (Status 400)
```json
{
  "error": {
    "message": "Erro de validação nos dados fornecidos.",
    "field_errors": {
      "email": ["Este e-mail já está cadastrado."]
    }
  }
}
```

## Como o Frontend Deve Processar

### 1. Interceptar a Resposta 400
```javascript
// Se usando axios
axios.post('/api/auth/register/', data)
  .catch(error => {
    if (error.response && error.response.status === 400) {
      const errorData = error.response.data;
      
      // Verificar se tem field_errors
      if (errorData.error && errorData.error.field_errors) {
        // Processar erros por campo
        const fieldErrors = errorData.error.field_errors;
        
        // Exemplo: mostrar erro do email
        if (fieldErrors.email) {
          // Mostrar: "Este e-mail já está cadastrado."
          setEmailError(fieldErrors.email[0]);
        }
      }
    }
  });
```

### 2. Se Usando Fetch API
```javascript
fetch('/api/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
.then(response => {
  // IMPORTANTE: Ler o JSON mesmo se status não for ok
  return response.json().then(data => ({
    status: response.status,
    data: data
  }));
})
.then(result => {
  if (result.status !== 201) {
    // Erro!
    if (result.data.error && result.data.error.field_errors) {
      // Mostrar erros específicos
      const errors = result.data.error.field_errors;
      
      // Para cada campo com erro
      Object.keys(errors).forEach(field => {
        console.log(`Erro no campo ${field}: ${errors[field][0]}`);
        // Atualizar UI com o erro
      });
    }
  }
});
```

### 3. Estrutura Completa dos Erros Possíveis

```javascript
// Email já existe
{
  "error": {
    "field_errors": {
      "email": ["Este e-mail já está cadastrado."]
    }
  }
}

// Senha fraca
{
  "error": {
    "field_errors": {
      "password": [
        "A senha deve ter pelo menos 8 caracteres.",
        "A senha deve conter pelo menos uma letra maiúscula.",
        "A senha deve conter pelo menos um número."
      ]
    }
  }
}

// CNPJ inválido
{
  "error": {
    "field_errors": {
      "company_cnpj": ["CNPJ inválido. Verifique se digitou corretamente."]
    }
  }
}

// Múltiplos erros
{
  "error": {
    "field_errors": {
      "email": ["Este e-mail já está cadastrado."],
      "password": ["As senhas não coincidem."],
      "phone": ["Telefone deve ter 10 ou 11 números incluindo DDD."]
    }
  }
}
```

## Checklist para o Frontend

1. ✅ Verificar se está lendo `response.data.error.field_errors`
2. ✅ Não assumir que erro 400 é genérico - ler o conteúdo
3. ✅ Mostrar erro específico de cada campo
4. ✅ Primeiro erro do array geralmente é suficiente: `errors[field][0]`

## Exemplo de Debug

```javascript
// Adicione este código temporariamente para debug
.catch(error => {
  console.log('Erro completo:', error);
  console.log('Response:', error.response);
  console.log('Data:', error.response?.data);
  console.log('Field Errors:', error.response?.data?.error?.field_errors);
  
  // Ver exatamente o que está chegando
  alert(JSON.stringify(error.response?.data, null, 2));
});
```