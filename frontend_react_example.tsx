// Exemplo de como processar erros de validação no React/TypeScript

interface FieldErrors {
  [key: string]: string[];
}

interface RegisterResponse {
  user?: any;
  tokens?: {
    access: string;
    refresh: string;
  };
  message?: string;
  error?: {
    message: string;
    field_errors?: FieldErrors;
  };
}

// Hook ou função para registro
const useRegister = () => {
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  const register = async (formData: any) => {
    setLoading(true);
    setFieldErrors({});

    try {
      const response = await fetch(`${API_URL}/api/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data: RegisterResponse = await response.json();

      if (!response.ok) {
        // Processar erros de validação
        if (data.error?.field_errors) {
          setFieldErrors(data.error.field_errors);
          
          // Mostrar primeira mensagem de erro como toast/alert
          const firstField = Object.keys(data.error.field_errors)[0];
          const firstError = data.error.field_errors[firstField][0];
          toast.error(firstError);
          
          return { success: false, fieldErrors: data.error.field_errors };
        }

        // Erro genérico
        toast.error(data.error?.message || 'Erro ao realizar cadastro');
        return { success: false };
      }

      // Sucesso
      toast.success(data.message || 'Cadastro realizado com sucesso!');
      return { success: true, data };

    } catch (error) {
      toast.error('Erro de conexão. Tente novamente.');
      return { success: false };
    } finally {
      setLoading(false);
    }
  };

  return { register, fieldErrors, loading };
};

// Componente de formulário
const RegisterForm = () => {
  const { register, fieldErrors, loading } = useRegister();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    phone: '',
    company_name: '',
    company_cnpj: '',
    company_type: '',
    business_sector: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await register(formData);
    
    if (result.success) {
      // Redirecionar ou fazer login automático
      // router.push('/dashboard');
    }
  };

  // Função helper para pegar erro de um campo
  const getFieldError = (fieldName: string): string | null => {
    return fieldErrors[fieldName]?.[0] || null;
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Campo de Email */}
      <div className="form-group">
        <input
          type="email"
          placeholder="E-mail"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className={getFieldError('email') ? 'error' : ''}
        />
        {getFieldError('email') && (
          <span className="error-message">{getFieldError('email')}</span>
        )}
      </div>

      {/* Campo de Senha */}
      <div className="form-group">
        <input
          type="password"
          placeholder="Senha"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className={getFieldError('password') ? 'error' : ''}
        />
        {getFieldError('password') && (
          <span className="error-message">{getFieldError('password')}</span>
        )}
      </div>

      {/* Campo de CNPJ */}
      <div className="form-group">
        <input
          type="text"
          placeholder="CNPJ"
          value={formData.company_cnpj}
          onChange={(e) => setFormData({ ...formData, company_cnpj: e.target.value })}
          className={getFieldError('company_cnpj') ? 'error' : ''}
        />
        {getFieldError('company_cnpj') && (
          <span className="error-message">{getFieldError('company_cnpj')}</span>
        )}
      </div>

      {/* ... outros campos ... */}

      <button type="submit" disabled={loading}>
        {loading ? 'Cadastrando...' : 'Cadastrar'}
      </button>
    </form>
  );
};

// CSS sugerido
const styles = `
  .form-group {
    margin-bottom: 1rem;
  }

  .error-message {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    display: block;
  }

  input.error {
    border-color: #ef4444;
  }
`;