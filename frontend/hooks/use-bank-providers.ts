import { useState, useEffect } from 'react';
import { pluggyService } from '@/services/pluggy.service';

interface BankProvider {
  id: number;
  name: string;
  code: string;
  logo?: string;
  color?: string;
  is_open_banking: boolean;
  supports_pix: boolean;
  supports_ted: boolean;
}

export function useBankProviders() {
  const [providers, setProviders] = useState<BankProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProviders() {
      try {
        
        // Get banks from Pluggy
        const pluggyBanks = await pluggyService.getSupportedBanks();
        
        // Validate response
        if (!Array.isArray(pluggyBanks)) {
          console.warn('Pluggy returned non-array:', pluggyBanks);
          throw new Error('Invalid response format from Pluggy');
        }
        
        // Convert Pluggy format to our format
        const mappedProviders: BankProvider[] = pluggyBanks.map(bank => ({
          id: bank.id || 0,
          name: bank.name || 'Unknown Bank',
          code: bank.code || String(bank.id),
          logo: bank.logo,
          color: bank.primary_color ? `#${bank.primary_color}` : (bank.color || '#000000'),
          is_open_banking: true, // All Pluggy banks support open banking
          supports_pix: true,
          supports_ted: true,
        }));
        
        setProviders(mappedProviders);
        
      } catch (err: any) {
        console.error('❌ Error loading banks from Pluggy:', err);
        setError(err.message || 'Erro ao carregar bancos');
        
        // Fallback to static banks
        setProviders([
          {
            id: 200,
            name: 'MeuPluggy',
            code: '200',
            color: '#FF6B35',
            is_open_banking: true,
            supports_pix: true,
            supports_ted: true,
          },
          {
            id: 201,
            name: 'Banco do Brasil',
            code: '001',
            color: '#F8E71C',
            is_open_banking: true,
            supports_pix: true,
            supports_ted: true,
          },
          {
            id: 202,
            name: 'Itaú',
            code: '341',
            color: '#EC7000',
            is_open_banking: true,
            supports_pix: true,
            supports_ted: true,
          },
          {
            id: 203,
            name: 'Bradesco',
            code: '237',
            color: '#CC092F',
            is_open_banking: true,
            supports_pix: true,
            supports_ted: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
    
    fetchProviders();
  }, []);

  // Debug log when providers change
  useEffect(() => {
  }, [providers]);

  return { providers, loading, error };
}