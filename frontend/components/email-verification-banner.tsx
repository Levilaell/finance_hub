"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";
import { authService } from "@/services/auth.service";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Mail, X } from "lucide-react";
import { toast } from "sonner";
import { testId, TEST_IDS } from "@/utils/test-helpers";

export function EmailVerificationBanner() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [localDismissed, setLocalDismissed] = useState(false);

  useEffect(() => {
    // Check if banner was dismissed
    const dismissed = localStorage.getItem('email_verification_banner_dismissed');
    const dismissedDate = localStorage.getItem('email_verification_banner_dismissed_date');
    
    if (dismissed && dismissedDate) {
      // Reset dismissal after 24 hours
      const dismissedTime = new Date(dismissedDate).getTime();
      const now = new Date().getTime();
      const hoursSinceDismissed = (now - dismissedTime) / (1000 * 60 * 60);
      
      if (hoursSinceDismissed < 24) {
        setLocalDismissed(true);
      } else {
        localStorage.removeItem('email_verification_banner_dismissed');
        localStorage.removeItem('email_verification_banner_dismissed_date');
      }
    }
  }, []);

  const handleResendEmail = async () => {
    setLoading(true);
    try {
      await authService.resendVerificationEmail();
      toast.success("E-mail de verificação enviado!", {
        description: "Verifique sua caixa de entrada e a pasta de spam.",
      });
    } catch (error: any) {
      toast.error("Erro ao enviar e-mail", {
        description: error.response?.data?.message || "Tente novamente mais tarde.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    setLocalDismissed(true);
    localStorage.setItem('email_verification_banner_dismissed', 'true');
    localStorage.setItem('email_verification_banner_dismissed_date', new Date().toISOString());
  };

  if (!user || user.is_email_verified || localDismissed || isDismissed) {
    return null;
  }

  return (
    <Card className="mb-6 border-muted relative" {...testId(TEST_IDS.auth.verificationBanner)}>
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
        aria-label="Fechar banner"
      >
        <X className="h-5 w-5" />
      </button>
      
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-3 flex-1">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
            <Mail className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">
              Verifique seu e-mail
            </p>
            <p className="text-sm text-muted-foreground">
              Confirme seu endereço de e-mail para acessar todos os recursos do sistema.
            </p>
          </div>
        </div>
        <div className="flex space-x-2 ml-4">
          <Button 
            size="sm" 
            onClick={handleResendEmail}
            disabled={loading}
            variant="default"
            {...testId(TEST_IDS.auth.resendVerification)}
          >
            {loading ? "Enviando..." : "Reenviar e-mail"}
          </Button>
          <Button 
            size="sm" 
            variant="ghost"
            onClick={handleDismiss}
          >
            Depois
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}