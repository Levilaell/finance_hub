"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

export const FinalCTASection = () => {
  return (
    <section className="py-24 bg-gradient-to-br from-primary/20 via-background to-background relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,_rgba(74,170,123,0.1)_0%,_transparent_50%)]" />
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto space-y-8"
        >
          <h2 className="text-5xl lg:text-6xl font-bold leading-tight">
            Pare de perder tempo com <span className="text-primary">planilhas</span>
          </h2>
          
          <p className="text-2xl text-muted-foreground">
            Tenha clareza total do seu caixa em 5 minutos
          </p>

          <div className="pt-4">
            <Button
              size="lg"
              className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg md:text-xl px-8 md:px-12 py-6 md:py-7 h-auto shadow-[0_0_40px_rgba(57,224,142,0.4)] hover:shadow-[0_0_50px_rgba(57,224,142,0.6)] transition-all duration-300"
              asChild
            >
              <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                Começar Agora - 7 Dias Grátis
              </a>
            </Button>
          </div>

          <p className="text-sm text-muted-foreground">
            Configure em 5 minutos. Tenha clareza para sempre.
          </p>
        </motion.div>
      </div>
    </section>
  );
};
