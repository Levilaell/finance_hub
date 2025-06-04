'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function ClearStoragePage() {
  const clearStorage = () => {
    if (typeof window !== 'undefined') {
      // Clear localStorage
      localStorage.clear();
      
      // Clear cookies
      document.cookie.split(";").forEach((c) => {
        const eqPos = c.indexOf("=");
        const name = eqPos > -1 ? c.substr(0, eqPos) : c;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
      });
      
      alert('Storage cleared! Redirecting to login...');
      window.location.href = '/login';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold mb-4">Clear Storage</h1>
        <p className="text-gray-600 mb-6">
          Esta página limpa todos os dados de autenticação armazenados (localStorage e cookies).
        </p>
        <Button onClick={clearStorage} className="w-full">
          Limpar e Fazer Login Novamente
        </Button>
      </div>
    </div>
  );
}