"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";

export const DemoSection = () => {
  return (
    <section className="py-24 bg-muted/30 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/20 to-background" />
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-6xl mx-auto"
        >
          <div className="text-center mb-12">
            <h2 className="text-4xl lg:text-5xl font-bold mb-6">
              Veja o CaixaHub em Ação
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Descubra como é simples organizar todo o seu caixa em poucos cliques
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative rounded-2xl overflow-hidden border border-border shadow-2xl bg-background group cursor-pointer"
          >
            {/* Video Placeholder */}
            <div className="aspect-video bg-gradient-to-br from-muted via-muted/80 to-muted/60 flex items-center justify-center relative">
              {/* Play Button Overlay */}
              <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center">
                <motion.div
                  whileHover={{ scale: 1.1 }}
                  className="w-20 h-20 rounded-full bg-primary/90 backdrop-blur-sm flex items-center justify-center shadow-[0_0_30px_rgba(57,224,142,0.5)] group-hover:shadow-[0_0_50px_rgba(57,224,142,0.7)] transition-all duration-300"
                >
                  <Play className="w-10 h-10 text-primary-foreground ml-1" fill="currentColor" />
                </motion.div>
              </div>
              
              {/* Placeholder Content */}
              <div className="text-center space-y-4 z-0">
                <div className="text-7xl mb-4">🎬</div>
                <p className="text-muted-foreground text-lg font-medium px-4">
                  Demonstração do Dashboard CaixaHub
                </p>
              </div>
            </div>

            {/* Video frame decoration */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
              <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-center mt-12"
          >
            <p className="text-muted-foreground mb-6 text-lg">
              Pronto para organizar o caixa da sua loja?
            </p>
            <Button
              size="lg"
              className="bg-primary hover:bg-primary/90 text-primary-foreground text-lg px-8 py-6 h-auto shadow-[0_0_30px_rgba(57,224,142,0.3)] hover:shadow-[0_0_40px_rgba(57,224,142,0.5)] transition-all duration-300"
              asChild
            >
              <a href="https://caixahub.com.br/register" target="_blank" rel="noopener noreferrer">
                Começar agora - 7 dias grátis
              </a>
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};
