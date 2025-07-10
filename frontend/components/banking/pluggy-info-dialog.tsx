'use client';

import { InformationCircleIcon } from '@heroicons/react/24/outline';

export function PluggyInfoDialog() {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex gap-3">
        <InformationCircleIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-blue-900">
          <strong>Como funciona a conexão segura:</strong>
          <ol className="mt-2 ml-4 list-decimal space-y-1 text-sm">
            <li>Você será redirecionado para o Pluggy Connect</li>
            <li>Escolha seu banco e faça login com suas credenciais bancárias</li>
            <li>O Pluggy conecta de forma segura e busca suas contas automaticamente</li>
            <li>Suas transações serão sincronizadas periodicamente</li>
          </ol>
          <p className="mt-3 text-xs">
            🔒 Suas credenciais são processadas diretamente pelo Pluggy e pelo banco. 
            Não armazenamos suas senhas.
          </p>
        </div>
      </div>
    </div>
  );
}