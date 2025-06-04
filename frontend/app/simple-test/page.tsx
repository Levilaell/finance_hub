'use client';

import { useEffect, useState } from 'react';

export default function SimpleTest() {
  const [storageData, setStorageData] = useState<{
    localStorage: Record<string, any>;
    sessionStorage: Record<string, any>;
    cookies: string;
  }>({
    localStorage: {},
    sessionStorage: {},
    cookies: ''
  });

  const [apiTestResult, setApiTestResult] = useState<{
    status: string;
    headers: Record<string, string>;
    error?: string;
  } | null>(null);

  useEffect(() => {
    // Verificar localStorage
    const localStorageData: Record<string, any> = {};
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        try {
          const value = localStorage.getItem(key);
          localStorageData[key] = value ? JSON.parse(value) : value;
        } catch {
          localStorageData[key] = localStorage.getItem(key);
        }
      }
    }

    // Verificar sessionStorage
    const sessionStorageData: Record<string, any> = {};
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key) {
        try {
          const value = sessionStorage.getItem(key);
          sessionStorageData[key] = value ? JSON.parse(value) : value;
        } catch {
          sessionStorageData[key] = sessionStorage.getItem(key);
        }
      }
    }

    setStorageData({
      localStorage: localStorageData,
      sessionStorage: sessionStorageData,
      cookies: document.cookie
    });
  }, []);

  const testAPICall = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'include'
      });

      const headers: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        headers[key] = value;
      });

      setApiTestResult({
        status: `${response.status} ${response.statusText}`,
        headers: headers,
        error: response.ok ? undefined : await response.text()
      });
    } catch (error) {
      setApiTestResult({
        status: 'Error',
        headers: {},
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  const clearStorage = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f3f4f6',
      padding: '2rem',
      fontFamily: 'monospace'
    }}>
      <h1 style={{ 
        fontSize: '2rem', 
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: '2rem'
      }}>
        Authentication Storage Diagnostic
      </h1>

      {/* LocalStorage */}
      <div style={{
        backgroundColor: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          LocalStorage ({Object.keys(storageData.localStorage).length} items)
        </h2>
        <pre style={{ 
          backgroundColor: '#f3f4f6', 
          padding: '1rem', 
          borderRadius: '0.25rem',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(storageData.localStorage, null, 2)}
        </pre>
      </div>

      {/* SessionStorage */}
      <div style={{
        backgroundColor: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          SessionStorage ({Object.keys(storageData.sessionStorage).length} items)
        </h2>
        <pre style={{ 
          backgroundColor: '#f3f4f6', 
          padding: '1rem', 
          borderRadius: '0.25rem',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(storageData.sessionStorage, null, 2)}
        </pre>
      </div>

      {/* Cookies */}
      <div style={{
        backgroundColor: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Cookies
        </h2>
        <pre style={{ 
          backgroundColor: '#f3f4f6', 
          padding: '1rem', 
          borderRadius: '0.25rem',
          overflow: 'auto'
        }}>
          {storageData.cookies || 'No cookies found'}
        </pre>
      </div>

      {/* API Test */}
      <div style={{
        backgroundColor: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          API Authentication Test
        </h2>
        <button 
          onClick={testAPICall}
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer',
            marginBottom: '1rem'
          }}
        >
          Test API Call (/api/auth/me)
        </button>
        
        {apiTestResult && (
          <div>
            <p><strong>Status:</strong> {apiTestResult.status}</p>
            <p><strong>Response Headers:</strong></p>
            <pre style={{ 
              backgroundColor: '#f3f4f6', 
              padding: '1rem', 
              borderRadius: '0.25rem',
              overflow: 'auto',
              maxHeight: '200px'
            }}>
              {JSON.stringify(apiTestResult.headers, null, 2)}
            </pre>
            {apiTestResult.error && (
              <>
                <p><strong>Error:</strong></p>
                <pre style={{ 
                  backgroundColor: '#fee2e2', 
                  padding: '1rem', 
                  borderRadius: '0.25rem',
                  overflow: 'auto'
                }}>
                  {apiTestResult.error}
                </pre>
              </>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ marginTop: '2rem' }}>
        <button 
          onClick={clearStorage}
          style={{
            backgroundColor: '#ef4444',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer',
            marginRight: '1rem'
          }}
        >
          Clear All Storage
        </button>
        <button 
          onClick={() => window.location.reload()}
          style={{
            backgroundColor: '#6b7280',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          Refresh Page
        </button>
      </div>
    </div>
  )
}