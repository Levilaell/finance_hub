"use client";

import { motion } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const FAQSection = () => {
  const faqs = [
    {
      question: "Funciona para loja física?",
      answer: "Sim. Conecta todas as suas contas (banco da loja, maquininhas, Pix) e consolida tudo em um lugar.",
    },
    {
      question: "É seguro conectar minha conta?",
      answer: "Totalmente. Usamos Open Banking certificado pelo Banco Central. Não armazenamos suas senhas. Mesma tecnologia usada por Nubank e outros bancos digitais.",
    },
    {
      question: "Funciona com maquininha de cartão?",
      answer: "Sim, se sua maquininha deposita em conta bancária. Conecte a conta e o CaixaHub categoriza automaticamente as vendas.",
    },
    {
      question: "Preciso saber de tecnologia?",
      answer: "Não. Se você usa WhatsApp, consegue usar o CaixaHub. É intuitivo e simples.",
    },
    {
      question: "Substitui meu contador?",
      answer: "Não, mas facilita muito o trabalho dele. Você exporta tudo organizado e envia. Ele vai adorar receber os dados assim.",
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
          <h2 className="text-4xl lg:text-5xl font-bold">Perguntas frequentes</h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto"
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="bg-card border border-border/50 rounded-lg px-6 data-[state=open]:border-primary/50 transition-colors duration-300"
              >
                <AccordionTrigger className="text-left text-lg font-semibold hover:text-primary hover:no-underline py-6">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed pb-6">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
};
