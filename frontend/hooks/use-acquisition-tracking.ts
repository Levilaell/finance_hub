'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

const STORAGE_KEY = 'acquisition_angle';

/**
 * Hook para capturar e persistir o parâmetro de aquisição (UTM).
 * Captura o parâmetro "a" da URL e salva em localStorage.
 *
 * Valores esperados: time, price, delay, visibility
 * Exemplo de URL: /dtr?a=time
 */
export function useAcquisitionTracking() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const angle = searchParams.get('a');

    if (angle) {
      // Salva no localStorage para persistir entre páginas
      localStorage.setItem(STORAGE_KEY, angle);
    }
  }, [searchParams]);
}

/**
 * Recupera o ângulo de aquisição do localStorage.
 * Usar no momento do registro para enviar ao backend.
 */
export function getAcquisitionAngle(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEY);
}

/**
 * Limpa o ângulo de aquisição do localStorage.
 * Chamar após registro bem-sucedido.
 */
export function clearAcquisitionAngle(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}
