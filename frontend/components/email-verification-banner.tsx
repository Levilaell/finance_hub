"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/store/auth-store";
import { authService } from "@/services/auth.service";
import { Mail } from "lucide-react";
import { toast } from "sonner";
import { testId, TEST_IDS } from "@/utils/test-helpers";
import { 
  ResponsiveBannerContainer, 
  ResponsiveBannerContent, 
  ResponsiveButtonGroup,
  ResponsiveDismissButton 
} from "@/components/ui/responsive-banner";

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
    <ResponsiveBannerContainer 
      variant="info" 
      className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/10"
      {...testId(TEST_IDS.auth.verificationBanner)}
    >
      <ResponsiveBannerContent
        icon={<Mail className="h-4 w-4 sm:h-5 sm:w-5 text-blue-600" />}
        title="Verifique seu e-mail"
        description="Confirme seu endereço de e-mail para acessar todos os recursos do sistema."
        dismissButton={<ResponsiveDismissButton onClick={handleDismiss} />}
        actions={
          <ResponsiveButtonGroup
            primary={{
              label: loading ? "Enviando..." : "Reenviar",
              onClick: handleResendEmail,
              loading,
              variant: "default"
            }}
            secondary={{
              label: "Depois",
              onClick: handleDismiss
            }}
          />
        }
      />
    </ResponsiveBannerContainer>
  );
}