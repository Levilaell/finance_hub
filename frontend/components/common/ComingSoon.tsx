import React from 'react';
import { Lock, Sparkles, Clock, Bell } from 'lucide-react';

interface ComingSoonProps {
  title?: string;
  description?: string;
  features?: string[];
  expectedDate?: string;
}

export default function ComingSoon({
  title = "Insights com IA",
  description = "Nossa inteligência artificial está em desenvolvimento para oferecer insights poderosos sobre suas finanças.",
  features = [
    "Análise preditiva de gastos",
    "Recomendações personalizadas de economia",
    "Alertas inteligentes de anomalias",
    "Relatórios automáticos com insights"
  ],
  expectedDate = "Em breve"
}: ComingSoonProps) {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-100 to-indigo-100 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-full mb-6">
            <Lock className="w-10 h-10 text-purple-600 dark:text-purple-400" />
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {title}
          </h1>
          
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 rounded-full text-sm font-medium mb-6">
            <Clock className="w-4 h-4" />
            <span>{expectedDate}</span>
          </div>
          
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-lg mx-auto">
            {description}
          </p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800 rounded-xl p-8 border border-purple-200 dark:border-purple-900">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              O que está por vir
            </h2>
          </div>
          
          <ul className="space-y-3">
            {features.map((feature, index) => (
              <li key={index} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-200 dark:bg-purple-900/50 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">
                    {index + 1}
                  </span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">
                  {feature}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-900">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-1">
                Seja o primeiro a saber!
              </p>
              <p className="text-sm text-blue-700 dark:text-blue-400">
                Você será notificado assim que esta funcionalidade estiver disponível em seu plano.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}