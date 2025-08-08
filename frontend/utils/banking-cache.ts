/**
 * Banking data caching utilities
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class BankingCache {
  private static readonly CACHE_PREFIX = 'banking_cache_';
  
  // Default TTLs (in milliseconds)
  private static readonly TTL = {
    accounts: 30 * 60 * 1000, // 30 minutes
    transactions: 15 * 60 * 1000, // 15 minutes
    categories: 60 * 60 * 1000, // 1 hour
    connectors: 24 * 60 * 60 * 1000, // 24 hours
    dashboard: 5 * 60 * 1000, // 5 minutes
  };

  /**
   * Get cached data if valid
   */
  static get<T>(key: string): T | null {
    try {
      const cached = localStorage.getItem(`${this.CACHE_PREFIX}${key}`);
      if (!cached) return null;

      const entry: CacheEntry<T> = JSON.parse(cached);
      const now = Date.now();

      // Check if cache is expired
      if (now - entry.timestamp > entry.ttl) {
        this.remove(key);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }

  /**
   * Set cache data
   */
  static set<T>(key: string, data: T, ttl?: number): void {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl: ttl || this.getDefaultTTL(key),
      };

      localStorage.setItem(
        `${this.CACHE_PREFIX}${key}`,
        JSON.stringify(entry)
      );
    } catch (error) {
      console.error('Cache write error:', error);
      // If storage is full, clear old entries
      if (error instanceof DOMException && error.code === 22) {
        this.clearOldEntries();
        // Try again
        try {
          localStorage.setItem(
            `${this.CACHE_PREFIX}${key}`,
            JSON.stringify({ data, timestamp: Date.now(), ttl })
          );
        } catch {
          // Give up if still failing
        }
      }
    }
  }

  /**
   * Remove cached data
   */
  static remove(key: string): void {
    localStorage.removeItem(`${this.CACHE_PREFIX}${key}`);
  }

  /**
   * Clear all banking cache
   */
  static clear(): void {
    const keys = Object.keys(localStorage);
    keys.forEach((key) => {
      if (key.startsWith(this.CACHE_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
  }

  /**
   * Clear old cache entries
   */
  static clearOldEntries(): void {
    const keys = Object.keys(localStorage);
    const now = Date.now();

    keys.forEach((key) => {
      if (key.startsWith(this.CACHE_PREFIX)) {
        try {
          const cached = localStorage.getItem(key);
          if (cached) {
            const entry = JSON.parse(cached);
            if (now - entry.timestamp > entry.ttl) {
              localStorage.removeItem(key);
            }
          }
        } catch {
          // Remove invalid entries
          localStorage.removeItem(key);
        }
      }
    });
  }

  /**
   * Get default TTL based on key pattern
   */
  private static getDefaultTTL(key: string): number {
    if (key.includes('accounts')) return this.TTL.accounts;
    if (key.includes('transactions')) return this.TTL.transactions;
    if (key.includes('categories')) return this.TTL.categories;
    if (key.includes('connectors')) return this.TTL.connectors;
    if (key.includes('dashboard')) return this.TTL.dashboard;
    return 15 * 60 * 1000; // Default 15 minutes
  }

  /**
   * Create cache key
   */
  static createKey(...parts: string[]): string {
    return parts.filter(Boolean).join('_');
  }

  /**
   * Check if data needs refresh
   */
  static needsRefresh(key: string, forceRefreshAfter?: number): boolean {
    try {
      const cached = localStorage.getItem(`${this.CACHE_PREFIX}${key}`);
      if (!cached) return true;

      const entry: CacheEntry<any> = JSON.parse(cached);
      const now = Date.now();
      const age = now - entry.timestamp;

      // Force refresh if specified
      if (forceRefreshAfter && age > forceRefreshAfter) {
        return true;
      }

      // Check normal expiry
      return age > entry.ttl;
    } catch {
      return true;
    }
  }

  /**
   * Get cache age in milliseconds
   */
  static getAge(key: string): number | null {
    try {
      const cached = localStorage.getItem(`${this.CACHE_PREFIX}${key}`);
      if (!cached) return null;

      const entry: CacheEntry<any> = JSON.parse(cached);
      return Date.now() - entry.timestamp;
    } catch {
      return null;
    }
  }
}

/**
 * React hook for cached data
 */
export function useCachedData<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: {
    ttl?: number;
    forceRefresh?: boolean;
    onError?: (error: Error) => void;
  }
): {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
} {
  const [data, setData] = React.useState<T | null>(() => 
    options?.forceRefresh ? null : BankingCache.get<T>(key)
  );
  const [isLoading, setIsLoading] = React.useState(!data);
  const [error, setError] = React.useState<Error | null>(null);

  const refresh = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const freshData = await fetcher();
      BankingCache.set(key, freshData, options?.ttl);
      setData(freshData);
    } catch (err) {
      const error = err as Error;
      setError(error);
      options?.onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [key, fetcher, options]);

  React.useEffect(() => {
    // Check if we need to fetch
    if (!data || options?.forceRefresh) {
      refresh();
    } else {
      // Check if cache is stale
      const needsRefresh = BankingCache.needsRefresh(key);
      if (needsRefresh) {
        refresh();
      }
    }
  }, [key, options?.forceRefresh]);

  return { data, isLoading, error, refresh };
}

// Import React at the end to avoid circular dependency
import React from 'react';