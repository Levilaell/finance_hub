/**
 * Request Manager for batching and deduplicating API requests
 * Prevents rate limiting issues by managing concurrent requests
 */

interface PendingRequest {
  promise: Promise<any>;
  timestamp: number;
}

class RequestManager {
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private requestQueue: Array<() => Promise<any>> = [];
  private activeRequests = 0;
  private readonly MAX_CONCURRENT_REQUESTS = 10;
  private readonly REQUEST_CACHE_TTL = 5000; // 5 seconds
  private readonly MIN_REQUEST_INTERVAL = 100; // 100ms between requests
  private lastRequestTime = 0;

  /**
   * Execute a request with deduplication and rate limiting
   */
  async executeRequest<T>(
    key: string,
    requestFn: () => Promise<T>,
    options: {
      cacheTTL?: number;
      skipCache?: boolean;
      priority?: boolean;
    } = {}
  ): Promise<T> {
    const { cacheTTL = this.REQUEST_CACHE_TTL, skipCache = false, priority = false } = options;

    // Check for pending request with the same key
    if (!skipCache) {
      const pending = this.pendingRequests.get(key);
      if (pending && Date.now() - pending.timestamp < cacheTTL) {
        return pending.promise;
      }
    }

    // Create request wrapper
    const wrappedRequest = async () => {
      // Rate limiting
      const now = Date.now();
      const timeSinceLastRequest = now - this.lastRequestTime;
      if (timeSinceLastRequest < this.MIN_REQUEST_INTERVAL) {
        await this.delay(this.MIN_REQUEST_INTERVAL - timeSinceLastRequest);
      }
      this.lastRequestTime = Date.now();

      this.activeRequests++;
      try {
        const result = await requestFn();
        return result;
      } finally {
        this.activeRequests--;
        this.pendingRequests.delete(key);
        this.processQueue();
      }
    };

    // Create promise for this request
    const requestPromise = this.enqueueRequest(wrappedRequest, priority);

    // Store in pending requests
    this.pendingRequests.set(key, {
      promise: requestPromise,
      timestamp: Date.now(),
    });

    return requestPromise;
  }

  /**
   * Batch multiple requests into a single execution
   */
  async batchRequests<T>(
    requests: Array<{
      key: string;
      fn: () => Promise<any>;
      transform?: (data: any) => T;
    }>
  ): Promise<T[]> {
    const results = await Promise.all(
      requests.map(({ key, fn, transform }) =>
        this.executeRequest(key, fn).then(data => transform ? transform(data) : data)
      )
    );
    return results;
  }

  /**
   * Clear cache for specific key or all keys
   */
  clearCache(key?: string) {
    if (key) {
      this.pendingRequests.delete(key);
    } else {
      this.pendingRequests.clear();
    }
  }

  /**
   * Get current queue status
   */
  getStatus() {
    return {
      activeRequests: this.activeRequests,
      queuedRequests: this.requestQueue.length,
      cachedRequests: this.pendingRequests.size,
    };
  }

  private async enqueueRequest<T>(
    requestFn: () => Promise<T>,
    priority: boolean
  ): Promise<T> {
    // If under limit, execute immediately
    if (this.activeRequests < this.MAX_CONCURRENT_REQUESTS) {
      return requestFn();
    }

    // Otherwise, queue the request
    return new Promise((resolve, reject) => {
      const queuedFn = async () => {
        try {
          const result = await requestFn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      };

      if (priority) {
        this.requestQueue.unshift(queuedFn);
      } else {
        this.requestQueue.push(queuedFn);
      }
    });
  }

  private processQueue() {
    while (
      this.requestQueue.length > 0 &&
      this.activeRequests < this.MAX_CONCURRENT_REQUESTS
    ) {
      const nextRequest = this.requestQueue.shift();
      if (nextRequest) {
        nextRequest();
      }
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Singleton instance
export const requestManager = new RequestManager();

// Helper function for creating request keys
export function createRequestKey(url: string, params?: any): string {
  const paramStr = params ? JSON.stringify(params) : '';
  return `${url}:${paramStr}`;
}