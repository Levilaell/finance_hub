// Script de exemplo para o frontend processar erros de validação corretamente

// Exemplo de como fazer a requisição de registro
async function register(userData) {
  try {
    const response = await fetch('https://finance-backend-production-29df.up.railway.app/api/auth/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });

    const data = await response.json();

    if (!response.ok) {
      // Processar erros de validação
      if (data.error && data.error.field_errors) {
        // Erros específicos de campos
        const fieldErrors = data.error.field_errors;
        
        // Exemplo de como mostrar os erros:
        Object.keys(fieldErrors).forEach(field => {
          const errors = fieldErrors[field];
          console.error(`Erro no campo ${field}:`, errors.join(', '));
          
          // No frontend, você deve mostrar esses erros próximos aos campos
          // Exemplo:
          // document.getElementById(`${field}-error`).textContent = errors.join(', ');
        });
        
        // Retornar os erros para o componente
        return {
          success: false,
          fieldErrors: fieldErrors,
          message: data.error.message
        };
      } else {
        // Erro genérico
        return {
          success: false,
          message: data.error?.message || 'Erro ao realizar cadastro'
        };
      }
    }

    // Sucesso!
    return {
      success: true,
      user: data.user,
      tokens: data.tokens,
      message: data.message
    };

  } catch (error) {
    console.error('Erro de rede:', error);
    return {
      success: false,
      message: 'Erro de conexão. Tente novamente.'
    };
  }
}

// Exemplo de uso:
const testData = {
  email: "teste@teste.com",  // Este email já existe!
  password: "SenhaForte123!",
  password2: "SenhaForte123!",
  first_name: "João",
  last_name: "Silva",
  phone: "(11) 98765-4321",
  company_name: "Empresa Teste",
  company_cnpj: "11.222.333/0001-81",
  company_type: "ltda",
  business_sector: "tecnologia"
};

// Testar
register(testData).then(result => {
  console.log('Resultado:', result);
  
  if (!result.success) {
    if (result.fieldErrors) {
      // Mostrar erros específicos de cada campo
      if (result.fieldErrors.email) {
        console.log('Erro no email:', result.fieldErrors.email[0]);
        // Mostrar no UI: "Este e-mail já está cadastrado."
      }
      if (result.fieldErrors.password) {
        console.log('Erro na senha:', result.fieldErrors.password);
      }
      // ... outros campos
    } else {
      // Erro genérico
      console.log('Erro:', result.message);
    }
  }
});

// Estrutura da resposta de erro:
// {
//   "error": {
//     "message": "Erro de validação nos dados fornecidos.",
//     "field_errors": {
//       "email": ["Este e-mail já está cadastrado."],
//       "password": ["A senha deve ter pelo menos 8 caracteres.", "A senha deve conter pelo menos uma letra maiúscula."],
//       "company_cnpj": ["CNPJ inválido. Verifique se digitou corretamente."]
//     }
//   }
// }