'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  SparklesIcon,
  BeakerIcon,
  GlobeAltIcon,
  CogIcon,
  ArrowRightIcon,
  ChartBarIcon,
  LightBulbIcon,
  TrophyIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline';

interface FeatureShowcaseProps {
  onFeatureClick: (feature: string) => void;
  hasInsights: boolean;
  hasContext: boolean;
}

export function FeatureShowcase({ onFeatureClick, hasInsights, hasContext }: FeatureShowcaseProps) {
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  const features = [
    {
      id: 'simulator',
      title: 'Simulador de Cenários',
      icon: BeakerIcon,
      color: 'purple',
      description: 'Teste "e se..." e veja o impacto futuro',
      benefits: [
        'Projeções de 12 meses',
        'Cenários pré-definidos',
        'Gráficos interativos'
      ],
      cta: 'Simular Agora',
      badge: 'NOVO',
      badgeColor: 'bg-purple-500',
      locked: !hasInsights,
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      id: 'benchmarking',
      title: 'Benchmarking Inteligente',
      icon: GlobeAltIcon,
      color: 'blue',
      description: 'Compare com líderes do seu setor',
      benefits: [
        'Dados de 5 setores',
        'Ranking competitivo',
        'Melhores práticas'
      ],
      cta: 'Comparar',
      badge: 'EXCLUSIVO',
      badgeColor: 'bg-blue-500',
      locked: !hasInsights,
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'context',
      title: 'IA Personalizada',
      icon: CogIcon,
      color: 'green',
      description: 'Configure para análises precisas',
      benefits: [
        'Metas personalizadas',
        'Contexto do negócio',
        'Perguntas diretas'
      ],
      cta: hasContext ? 'Atualizar' : 'Configurar',
      badge: hasContext ? 'ATIVO' : 'CONFIGURE',
      badgeColor: hasContext ? 'bg-green-500' : 'bg-yellow-500',
      locked: false,
      gradient: 'from-green-500 to-emerald-500'
    }
  ];

  return (
    <div className="mb-8">
      {/* Hero Section */}
      <div className="relative mb-8 p-8 rounded-2xl bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-0 right-0 w-60 h-60 bg-purple-300 rounded-full blur-3xl animate-pulse delay-700" />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <RocketLaunchIcon className="h-10 w-10" />
            <h2 className="text-3xl font-bold">
              Ferramentas Premium de IA
            </h2>
            <Badge className="bg-white text-purple-600 hover:bg-white">
              3 FERRAMENTAS
            </Badge>
          </div>
          <p className="text-lg opacity-90 mb-6 max-w-3xl">
            Desbloqueie o poder total da inteligência artificial para transformar seus dados em decisões lucrativas
          </p>
          
          <div className="grid md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5" />
              <span>Aumente lucros em até 30%</span>
            </div>
            <div className="flex items-center gap-2">
              <LightBulbIcon className="h-5 w-5" />
              <span>Decisões baseadas em dados</span>
            </div>
            <div className="flex items-center gap-2">
              <TrophyIcon className="h-5 w-5" />
              <span>Supere a concorrência</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          const isHovered = hoveredFeature === feature.id;
          
          return (
            <Card
              key={feature.id}
              className={cn(
                "relative overflow-hidden transition-all duration-300 cursor-pointer",
                "border-2 hover:border-opacity-100",
                isHovered ? "transform scale-105 shadow-2xl" : "hover:shadow-xl",
                feature.locked && "opacity-75"
              )}
              style={{
                borderColor: isHovered ? `rgb(147 51 234)` : 'rgb(229 231 235)'
              }}
              onMouseEnter={() => setHoveredFeature(feature.id)}
              onMouseLeave={() => setHoveredFeature(null)}
              onClick={() => !feature.locked && onFeatureClick(feature.id)}
            >
              {/* Badge */}
              <div className={cn(
                "absolute top-0 right-0 px-3 py-1 text-xs font-bold text-white rounded-bl-lg",
                feature.badgeColor
              )}>
                {feature.badge}
              </div>

              {/* Background Gradient */}
              <div 
                className={cn(
                  "absolute inset-0 opacity-5 bg-gradient-to-br",
                  feature.gradient
                )}
              />

              {/* Content */}
              <div className="relative p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "p-3 rounded-xl bg-gradient-to-br text-white",
                    feature.gradient
                  )}>
                    <Icon className="h-8 w-8" />
                  </div>
                  {feature.locked && (
                    <Badge variant="outline" className="bg-yellow-50">
                      🔒 Gere análise primeiro
                    </Badge>
                  )}
                </div>

                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600 mb-4">{feature.description}</p>

                <div className="space-y-2 mb-6">
                  {feature.benefits.map((benefit, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <div className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        feature.color === 'purple' && "bg-purple-500",
                        feature.color === 'blue' && "bg-blue-500",
                        feature.color === 'green' && "bg-green-500"
                      )} />
                      <span className="text-gray-700">{benefit}</span>
                    </div>
                  ))}
                </div>

                <Button
                  className={cn(
                    "w-full group bg-gradient-to-r text-white font-semibold",
                    feature.gradient,
                    feature.locked && "opacity-50 cursor-not-allowed"
                  )}
                  disabled={feature.locked}
                >
                  {feature.cta}
                  <ArrowRightIcon className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>

              {/* Hover Effect */}
              {isHovered && !feature.locked && (
                <div className="absolute inset-0 pointer-events-none">
                  <div className={cn(
                    "absolute inset-0 opacity-10 bg-gradient-to-br animate-pulse",
                    feature.gradient
                  )} />
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* CTA Section */}
      {!hasInsights && (
        <div className="mt-8 p-6 bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-200 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-1">
                🎯 Comece agora mesmo!
              </h3>
              <p className="text-gray-600">
                Gere sua primeira análise com IA para desbloquear todas as ferramentas premium
              </p>
            </div>
            <Button 
              size="lg" 
              className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white"
            >
              Gerar Análise
              <SparklesIcon className="h-5 w-5 ml-2" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}