"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Quote } from "lucide-react";

export const TestimonialsSection = () => {
  const testimonials = [
    {
      quote: "Antes eu passava todo sábado fechando caixa na planilha. Agora o CaixaHub mostra tudo em tempo real. Recuperei meus finais de semana.",
      name: "Mariana Silva",
      role: "Dona da Boutique Estilo, São Paulo",
      initials: "MS",
    },
    {
      quote: "Descobri que estava pagando uma assinatura esquecida de R$ 79/mês há 8 meses. O CaixaHub me mostrou na primeira semana. Já pagou o sistema.",
      name: "Carlos Eduardo",
      role: "Dono da Loja de Eletrônicos Tech House",
      initials: "CE",
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
          className="text-center mb-16"
        >
          <h2 className="text-4xl lg:text-5xl font-bold">
            Lojistas que recuperaram seu tempo
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
            >
              <Card className="p-8 bg-card border-border/50 h-full relative">
                <Quote className="absolute top-6 right-6 w-12 h-12 text-primary/30" />
                
                <div className="relative z-10">
                  <p className="text-lg text-foreground/90 mb-8 leading-relaxed italic">
                    "{testimonial.quote}"
                  </p>
                  
                  <div className="flex items-center gap-4">
                    <Avatar className="w-14 h-14 border-2 border-primary/20">
                      <AvatarFallback className="bg-primary/10 text-primary font-bold text-lg">
                        {testimonial.initials}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-bold text-foreground">{testimonial.name}</p>
                      <p className="text-sm text-muted-foreground">{testimonial.role}</p>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
