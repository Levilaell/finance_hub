/**
 * Retry Manager with Exponential Backoff
 * Handles rate limiting and transient errors gracefully
 */

import { AxiosError } from 'axios';

interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  shouldRetry?: (error: AxiosError) => boolean;
  onRetry?: (attempt: number, delay: number, error: AxiosError) => void;
}

interface QueuedRequest<T> {
  execute: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: any) => void;
  options: RetryOptions;
  attempts: number;
}

class RetryManager {
  private queue: QueuedRequest<any>[] = [];
  private isProcessing = false;
  private rateLimitResetTime: number | null = null;

  /**
   * Default configuration
   */
  private defaultOptions: Required<RetryOptions> = {
    maxRetries: 3,
    initialDelay: 1000, // 1 second
    maxDelay: 30000, // 30 seconds
    backoffMultiplier: 2,
    shouldRetry: (error: AxiosError) => {
      // Retry on rate limits, network errors, and 5xx errors
      if (!error.response) return true; // Network error
      const status = error.response.status;
      return status === 429 || status >= 500;
    },
    onRetry: (attempt, delay, error) => {
    }
  };

  /**
   * Execute a request with retry logic
   */
  async executeWithRetry<T>(
    request: () => Promise<T>,
    options: RetryOptions = {}
  ): Promise<T> {
    const mergedOptions = { ...this.defaultOptions, ...options };

    return new Promise<T>((resolve, reject) => {
      const queuedRequest: QueuedRequest<T> = {
        execute: request,
        resolve,
        reject,
        options: mergedOptions,
        attempts: 0
      };

      this.queue.push(queuedRequest);
      this.processQueue();
    });
  }

  /**
   * Process the request queue
   */
  private async processQueue() {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    // Check if we're still in rate limit window
    if (this.rateLimitResetTime && Date.now() < this.rateLimitResetTime) {
      const delay = this.rateLimitResetTime - Date.now();
      setTimeout(() => this.processQueue(), delay);
      return;
    }

    this.isProcessing = true;
    const request = this.queue.shift()!;

    try {
      const result = await this.executeRequest(request);
      request.resolve(result);
    } catch (error) {
      request.reject(error);
    } finally {
      this.isProcessing = false;
      // Process next request
      if (this.queue.length > 0) {
        setTimeout(() => this.processQueue(), 100);
      }
    }
  }

  /**
   * Execute a single request with retry logic
   */
  private async executeRequest<T>(request: QueuedRequest<T>): Promise<T> {
    const { execute, options } = request;

    while (request.attempts <= (options.maxRetries ?? this.defaultOptions.maxRetries)) {
      try {
        request.attempts++;
        const result = await execute();
        // Reset rate limit time on success
        this.rateLimitResetTime = null;
        return result;
      } catch (error) {
        const axiosError = error as AxiosError;

        // Check if we should retry
        if (request.attempts > (options.maxRetries ?? this.defaultOptions.maxRetries) || !(options.shouldRetry ?? this.defaultOptions.shouldRetry)(axiosError)) {
          throw error;
        }

        // Calculate delay
        const delay = this.calculateDelay(request.attempts, options, axiosError);

        // Handle rate limit specifically
        if (axiosError.response?.status === 429) {
          this.handleRateLimit(axiosError, delay);
        }

        // Call retry callback
        options.onRetry?.(request.attempts, delay, axiosError);

        // Wait before retrying
        await this.sleep(delay);
      }
    }

    throw new Error(`Max retries (${options.maxRetries}) exceeded`);
  }

  /**
   * Calculate delay for next retry using exponential backoff
   */
  private calculateDelay(
    attempt: number,
    options: RetryOptions,
    error: AxiosError
  ): number {
    // Check if server provided retry-after header
    if (error.response?.headers['retry-after']) {
      const retryAfter = parseInt(error.response.headers['retry-after']);
      if (!isNaN(retryAfter)) {
        return retryAfter * 1000; // Convert to milliseconds
      }
    }

    // Check if error response has wait_time
    const errorData = error.response?.data as any;
    if (errorData?.wait_time || errorData?.retry_after) {
      const waitTime = errorData.wait_time || errorData.retry_after;
      return waitTime * 1000; // Convert to milliseconds
    }

    // Calculate exponential backoff
    const baseDelay = (options.initialDelay ?? this.defaultOptions.initialDelay) * Math.pow(options.backoffMultiplier ?? this.defaultOptions.backoffMultiplier, attempt - 1);
    
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.1 * baseDelay;
    
    return Math.min(baseDelay + jitter, options.maxDelay ?? this.defaultOptions.maxDelay);
  }

  /**
   * Handle rate limit response
   */
  private handleRateLimit(error: AxiosError, delay: number) {
    const resetTime = Date.now() + delay;
    
    // Update global rate limit reset time
    if (!this.rateLimitResetTime || resetTime > this.rateLimitResetTime) {
      this.rateLimitResetTime = resetTime;
    }

    // Log rate limit info
    const errorData = error.response?.data as any;
    console.warn('Rate limit hit:', {
      endpoint: error.config?.url,
      retryAfter: delay / 1000,
      message: errorData?.error?.message || 'Rate limit exceeded'
    });
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get current queue size
   */
  getQueueSize(): number {
    return this.queue.length;
  }

  /**
   * Check if currently rate limited
   */
  isRateLimited(): boolean {
    return this.rateLimitResetTime !== null && Date.now() < this.rateLimitResetTime;
  }

  /**
   * Get time until rate limit reset
   */
  getTimeUntilReset(): number | null {
    if (!this.rateLimitResetTime) return null;
    const remaining = this.rateLimitResetTime - Date.now();
    return remaining > 0 ? remaining : null;
  }

  /**
   * Clear the request queue
   */
  clearQueue() {
    this.queue.forEach(request => {
      request.reject(new Error('Request queue cleared'));
    });
    this.queue = [];
  }
}

// Create singleton instance
export const retryManager = new RetryManager();

// Export for testing
export { RetryManager };
export type { RetryOptions };