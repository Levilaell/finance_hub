/**
 * Hook for monitoring MFA timeout status
 * Monitors Pluggy items that are waiting for user action and shows countdown
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import { bankingService } from '@/services/banking.service';

interface MFATimeoutState {
  isActive: boolean;
  remainingTime: number; // seconds
  itemId: string | null;
  institutionName: string | null;
  startTime: number | null;
}

interface UseMFATimeoutOptions {
  timeout?: number; // Total timeout in seconds (default 60)
  onTimeout?: (itemId: string) => void;
  onWarning?: (remainingTime: number) => void;
  warningThreshold?: number; // Show warning when time <= threshold (default 20s)
}

export function useMFATimeout(options: UseMFATimeoutOptions = {}) {
  const {
    timeout = 60,
    onTimeout,
    onWarning,
    warningThreshold = 20
  } = options;

  const [state, setState] = useState<MFATimeoutState>({
    isActive: false,
    remainingTime: 0,
    itemId: null,
    institutionName: null,
    startTime: null
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const hasWarned = useRef(false);

  // Query to get items waiting for user action
  const { data: waitingItems } = useQuery({
    queryKey: ['banking', 'waiting-items'],
    queryFn: () => bankingService.getWaitingItems(),
    refetchInterval: 5000, // Check every 5 seconds
    enabled: true,
    select: (response) => response.success ? response.data : []
  });

  // Start MFA timeout monitoring
  const startMFATimeout = useCallback((itemId: string, institutionName?: string) => {
    const startTime = Date.now();
    
    setState({
      isActive: true,
      remainingTime: timeout,
      itemId,
      institutionName: institutionName || null,
      startTime
    });

    hasWarned.current = false;

    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Start countdown
    intervalRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.max(0, timeout - elapsed);

      setState(prev => ({
        ...prev,
        remainingTime: remaining
      }));

      // Warning threshold
      if (remaining <= warningThreshold && !hasWarned.current) {
        hasWarned.current = true;
        onWarning?.(remaining);
        toast.warning(`⏰ Tempo para inserir código MFA: ${remaining}s restantes`, {
          duration: 5000
        });
      }

      // Timeout reached
      if (remaining <= 0) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }

        setState(prev => ({
          ...prev,
          isActive: false,
          remainingTime: 0
        }));

        onTimeout?.(itemId);
        toast.error('⌛ Tempo esgotado para inserir código MFA. Reconecte sua conta.', {
          duration: 10000
        });
      }
    }, 1000);
  }, [timeout, onTimeout, onWarning, warningThreshold]);

  // Stop MFA timeout monitoring
  const stopMFATimeout = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setState({
      isActive: false,
      remainingTime: 0,
      itemId: null,
      institutionName: null,
      startTime: null
    });

    hasWarned.current = false;
  }, []);

  // Auto-start timeout when items are waiting for action
  useEffect(() => {
    if (!waitingItems || waitingItems.length === 0) {
      if (state.isActive) {
        stopMFATimeout();
      }
      return;
    }

    // Find item waiting for MFA
    const waitingItem = waitingItems.find((item: any) => 
      item.status === 'WAITING_USER_INPUT' || 
      item.execution_status === 'WAITING_USER_INPUT'
    );

    if (waitingItem && !state.isActive) {
      // Start timeout for this item
      startMFATimeout(
        waitingItem.id || waitingItem.pluggy_item_id,
        waitingItem.connector?.name || 'Banco'
      );
    }
  }, [waitingItems, state.isActive, startMFATimeout, stopMFATimeout]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Format remaining time for display
  const formatTime = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (mins > 0) {
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    return `${secs}s`;
  }, []);

  // Get status info for UI
  const getStatusInfo = useCallback(() => {
    if (!state.isActive) {
      return null;
    }

    const isUrgent = state.remainingTime <= warningThreshold;
    const isCritical = state.remainingTime <= 10;

    return {
      isUrgent,
      isCritical,
      remainingTime: state.remainingTime,
      formattedTime: formatTime(state.remainingTime),
      itemId: state.itemId,
      institutionName: state.institutionName,
      progress: ((timeout - state.remainingTime) / timeout) * 100
    };
  }, [state, timeout, warningThreshold, formatTime]);

  return {
    // State
    isActive: state.isActive,
    remainingTime: state.remainingTime,
    itemId: state.itemId,
    institutionName: state.institutionName,
    
    // Actions
    startMFATimeout,
    stopMFATimeout,
    
    // Helpers
    formatTime,
    getStatusInfo
  };
}