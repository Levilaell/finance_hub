'use client';

import { useClientOnly } from '@/hooks/use-client-only';
import { ReactNode } from 'react';

interface HydrationBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Component to prevent hydration mismatches by rendering fallback during SSR
 * and actual content only after client-side hydration
 */
export function HydrationBoundary({ children, fallback }: HydrationBoundaryProps) {
  const isClient = useClientOnly();

  if (!isClient) {
    return fallback || <div className="animate-pulse bg-gray-200 h-4 w-full rounded" />;
  }

  return <>{children}</>;
}