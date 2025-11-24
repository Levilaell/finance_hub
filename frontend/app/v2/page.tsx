"use client";

import { Header } from "@/components/landing-v2/Header";
import { HeroSection } from "@/components/landing-v2/HeroSection";
import { ProblemSolutionSection } from "@/components/landing-v2/ProblemSolutionSection";
import { HowItWorksSection } from "@/components/landing-v2/HowItWorksSection";
import { DemoSection } from "@/components/landing-v2/DemoSection";
import { TestimonialsSection } from "@/components/landing-v2/TestimonialsSection";
import { PricingSection } from "@/components/landing-v2/PricingSection";
import { FAQSection } from "@/components/landing-v2/FAQSection";
import { FinalCTASection } from "@/components/landing-v2/FinalCTASection";
import { Footer } from "@/components/landing-v2/Footer";

export default function LandingV2Page() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20">
        <HeroSection />
        <ProblemSolutionSection />
        <HowItWorksSection />
        <DemoSection />
        <TestimonialsSection />
        <PricingSection />
        <FAQSection />
        <FinalCTASection />
      </main>
      <Footer />
    </div>
  );
}
