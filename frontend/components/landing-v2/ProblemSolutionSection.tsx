"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { X, Check } from "lucide-react";

export const ProblemSolutionSection = () => {
  const problems = [
    "Vendas entram em 3 bancos diferentes, tudo desorganizado",
    "Não sabe se o mês fechou no positivo ou negativo",
    "Gastos pequenos somam e você só descobre no fim do mês",
    "Passa horas no sábado tentando fechar o caixa",
  ];

  const solutions = [
    "Todas as contas consolidadas em um painel",
    "Vê entrada vs saída em tempo real",
    "IA categoriza e mostra onde está vazando dinheiro",
    "Relatório pronto em 2 cliques",
  ];

  return (
    <section className="py-24 bg-background relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-muted/10 to-background" />
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-4">
            Você está <span className="text-destructive">perdendo dinheiro</span> sem perceber
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto mb-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Card className="p-8 bg-card border-destructive/20 h-full">
              <h3 className="text-2xl font-bold mb-6 text-destructive">Sem o CaixaHub:</h3>
              <div className="space-y-4">
                {problems.map((problem, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <X className="w-5 h-5 text-destructive flex-shrink-0 mt-1" />
                    <p className="text-foreground/80">{problem}</p>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <Card className="p-8 bg-card border-success/20 h-full">
              <h3 className="text-2xl font-bold mb-6 text-success">Com o CaixaHub:</h3>
              <div className="space-y-4">
                {solutions.map((solution, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-success flex-shrink-0 mt-1" />
                    <p className="text-foreground/80">{solution}</p>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-center"
        >
          <Button
            size="lg"
            className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(74,170,123,0.3)] hover:shadow-[0_0_40px_rgba(74,170,123,0.5)] transition-all duration-300"
            asChild
          >
            <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
              Quero clareza do meu caixa
            </a>
          </Button>
        </motion.div>
      </div>
    </section>
  );
};
