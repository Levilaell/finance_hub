"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Check, Sparkles } from "lucide-react";

// Price ID padrão de R$197
const PRICE_ID_197 = process.env.NEXT_PUBLIC_PRICE_197 || "price_1SXwA6AhSWJIUR4PV1BYoKLt";

export const PricingSection = () => {
  const features = [
    "Conexão ilimitada com bancos via Open Banking",
    "Categorização automática por IA",
    "Dashboard financeiro em tempo real",
    "Relatórios detalhados (PDF e Excel)",
    "Múltiplas contas em um só lugar",
    "Suporte via WhatsApp",
    "Sincronização automática 24/7",
    "Categorias personalizadas",
    "Insights inteligentes",
    "Exportação para contador",
  ];

  return (
    <section id="pricing" className="py-24 bg-background relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-muted/10 to-background" />
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <Card className="p-10 lg:p-14 bg-card border-primary/30 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl" />
            
            <div className="relative z-10">
              <div className="text-center mb-10">
                <div className="inline-block px-4 py-2 bg-primary/10 text-primary text-sm font-bold rounded-full mb-4">
                  Plano Pro
                </div>
                <h2 className="text-3xl lg:text-4xl font-bold mb-3">Acesso completo à plataforma</h2>
                <div className="flex items-baseline justify-center gap-2 mb-2">
                  <span className="text-6xl lg:text-7xl font-bold text-primary">R$ 197</span>
                  <span className="text-2xl text-muted-foreground">/mês</span>
                </div>
                <p className="text-muted-foreground">Cobrado mensalmente</p>
              </div>

              <div className="mb-8">
                <h3 className="text-xl font-bold mb-6 text-center">Tudo que está incluído:</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {features.map((feature, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.05 }}
                      className="flex items-start gap-3"
                    >
                      <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                      <p className="text-foreground/80">{feature}</p>
                    </motion.div>
                  ))}
                </div>
              </div>

              <Card className="p-6 bg-primary/10 border-primary/20 mb-8">
                <div className="flex items-center justify-center gap-3 mb-2">
                  <Sparkles className="w-6 h-6 text-primary" />
                  <p className="text-xl font-bold text-primary">7 dias de trial grátis para testar</p>
                </div>
                <p className="text-center text-muted-foreground">Cancele a qualquer momento</p>
              </Card>

              <div className="text-center space-y-4">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground text-xl px-12 py-7 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300 w-full md:w-auto"
                  asChild
                >
                  <a href={`/register?price_id=${PRICE_ID_197}`}>
                    Começar Trial de 7 Dias
                  </a>
                </Button>
                <p className="text-sm text-muted-foreground">
                  Menos que 1 hora do seu tempo vale. E economiza 5h/semana.
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </section>
  );
};
