"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BanknotesIcon } from "@heroicons/react/24/outline";

export const AuthHeader = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background border-b border-border/50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-20">
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
              <BanknotesIcon className="h-6 w-6 text-primary" />
            </div>
            <span className="text-xl font-bold">
              CaixaHub
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <Button variant="ghost" asChild>
              <Link href="/login">Login</Link>
            </Button>
            <Button className="bg-primary hover:bg-primary/90 text-primary-foreground" asChild>
              <Link href="/pricing">Ver Planos</Link>
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};
