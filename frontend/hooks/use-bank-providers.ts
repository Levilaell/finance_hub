import { useState, useEffect } from 'react';
import bankProvidersData from '@/data/bank-providers.json';

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
    console.log('🔄 Starting to load providers...');
    console.log('📄 Static import result:', bankProvidersData);
    console.log('📄 Is array:', Array.isArray(bankProvidersData));
    console.log('📄 Length:', bankProvidersData?.length);
    
    // Immediate synchronous load since we have static import
    if (Array.isArray(bankProvidersData) && bankProvidersData.length > 0) {
      console.log('✅ Setting providers from static import');
      setProviders(bankProvidersData as BankProvider[]);
    } else {
      console.log('🆘 Using hardcoded providers as fallback');
      // Hardcoded providers as fallback
      setProviders([
        {
          id: 1,
          name: 'Nubank',
          code: '260',
          color: '#8A05BE',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
        {
          id: 2,
          name: 'Itaú',
          code: '341',
          color: '#EC7000',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
        {
          id: 3,
          name: 'Bradesco',
          code: '237',
          color: '#CC092F',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
        {
          id: 4,
          name: 'Banco do Brasil',
          code: '001',
          color: '#F8E71C',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
        {
          id: 5,
          name: 'Santander',
          code: '033',
          color: '#EC0000',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
        {
          id: 6,
          name: 'Inter',
          code: '077',
          color: '#FF7A00',
          is_open_banking: true,
          supports_pix: true,
          supports_ted: true,
        },
      ]);
    }
    
    setLoading(false);
  }, []);

  // Debug log when providers change
  useEffect(() => {
    console.log('🏦 Providers state updated:', providers.length, 'providers');
  }, [providers]);

  return { providers, loading, error };
}