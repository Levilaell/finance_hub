"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { authService } from "@/services/auth.service";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");
  
  const [verifying, setVerifying] = useState(true);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (token) {
      verifyEmail(token);
    } else {
      setVerifying(false);
      setError("Token de verificação não encontrado");
    }
  }, [token]);

  const verifyEmail = async (verificationToken: string) => {
    try {
      await authService.verifyEmail(verificationToken);
      setVerified(true);
      setError("");
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (error: any) {
      setError(error.response?.data?.error || "Erro ao verificar email");
      setVerified(false);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Verificação de E-mail</CardTitle>
          <CardDescription>
            Confirmando seu endereço de e-mail
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {verifying && (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Verificando seu e-mail...
              </p>
            </div>
          )}

          {!verifying && verified && (
            <div className="flex flex-col items-center space-y-4">
              <CheckCircle className="h-12 w-12 text-green-500" />
              <div className="text-center space-y-2">
                <p className="font-semibold">E-mail verificado com sucesso!</p>
                <p className="text-sm text-muted-foreground">
                  Você será redirecionado para a página de login em alguns segundos...
                </p>
              </div>
              <Link href="/login">
                <Button>Ir para Login</Button>
              </Link>
            </div>
          )}

          {!verifying && !verified && error && (
            <div className="flex flex-col items-center space-y-4">
              <XCircle className="h-12 w-12 text-destructive" />
              <div className="text-center space-y-2">
                <p className="font-semibold">Erro na verificação</p>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
              <div className="flex gap-2">
                <Link href="/login">
                  <Button variant="outline">Fazer Login</Button>
                </Link>
                <Link href="/register">
                  <Button>Criar Nova Conta</Button>
                </Link>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}