/**
 * Browser Detection Utilities for Authentication Method Selection
 * Specifically handles mobile Safari cookie issues
 */

/**
 * Detect if current browser is mobile Safari (iPhone/iPad Safari)
 */
export function isMobileSafari(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  const userAgent = navigator.userAgent;
  
  // iPhone Safari detection
  const isIPhoneSafari = /iPhone.*Safari/.test(userAgent) && 
                         !/CriOS/.test(userAgent) && // Not Chrome iOS
                         !/FxiOS/.test(userAgent) && // Not Firefox iOS  
                         !/EdgiOS/.test(userAgent);  // Not Edge iOS
  
  // iPad Safari detection  
  const isIPadSafari = /iPad.*Safari/.test(userAgent) &&
                       !/CriOS/.test(userAgent) &&
                       !/FxiOS/.test(userAgent) &&
                       !/EdgiOS/.test(userAgent);

  return isIPhoneSafari || isIPadSafari;
}

/**
 * Check if browser requires localStorage authentication fallback
 * Currently only mobile Safari due to strict cookie handling
 */
export function requiresLocalStorageAuth(): boolean {
  return isMobileSafari();
}

/**
 * Get browser authentication method preference
 */
export function getAuthMethod(): 'cookies' | 'localStorage' {
  return requiresLocalStorageAuth() ? 'localStorage' : 'cookies';
}

/**
 * Log browser detection info for debugging
 */
export function logBrowserInfo(): void {
  if (typeof window === 'undefined') {
    return;
  }

  const userAgent = navigator.userAgent;
  const authMethod = getAuthMethod();
  const isMobile = isMobileSafari();
  
  console.log('[Browser Detection]', {
    userAgent: userAgent.substring(0, 100) + '...',
    isMobileSafari: isMobile,
    authMethod,
    requiresLocalStorageAuth: requiresLocalStorageAuth()
  });
}

/**
 * Check if current environment supports cookies
 * Test by setting and reading a test cookie
 */
export function testCookieSupport(): boolean {
  if (typeof document === 'undefined') {
    return false;
  }

  try {
    const testName = 'cookie_test_' + Date.now();
    const testValue = 'test';
    
    // Set test cookie
    document.cookie = `${testName}=${testValue}; path=/; SameSite=None; Secure`;
    
    // Read test cookie
    const cookieSupported = document.cookie.includes(`${testName}=${testValue}`);
    
    // Clean up test cookie
    document.cookie = `${testName}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
    
    return cookieSupported;
  } catch (error) {
    console.warn('[Cookie Test] Failed:', error);
    return false;
  }
}