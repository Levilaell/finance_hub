"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Building2, Bot, LayoutDashboard } from "lucide-react";

export const HowItWorksSection = () => {
  const steps = [
    {
      number: 1,
      icon: Building2,
      title: "Conecte seus bancos",
      description: "Nubank, Itaú, Bradesco, qualquer banco via Open Banking seguro",
      time: "2 minutos",
    },
    {
      number: 2,
      icon: Bot,
      title: "IA organiza tudo",
      description: "Categoriza vendas, fornecedores, impostos, despesas automaticamente",
      time: "2 minutos",
    },
    {
      number: 3,
      icon: LayoutDashboard,
      title: "Veja seu caixa real",
      description: "Dashboard mostra quanto entrou, quanto saiu, quanto tem disponível",
      time: "1 minuto",
    },
  ];

  return (
    <section className="py-24 bg-muted/30 relative overflow-hidden">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-6"
        >
          <h2 className="text-4xl lg:text-5xl font-bold mb-4">Como funciona</h2>
          <p className="text-xl text-muted-foreground">
            De caos financeiro para clareza total em 3 passos
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12 mt-16">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
            >
              <Card className="p-8 bg-card border-border/50 h-full relative overflow-hidden group hover:border-primary/50 transition-all duration-300">
                <div className="absolute top-4 right-4 text-6xl font-bold text-primary/30 group-hover:text-primary/40 transition-colors duration-300">
                  {step.number}
                </div>
                
                <div className="relative z-10">
                  <div className="w-16 h-16 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                    <step.icon className="w-8 h-8 text-primary" />
                  </div>
                  
                  <h3 className="text-2xl font-bold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground mb-4 leading-relaxed">
                    {step.description}
                  </p>
                  <div className="inline-block px-3 py-1 bg-primary/10 text-primary text-sm font-medium rounded-full">
                    {step.time}
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="text-center space-y-6"
        >
          <p className="text-xl text-muted-foreground font-medium">
            Total: <span className="text-primary">5 minutos de configuração</span>
          </p>
          <Button
            size="lg"
            className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(74,170,123,0.3)] hover:shadow-[0_0_40px_rgba(74,170,123,0.5)] transition-all duration-300"
            asChild
          >
            <a href="/register">
              Começar agora - 7 dias grátis
            </a>
          </Button>
        </motion.div>
      </div>
    </section>
  );
};
