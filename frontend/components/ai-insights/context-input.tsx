'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import {
  InformationCircleIcon,
  PlusCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
  LightBulbIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface ContextInputProps {
  onContextUpdate: (context: BusinessContext) => void;
  initialContext?: BusinessContext;
}

export interface BusinessContext {
  businessGoals: string[];
  challenges: string[];
  seasonality: string;
  recentChanges: string;
  industry: string;
  businessModel: string;
  targetMarket: string;
  competitiveAdvantage: string;
  customQuestions: string[];
}

const PREDEFINED_GOALS = [
  'Aumentar faturamento em 20%',
  'Reduzir custos operacionais',
  'Expandir para novos mercados',
  'Melhorar margem de lucro',
  'Automatizar processos',
  'Contratar mais funcionários',
  'Lançar novo produto/serviço',
  'Melhorar fluxo de caixa',
];

const PREDEFINED_CHALLENGES = [
  'Alto custo de aquisição de clientes',
  'Concorrência acirrada',
  'Falta de capital de giro',
  'Dificuldade para escalar',
  'Alta rotatividade de funcionários',
  'Dependência de poucos clientes',
  'Sazonalidade nas vendas',
  'Processos manuais ineficientes',
];

const EXAMPLE_QUESTIONS = [
  'Como posso reduzir meu CAC (Custo de Aquisição de Cliente)?',
  'Qual a melhor estratégia para aumentar o ticket médio?',
  'Como otimizar meu fluxo de caixa nos próximos 3 meses?',
  'Devo investir em marketing digital ou tradicional?',
  'Como me preparar para a sazonalidade do fim de ano?',
];

