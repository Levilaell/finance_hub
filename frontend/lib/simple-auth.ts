/**
 * SIMPLE AUTH - Autenticação Ultra-Simplificada para MVP
 * 
 * Elimina complexidades que podem causar o erro "O token informado não é válido"
 * Foco em confiabilidade e simplicidade.
 */

import { useState, useEffect } from 'react';
import type { User } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Storage super simples - sem interceptors complexos
class SimpleStorage {
  setTokens(tokens: { access: string; refresh: string }) {
    try {
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      console.log('✅ Tokens stored successfully');
    } catch (error) {
      console.error('❌ Failed to store tokens:', error);
    }
  }

  getAccessToken(): string | null {
    try {
      return localStorage.getItem('access_token');
    } catch (error) {
      console.error('❌ Failed to get access token:', error);
      return null;
    }
  }

  getRefreshToken(): string | null {
    try {
      return localStorage.getItem('refresh_token');
    } catch (error) {
      console.error('❌ Failed to get refresh token:', error);
      return null;
    }
  }

  clearTokens() {
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      console.log('✅ Tokens cleared');
    } catch (error) {
      console.error('❌ Failed to clear tokens:', error);
    }
  }
}

// API Client Super Simples
class SimpleAuthAPI {
  private storage = new SimpleStorage();

  // Login mais simples possível
  async login(email: string, password: string) {
    try {
      const response = await fetch(`${API_URL}/api/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Login failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.access && data.refresh) {
        this.storage.setTokens({
          access: data.access,
          refresh: data.refresh
        });
        return data;
      } else {
        throw new Error('Invalid login response format');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      throw error;
    }
  }

  // Logout simples
  async logout() {
    try {
      this.storage.clearTokens();
      // Opcional: chamar endpoint de logout no backend
      window.location.href = '/login';
    } catch (error) {
      console.error('❌ Logout error:', error);
      // Mesmo com erro, limpar tokens localmente
      this.storage.clearTokens();
      window.location.href = '/login';
    }
  }

  // Verificar se usuário está logado
  isAuthenticated(): boolean {
    const token = this.storage.getAccessToken();
    if (!token) return false;

    try {
      // Verificação básica de formato JWT
      const parts = token.split('.');
      if (parts.length !== 3) return false;

      // Decodificar payload (sem validar assinatura - isso é feito no backend)
      const payload = JSON.parse(atob(parts[1]));
      const now = Date.now() / 1000;
      
      // Se token expirou há mais de 1 hora, consideramos inválido
      if (payload.exp && payload.exp < now - 3600) {
        this.storage.clearTokens();
        return false;
      }

      return true;
    } catch (error) {
      console.error('❌ Token validation error:', error);
      this.storage.clearTokens();
      return false;
    }
  }

  // Fazer requisição autenticada simples
  async authenticatedRequest(url: string, options: RequestInit = {}) {
    const token = this.storage.getAccessToken();
    
    if (!token) {
      throw new Error('No access token available');
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    try {
      const response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        // Token inválido - limpar e redirecionar para login
        console.warn('⚠️ Token invalid, redirecting to login');
        this.storage.clearTokens();
        window.location.href = '/login';
        throw new Error('Authentication required');
      }

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error(`❌ Authenticated request error for ${url}:`, error);
      throw error;
    }
  }

  // Método para obter dados do usuário atual
  async getCurrentUser() {
    return this.authenticatedRequest('/api/auth/profile/');
  }
}

// Instância global
export const simpleAuth = new SimpleAuthAPI();

// Hook simples para React
export function useSimpleAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setIsAuthenticated(simpleAuth.isAuthenticated());
    
    if (simpleAuth.isAuthenticated()) {
      simpleAuth.getCurrentUser()
        .then(setUser)
        .catch(() => setUser(null));
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const result = await simpleAuth.login(email, password);
      setIsAuthenticated(true);
      setUser(result.user);
      return result;
    } catch (error) {
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  };

  const logout = async () => {
    await simpleAuth.logout();
    setIsAuthenticated(false);
    setUser(null);
  };

  return {
    isAuthenticated,
    user,
    login,
    logout,
    authenticatedRequest: simpleAuth.authenticatedRequest.bind(simpleAuth),
  };
}

// Função para usar em componentes Next.js
export default simpleAuth;