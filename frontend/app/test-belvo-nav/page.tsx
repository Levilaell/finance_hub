'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowRight, Code, Smartphone, Info } from 'lucide-react';

export default function TestBelvoNavPage() {
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Testes de Integração Belvo</h1>

      {/* Overview */}
      <Card className="p-6 mb-6 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h2 className="text-lg font-semibold mb-2">Visão Geral</h2>
            <p className="text-sm mb-3">
              Escolha entre duas formas de testar a integração com o Belvo:
            </p>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li><strong>API Direta:</strong> Testa chamadas diretas à API do Belvo</li>
              <li><strong>Widget Belvo:</strong> Testa o fluxo completo com interface do usuário</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Test Options */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Direct API Test */}
        <Card className="p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Code className="h-6 w-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold mb-2">Teste via API Direta</h3>
              <p className="text-sm text-gray-600 mb-4">
                Teste as chamadas diretas à API do Belvo, ideal para debugging e 
                entender o fluxo de dados.
              </p>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Funcionalidades:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Listar instituições bancárias</li>
                  <li>Criar conexão com credenciais</li>
                  <li>Sincronizar dados bancários</li>
                  <li>Visualizar resultado detalhado</li>
                </ul>
              </div>
            </div>
          </div>
          <Link href="/test-belvo">
            <Button className="w-full">
              Testar API Direta
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </Card>

        {/* Widget Test */}
        <Card className="p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <Smartphone className="h-6 w-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold mb-2">Teste via Widget</h3>
              <p className="text-sm text-gray-600 mb-4">
                Teste o widget oficial do Belvo, simulando a experiência real 
                do usuário final.
              </p>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Funcionalidades:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Interface oficial do Belvo</li>
                  <li>Seleção visual de bancos</li>
                  <li>Fluxo de autenticação completo</li>
                  <li>Sincronização automática</li>
                </ul>
              </div>
            </div>
          </div>
          <Link href="/test-belvo-widget">
            <Button className="w-full" variant="outline">
              Testar Widget
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </Card>
      </div>

      {/* Sandbox Credentials */}
      <Card className="p-6 mt-6 bg-gray-50">
        <h2 className="text-lg font-semibold mb-4">Credenciais Sandbox</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="font-medium mb-2 text-sm">Conta Completa</h3>
            <div className="bg-white p-3 rounded border font-mono text-sm">
              <p>Username: bnk100</p>
              <p>Password: full</p>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Acesso completo a todas as funcionalidades
            </p>
          </div>
          <div>
            <h3 className="font-medium mb-2 text-sm">Conta Limitada</h3>
            <div className="bg-white p-3 rounded border font-mono text-sm">
              <p>Username: bnk100</p>
              <p>Password: limited</p>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Acesso limitado para testes específicos
            </p>
          </div>
        </div>
      </Card>

      {/* Additional Info */}
      <Card className="p-6 mt-6">
        <h2 className="text-lg font-semibold mb-3">Informações Importantes</h2>
        <ul className="space-y-2 text-sm">
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-0.5">•</span>
            <span>
              Todos os testes usam o ambiente <strong>sandbox</strong> do Belvo, 
              sem afetar dados reais
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-0.5">•</span>
            <span>
              As instituições sandbox simulam o comportamento de bancos reais
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-0.5">•</span>
            <span>
              Os dados retornados são fictícios mas seguem o formato real
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500 mt-0.5">•</span>
            <span>
              Ideal para desenvolvimento e testes sem custos adicionais
            </span>
          </li>
        </ul>
      </Card>
    </div>
  );
}