// hooks/use-pluggy-providers.ts
import { useState, useEffect } from 'react';
import { bankingService } from '@/services/banking.service';

interface PluggyProvider {
  id: number;
  name: string;
  code: string;
  logo?: string;
  primary_color?: string;
  health_status: string;
  supports_accounts: boolean;
  supports_transactions: boolean;
  is_sandbox: boolean;
}

export function usePluggyProviders() {
  const [providers, setProviders] = useState<PluggyProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sandboxMode, setSandboxMode] = useState(false);

  const fetchProviders = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('🏦 Fetching Pluggy banks...');
        
        // ✅ USAR: endpoint Pluggy específico
        const response = await bankingService.getPluggyBanks();
        
        console.log('🏦 Pluggy banks response:', response);
        
        if (response.success) {
          setProviders(response.data as any);
          setSandboxMode(response.sandbox_mode);
          console.log(`🏦 Loaded ${response.data.length} banks (sandbox: ${response.sandbox_mode})`);
        } else {
          throw new Error('Failed to fetch banks from Pluggy');
        }
      } catch (err: any) {
        console.error('❌ Error fetching Pluggy providers:', err);
        setError(err.message || 'Failed to fetch bank providers');
        
        // Fallback providers para desenvolvimento
        setProviders([
          {
            id: 999,
            name: 'Pluggy Bank (Sandbox)',
            code: 'pluggy-sandbox',
            health_status: 'ONLINE',
            supports_accounts: true,
            supports_transactions: true,
            is_sandbox: true,
            primary_color: '#007BFF'
          }
        ]);
        setSandboxMode(true);
      } finally {
        setLoading(false);
      }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  return { 
    providers, 
    loading, 
    error, 
    sandboxMode,
    refresh: () => {
      setLoading(true);
      fetchProviders();
    }
  };
}