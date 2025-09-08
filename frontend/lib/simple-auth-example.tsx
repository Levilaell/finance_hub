/**
 * EXEMPLO DE USO - Simple Auth
 * 
 * Como usar a autenticação simplificada em componentes React/Next.js
 */

import React from 'react';
import { useSimpleAuth } from './simple-auth';

// Exemplo 1: Página de Login
export function LoginPage() {
  const { login } = useSimpleAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
      // Redirecionamento será feito automaticamente
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.message || 'Erro no login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="email" 
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input 
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

// Exemplo 2: Componente Protegido
export function ProtectedComponent() {
  const { isAuthenticated, user, logout } = useSimpleAuth();

  if (!isAuthenticated) {
    return <div>Acesso negado. <a href="/login">Fazer login</a></div>;
  }

  return (
    <div>
      <h1>Bem-vindo, {user?.first_name || user?.email}!</h1>
      <button onClick={logout}>Sair</button>
    </div>
  );
}

// Exemplo 3: Fazer Requisições Autenticadas
export function DataComponent() {
  const { authenticatedRequest } = useSimpleAuth();
  const [data, setData] = useState(null);

  useEffect(() => {
    authenticatedRequest('/api/dashboard/stats/')
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div>
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <div>Carregando...</div>
      )}
    </div>
  );
}