export function ContextInput({ onContextUpdate, initialContext }: ContextInputProps) {
  const [context, setContext] = useState<BusinessContext>(initialContext || {
    businessGoals: [],
    challenges: [],
    seasonality: '',
    recentChanges: '',
    industry: '',
    businessModel: '',
    targetMarket: '',
    competitiveAdvantage: '',
    customQuestions: [],
  });

  const [newGoal, setNewGoal] = useState('');
  const [newChallenge, setNewChallenge] = useState('');
  const [newQuestion, setNewQuestion] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleAddGoal = (goal: string) => {
    if (goal && !context.businessGoals.includes(goal)) {
      const updated = {
        ...context,
        businessGoals: [...context.businessGoals, goal]
      };
      setContext(updated);
      setHasChanges(true);
      setNewGoal('');
    }
  };

  const handleRemoveGoal = (index: number) => {
    const updated = {
      ...context,
      businessGoals: context.businessGoals.filter((_, i) => i !== index)
    };
    setContext(updated);
    setHasChanges(true);
  };

  const handleAddChallenge = (challenge: string) => {
    if (challenge && !context.challenges.includes(challenge)) {
      const updated = {
        ...context,
        challenges: [...context.challenges, challenge]
      };
      setContext(updated);
      setHasChanges(true);
      setNewChallenge('');
    }
  };

  const handleRemoveChallenge = (index: number) => {
    const updated = {
      ...context,
      challenges: context.challenges.filter((_, i) => i !== index)
    };
    setContext(updated);
    setHasChanges(true);
  };

  const handleAddQuestion = (question: string) => {
    if (question && !context.customQuestions.includes(question)) {
      const updated = {
        ...context,
        customQuestions: [...context.customQuestions, question]
      };
      setContext(updated);
      setHasChanges(true);
      setNewQuestion('');
    }
  };

  const handleRemoveQuestion = (index: number) => {
    const updated = {
      ...context,
      customQuestions: context.customQuestions.filter((_, i) => i !== index)
    };
    setContext(updated);
    setHasChanges(true);
  };

  const handleSubmit = () => {
    onContextUpdate(context);
    setHasChanges(false);
  };

  const isContextComplete = () => {
    return context.businessGoals.length > 0 || 
           context.challenges.length > 0 || 
           context.industry || 
           context.businessModel ||
           context.recentChanges ||
           context.customQuestions.length > 0;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <DocumentTextIcon className="h-5 w-5 text-purple-600" />
            Contexto do Negócio
          </div>
          {isContextComplete() && (
            <Badge variant="default" className="bg-green-600">
              <CheckCircleIcon className="h-3 w-3 mr-1" />
              Contexto Configurado
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          Forneça informações sobre seu negócio para receber análises mais precisas e personalizadas
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Informações Básicas */}
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Setor/Indústria</Label>
            <Select 
              value={context.industry} 
              onValueChange={(value) => {
                setContext({ ...context, industry: value });
                setHasChanges(true);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o setor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="technology">Tecnologia</SelectItem>
                <SelectItem value="retail">Varejo</SelectItem>
                <SelectItem value="services">Serviços</SelectItem>
                <SelectItem value="manufacturing">Indústria</SelectItem>
                <SelectItem value="food">Alimentação</SelectItem>
                <SelectItem value="health">Saúde</SelectItem>
                <SelectItem value="education">Educação</SelectItem>
                <SelectItem value="finance">Finanças</SelectItem>
                <SelectItem value="other">Outro</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Modelo de Negócio</Label>
            <Select 
              value={context.businessModel} 
              onValueChange={(value) => {
                setContext({ ...context, businessModel: value });
                setHasChanges(true);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione o modelo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="b2b">B2B</SelectItem>
                <SelectItem value="b2c">B2C</SelectItem>
                <SelectItem value="b2b2c">B2B2C</SelectItem>
                <SelectItem value="marketplace">Marketplace</SelectItem>
                <SelectItem value="saas">SaaS</SelectItem>
                <SelectItem value="ecommerce">E-commerce</SelectItem>
                <SelectItem value="subscription">Assinatura</SelectItem>
                <SelectItem value="hybrid">Híbrido</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Metas do Negócio */}
        <div>
          <Label className="mb-2 block">
            Metas e Objetivos
            <span className="text-xs text-gray-500 ml-2">
              O que você quer alcançar?
            </span>
          </Label>
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Ex: Aumentar faturamento em 30%"
                value={newGoal}
                onChange={(e) => setNewGoal(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddGoal(newGoal);
                  }
                }}
              />
              <Button
                size="sm"
                onClick={() => handleAddGoal(newGoal)}
                disabled={!newGoal}
              >
                <PlusCircleIcon className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Sugestões de metas */}
            <div className="flex flex-wrap gap-2">
              {PREDEFINED_GOALS.filter(g => !context.businessGoals.includes(g)).slice(0, 4).map((goal) => (
                <Button
                  key={goal}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleAddGoal(goal)}
                >
                  <PlusCircleIcon className="h-3 w-3 mr-1" />
                  {goal}
                </Button>
              ))}
            </div>

            {/* Metas adicionadas */}
            {context.businessGoals.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {context.businessGoals.map((goal, index) => (
                  <Badge key={index} variant="secondary" className="pl-2">
                    {goal}
                    <button
                      onClick={() => handleRemoveGoal(index)}
                      className="ml-2 hover:text-red-600"
                    >
                      <XCircleIcon className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Desafios */}
        <div>
          <Label className="mb-2 block">
            Principais Desafios
            <span className="text-xs text-gray-500 ml-2">
              Quais são suas dificuldades?
            </span>
          </Label>
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Ex: Alto custo de aquisição de clientes"
                value={newChallenge}
                onChange={(e) => setNewChallenge(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddChallenge(newChallenge);
                  }
                }}
              />
              <Button
                size="sm"
                onClick={() => handleAddChallenge(newChallenge)}
                disabled={!newChallenge}
              >
                <PlusCircleIcon className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Sugestões de desafios */}
            <div className="flex flex-wrap gap-2">
              {PREDEFINED_CHALLENGES.filter(c => !context.challenges.includes(c)).slice(0, 4).map((challenge) => (
                <Button
                  key={challenge}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleAddChallenge(challenge)}
                >
                  <PlusCircleIcon className="h-3 w-3 mr-1" />
                  {challenge}
                </Button>
              ))}
            </div>

            {/* Desafios adicionados */}
            {context.challenges.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {context.challenges.map((challenge, index) => (
                  <Badge key={index} variant="secondary" className="pl-2">
                    {challenge}
                    <button
                      onClick={() => handleRemoveChallenge(index)}
                      className="ml-2 hover:text-red-600"
                    >
                      <XCircleIcon className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Informações Adicionais */}
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Sazonalidade</Label>
            <Input
              placeholder="Ex: Vendas aumentam 40% no fim de ano"
              value={context.seasonality}
              onChange={(e) => {
                setContext({ ...context, seasonality: e.target.value });
                setHasChanges(true);
              }}
            />
          </div>

          <div>
            <Label>Público-alvo</Label>
            <Input
              placeholder="Ex: PMEs do setor de tecnologia"
              value={context.targetMarket}
              onChange={(e) => {
                setContext({ ...context, targetMarket: e.target.value });
                setHasChanges(true);
              }}
            />
          </div>
        </div>

        {/* Mudanças Recentes */}
        <div>
          <Label>Mudanças Recentes ou Eventos Importantes</Label>
          <Textarea
            placeholder="Ex: Lançamos novo produto em outubro, contratamos 3 vendedores, mudamos de escritório..."
            value={context.recentChanges}
            onChange={(e) => {
              setContext({ ...context, recentChanges: e.target.value });
              setHasChanges(true);
            }}
            rows={3}
          />
        </div>

        {/* Vantagem Competitiva */}
        <div>
          <Label>Diferencial Competitivo</Label>
          <Textarea
            placeholder="Ex: Somos a única empresa da região com entrega em 2 horas..."
            value={context.competitiveAdvantage}
            onChange={(e) => {
              setContext({ ...context, competitiveAdvantage: e.target.value });
              setHasChanges(true);
            }}
            rows={2}
          />
        </div>

        {/* Perguntas Específicas */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label>
              Perguntas Específicas para a IA
              <span className="text-xs text-gray-500 ml-2">
                O que você gostaria de saber?
              </span>
            </Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowExamples(!showExamples)}
            >
              <LightBulbIcon className="h-4 w-4 mr-1" />
              {showExamples ? 'Ocultar' : 'Ver'} Exemplos
            </Button>
          </div>
          
          {showExamples && (
            <div className="mb-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium mb-2">Exemplos de perguntas:</p>
              <div className="space-y-1">
                {EXAMPLE_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    className="block text-left text-sm text-blue-700 hover:underline"
                    onClick={() => handleAddQuestion(question)}
                  >
                    • {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Ex: Como posso melhorar minha margem de lucro?"
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddQuestion(newQuestion);
                  }
                }}
              />
              <Button
                size="sm"
                onClick={() => handleAddQuestion(newQuestion)}
                disabled={!newQuestion}
              >
                <PlusCircleIcon className="h-4 w-4" />
              </Button>
            </div>

            {/* Perguntas adicionadas */}
            {context.customQuestions.length > 0 && (
              <div className="space-y-2 mt-2">
                {context.customQuestions.map((question, index) => (
                  <div key={index} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                    <span className="text-sm flex-1">{question}</span>
                    <button
                      onClick={() => handleRemoveQuestion(index)}
                      className="text-gray-400 hover:text-red-600"
                    >
                      <XCircleIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Botão de Salvar */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <InformationCircleIcon className="h-4 w-4" />
            <span>
              Quanto mais contexto você fornecer, mais precisas serão as análises
            </span>
          </div>
          
          <Button
            onClick={handleSubmit}
            disabled={!hasChanges || !isContextComplete()}
            className={cn(
              "transition-all",
              hasChanges && isContextComplete() && "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            )}
          >
            <SparklesIcon className="h-4 w-4 mr-2" />
            {hasChanges ? 'Salvar Contexto' : 'Contexto Salvo'}
          </Button>
        </div>

        {/* Dialog de Confirmação */}
        {hasChanges && isContextComplete() && (
          <Dialog>
            <DialogTrigger asChild>
              <div className="hidden" />
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Contexto Atualizado!</DialogTitle>
                <DialogDescription>
                  Suas informações foram salvas. A IA agora utilizará este contexto para gerar análises mais precisas e personalizadas para o seu negócio.
                </DialogDescription>
              </DialogHeader>
              <div className="mt-4">
                <Button onClick={() => setHasChanges(false)} className="w-full">
                  Entendido
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </CardContent>
    </Card>
  );
}