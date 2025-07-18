"use client";

import { useState } from "react";
import { useAuthStore } from "@/store/auth-store";
import { authService } from "@/services/auth.service";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Info, X } from "lucide-react";
import { toast } from "sonner";

export function EmailVerificationBanner() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  if (!user || user.is_email_verified || dismissed) {
    return null;
  }

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

  return (
    <Alert className="border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-900/20">
      <Info className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
      <AlertDescription className="flex items-center justify-between">
        <div className="flex-1">
          <span className="text-yellow-800 dark:text-yellow-200">
            Seu e-mail ainda não foi verificado. 
          </span>
          <span className="text-yellow-700 dark:text-yellow-300 ml-1">
            Verifique sua caixa de entrada ou
          </span>
          <Button
            variant="link"
            size="sm"
            className="text-yellow-700 hover:text-yellow-800 dark:text-yellow-300 dark:hover:text-yellow-200 p-0 ml-1"
            onClick={handleResendEmail}
            disabled={loading}
          >
            {loading ? "Enviando..." : "reenvie o e-mail"}
          </Button>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="ml-4 text-yellow-600 hover:text-yellow-700 dark:text-yellow-400 dark:hover:text-yellow-300"
          onClick={() => setDismissed(true)}
        >
          <X className="h-4 w-4" />
        </Button>
      </AlertDescription>
    </Alert>
  );
}