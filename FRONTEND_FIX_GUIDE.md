# 🚨 GUIA PARA CORRIGIR O FRONTEND

## O Backend está retornando corretamente!

### Estrutura da Resposta (Status 400):
```json
{
  "error": {
    "code": "validation_error",
    "message": "Erro de validação nos dados fornecidos.",
    "timestamp": "2025-07-21T03:33:45.787216+00:00",
    "field_errors": {
      "email": ["Este e-mail já está cadastrado."],
      "password": ["A senha deve ter pelo menos 8 caracteres."]
    }
  }
}
```

## Como o Frontend Deve Processar

### 1. Se usando Axios:
```javascript
try {
  const response = await axios.post('/api/auth/register/', formData);
  // sucesso
} catch (error) {
  if (error.response?.status === 400) {
    const errorData = error.response.data;
    
    // IMPORTANTE: A estrutura é error.field_errors
    if (errorData.error?.field_errors) {
      const fieldErrors = errorData.error.field_errors;
      
      // Processar cada campo
      Object.keys(fieldErrors).forEach(field => {
        const errorMessage = fieldErrors[field][0]; // Primeira mensagem
        
        // Mostrar erro no campo específico
        if (field === 'email') {
          setEmailError(errorMessage); // "Este e-mail já está cadastrado."
        }
        if (field === 'password') {
          setPasswordError(errorMessage);
        }
        // ... outros campos
      });
    } else {
      // Erro genérico
      setGeneralError(errorData.error?.message || 'Falha no cadastro');
    }
  }
}
```

### 2. Se usando Fetch:
```javascript
const response = await fetch('/api/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData)
});

const data = await response.json();

if (!response.ok) {
  // IMPORTANTE: Acessar data.error.field_errors
  if (data.error?.field_errors) {
    const errors = data.error.field_errors;
    
    // Exemplo para React
    setErrors({
      email: errors.email?.[0] || '',
      password: errors.password?.[0] || '',
      company_cnpj: errors.company_cnpj?.[0] || '',
      // ... outros campos
    });
  }
}
```

### 3. Exemplo Completo React:
```jsx
const [fieldErrors, setFieldErrors] = useState({});

const handleSubmit = async (e) => {
  e.preventDefault();
  setFieldErrors({}); // Limpar erros anteriores
  
  try {
    const response = await fetch(API_URL + '/api/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      // ⚠️ ATENÇÃO: O caminho é data.error.field_errors
      if (data.error?.field_errors) {
        setFieldErrors(data.error.field_errors);
      } else {
        alert(data.error?.message || 'Erro ao cadastrar');
      }
      return;
    }
    
    // Sucesso
    console.log('Cadastro realizado!', data);
  } catch (err) {
    alert('Erro de conexão');
  }
};

// No JSX:
<input 
  type="email" 
  name="email"
  className={fieldErrors.email ? 'error' : ''}
/>
{fieldErrors.email && (
  <span className="error-text">{fieldErrors.email[0]}</span>
)}
```

## Teste Rápido no Console do Browser

Cole isso no console do navegador para testar:

```javascript
fetch('https://finance-backend-production-29df.up.railway.app/api/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: "arabel.bebel@hotmail.com",
    password: "Test123!",
    password2: "Test123!",
    first_name: "Test",
    last_name: "Test",
    phone: "(17) 99200-5945",
    company_name: "Test",
    company_cnpj: "05.206.246/0001-38",
    company_type: "ltda",
    business_sector: "tech"
  })
})
.then(r => r.json())
.then(data => {
  console.log('Resposta:', data);
  if (data.error?.field_errors?.email) {
    console.log('Erro no email:', data.error.field_errors.email[0]);
  }
});
```

## ⚠️ IMPORTANTE

1. O caminho correto é: `response.data.error.field_errors`
2. Cada campo é um array: use `field_errors.email[0]`
3. Status 400 = Erro de validação
4. O backend está funcionando perfeitamente!