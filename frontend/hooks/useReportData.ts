import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { toast } from 'sonner';
import { reportsService } from '@/services/reports.service';
import { bankingService } from '@/services/banking.service';
import { categoriesService } from '@/services/categories.service';
import type { Report, DateRange, ReportData } from '@/types/reports';

interface UseReportDataOptions {
  initialPeriod?: DateRange;
  retryAttempts?: number;
  staleTime?: number;
  gcTime?: number;
  onError?: (error: any) => void;
}

interface UseReportDataReturn {
  reports: Report[] | undefined;
  accounts: any[] | undefined;
  categories: any[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: any;
  refetch: () => void;
  refetchAll: () => Promise<void>;
  selectedPeriod: DateRange | undefined;
  setSelectedPeriod: (period: DateRange) => void;
  retryCount: number;
}

const DEFAULT_RETRY_ATTEMPTS = 3;
const DEFAULT_STALE_TIME = 5 * 60 * 1000; // 5 minutes
const DEFAULT_GC_TIME = 10 * 60 * 1000; // 10 minutes

/**
 * Custom hook for fetching and managing report data with enhanced error handling
 */
export function useReportData(options: UseReportDataOptions = {}): UseReportDataReturn {
  const {
    initialPeriod,
    retryAttempts = DEFAULT_RETRY_ATTEMPTS,
    staleTime = DEFAULT_STALE_TIME,
    gcTime = DEFAULT_GC_TIME,
    onError
  } = options;

  const queryClient = useQueryClient();
  const [selectedPeriod, setSelectedPeriod] = useState<DateRange | undefined>(initialPeriod);
  const [retryCount, setRetryCount] = useState(0);

  // Ensure selectedPeriod is always defined with a default fallback
  const effectiveSelectedPeriod = selectedPeriod || initialPeriod;

  // Common query options with retry logic
  const commonQueryOptions: Partial<UseQueryOptions> = {
    staleTime,
    gcTime,
    retry: (failureCount, error) => {
      if (failureCount < retryAttempts) {
        setRetryCount(failureCount);
        // Exponential backoff
        const delay = Math.min(1000 * 2 ** failureCount, 30000);
        console.log(`Retrying request (attempt ${failureCount + 1}/${retryAttempts}) after ${delay}ms`);
        return true;
      }
      return false;
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  };

  // Fetch reports with error recovery
  const {
    data: reports,
    isLoading: reportsLoading,
    isError: reportsError,
    error: reportsErrorObj,
    refetch: refetchReports
  } = useQuery({
    queryKey: ['reports', effectiveSelectedPeriod || 'default'],
    queryFn: async () => {
      try {
        console.log('📋 useReportData: Iniciando busca de relatórios');
        const data = await reportsService.getReports();
        setRetryCount(0); // Reset retry count on success
        
        console.log('📋 useReportData: Dados recebidos:', data);
        console.log('📋 useReportData: Tipo dos dados:', typeof data);
        console.log('📋 useReportData: É array?', Array.isArray(data));
        
        // Ensure we return an array, handling both paginated and non-paginated responses
        if (Array.isArray(data)) {
          console.log('📋 useReportData: Retornando array direto');
          return data;
        } else if (data && data.results) {
          console.log('📋 useReportData: Retornando data.results');
          return data.results;
        }
        console.log('📋 useReportData: Retornando array vazio (fallback)');
        return [];
      } catch (error: any) {
        console.error('❌ useReportData: Erro ao buscar relatórios:', error);
        console.error('📊 useReportData: Response data:', error.response?.data);
        console.error('📈 useReportData: Status:', error.response?.status);
        
        // Check if we have cached data to fall back on
        const cachedData = queryClient.getQueryData(['reports']);
        if (cachedData) {
          console.log('📋 useReportData: Usando dados em cache como fallback');
          toast.info('Usando dados em cache enquanto reconectamos...');
          return cachedData;
        }
        
        // Provide specific error messages based on error type
        if (error.response?.status === 401) {
          toast.error('Sessão expirada. Por favor, faça login novamente.');
        } else if (error.response?.status === 403) {
          toast.error('Você não tem permissão para acessar os relatórios.');
        } else if (error.response?.status === 500) {
          toast.error('Erro interno do servidor. Tente novamente em alguns minutos.');
        } else {
          toast.error('Falha ao carregar relatórios. Verifique sua conexão.');
        }
        
        throw error;
      }
    },
    ...commonQueryOptions
  });

  // Fetch accounts with prefetching
  const {
    data: accounts,
    isLoading: accountsLoading,
    isError: accountsError
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => bankingService.getAccounts(),
    ...commonQueryOptions
  });

  // Fetch categories with prefetching
  const {
    data: categories,
    isLoading: categoriesLoading,
    isError: categoriesError
  } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesService.getCategories(),
    ...commonQueryOptions
  });

  // Prefetch related data on mount
  useEffect(() => {
    // Prefetch next likely queries
    const prefetchRelatedData = async () => {
      // Prefetch common report types
      await queryClient.prefetchQuery({
        queryKey: ['report-templates'],
        queryFn: () => reportsService.getReportTemplates(),
        staleTime: 60 * 60 * 1000 // 1 hour
      });

      // Prefetch analytics data if reports are loaded
      const reportsData = reports as { results: Report[] } | undefined;
      if (reportsData && reportsData.results && reportsData.results.length > 0) {
        await queryClient.prefetchQuery({
          queryKey: ['analytics', effectiveSelectedPeriod],
          queryFn: () => reportsService.getAnalytics(30),
          staleTime: 15 * 60 * 1000 // 15 minutes
        });
      }
    };

    prefetchRelatedData();
  }, [reports, effectiveSelectedPeriod, queryClient]);

  // Refetch all data with proper error handling
  const refetchAll = useCallback(async () => {
    try {
      setRetryCount(0);
      await Promise.all([
        refetchReports(),
        queryClient.invalidateQueries({ queryKey: ['accounts'] }),
        queryClient.invalidateQueries({ queryKey: ['categories'] })
      ]);
      toast.success('Dados atualizados com sucesso!');
    } catch (error) {
      console.error('Error refetching data:', error);
      toast.error('Erro ao atualizar dados. Tente novamente.');
    }
  }, [refetchReports, queryClient]);

  // Combined loading and error states
  const isLoading = reportsLoading || accountsLoading || categoriesLoading;
  const isError = reportsError || accountsError || categoriesError;
  const error = reportsErrorObj || (accountsError ? 'Error loading accounts' : null) || 
                (categoriesError ? 'Error loading categories' : null);

  // Set up automatic retry on network recovery
  useEffect(() => {
    const handleOnline = () => {
      if (isError) {
        console.log('Network recovered, retrying failed queries...');
        toast.info('Conexão restaurada. Atualizando dados...');
        refetchAll();
      }
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [isError, refetchAll]);

  return {
    reports: (reports as Report[] | undefined) || [],
    accounts: (accounts as any[]) || [],
    categories: (categories as any[]) || [],
    isLoading,
    isError,
    error,
    refetch: refetchAll,
    refetchAll,
    selectedPeriod: effectiveSelectedPeriod,
    setSelectedPeriod,
    retryCount
  };
}

/**
 * Hook for managing report generation with progress tracking
 */
export function useReportGeneration() {
  const queryClient = useQueryClient();
  const [generatingReports, setGeneratingReports] = useState<Set<string>>(new Set());

  const generateReport = useCallback(async (params: any) => {
    const reportId = `${params.report_type}_${params.period_start}_${params.period_end}`;
    
    try {
      setGeneratingReports(prev => new Set(prev).add(reportId));
      
      const report = await reportsService.generateReport(
        params.report_type, 
        params, 
        params.format || 'pdf'
      );
      
      // Poll for completion
      const checkStatus = async () => {
        const status = await reportsService.getReportStatus(report.id);
        
        if (status.is_generated) {
          toast.success('Relatório gerado com sucesso!');
          queryClient.invalidateQueries({ queryKey: ['reports'] });
          setGeneratingReports(prev => {
            const next = new Set(prev);
            next.delete(reportId);
            return next;
          });
          return status;
        } else if (status.error_message) {
          throw new Error(status.error_message);
        } else {
          // Continue polling
          await new Promise(resolve => setTimeout(resolve, 2000));
          return checkStatus();
        }
      };
      
      return await checkStatus();
      
    } catch (error: any) {
      setGeneratingReports(prev => {
        const next = new Set(prev);
        next.delete(reportId);
        return next;
      });
      
      if (error.response?.status === 409) {
        toast.error('Relatório já está sendo gerado. Aguarde a conclusão.');
      } else {
        toast.error(`Erro ao gerar relatório: ${error.message}`);
      }
      
      throw error;
    }
  }, [queryClient]);

  return {
    generateReport,
    isGenerating: (reportType: string, startDate: string, endDate: string) => {
      const reportId = `${reportType}_${startDate}_${endDate}`;
      return generatingReports.has(reportId);
    },
    generatingCount: generatingReports.size
  };
}