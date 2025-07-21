"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";
import {
  LayoutDashboard,
  Receipt,
  Wallet,
  Tags,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Bell,
  Sparkles,
} from "lucide-react";

interface MainLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Transações", href: "/transactions", icon: Receipt },
  { name: "Contas", href: "/accounts", icon: Wallet },
  { name: "Categorias", href: "/categories", icon: Tags },
  { name: "Insights com IA", href: "/ai-insights", icon: Sparkles },
  { name: "Relatórios", href: "/reports", icon: FileText },
  { name: "Configurações", href: "/settings", icon: Settings },
];

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, _hasHydrated } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);

  // Get user initials safely
  const getUserInitials = () => {
    if (!user || !_hasHydrated) return '??';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return first + last || '??';
  };

  const getUserFullName = () => {
    if (!user || !_hasHydrated) return 'Carregando...';
    return `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Usuário';
  };

  const getUserEmail = () => {
    if (!user || !_hasHydrated) return '';
    return user.email || '';
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar */}
      <div
        className={cn(
          "fixed inset-0 z-50 lg:hidden",
          sidebarOpen ? "block" : "hidden"
        )}
      >
        <div
          className="fixed inset-0 bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-card">
          <div className="flex h-16 items-center justify-between px-4">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <span className="text-xl font-bold">CaixaHub</span>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-medium" suppressHydrationWarning>
                  {getUserInitials()}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium" suppressHydrationWarning>
                  {getUserFullName()}
                </p>
                <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                  {getUserEmail()}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="mt-4 w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </Button>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-1 flex-col bg-card border-r">
          <div className="flex h-16 items-center px-4">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <span className="text-xl font-bold">CaixaHub</span>
            </Link>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-medium" suppressHydrationWarning>
                  {getUserInitials()}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium" suppressHydrationWarning>
                  {getUserFullName()}
                </p>
                <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                  {getUserEmail()}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="mt-4 w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="sticky top-0 z-40 flex h-16 items-center border-b bg-background px-4 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex flex-1 items-center justify-end space-x-4">
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </Button>
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2"
              >
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {getUserInitials()}
                  </span>
                </div>
                <ChevronDown className="h-4 w-4" />
              </Button>
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-md bg-card border shadow-lg">
                  <div className="py-1">
                    <Link
                      href="/settings"
                      className="block px-4 py-2 text-sm text-foreground hover:bg-accent"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Configurações
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full px-4 py-2 text-left text-sm text-foreground hover:bg-accent"
                    >
                      Sair
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 sm:p-8 lg:p-10">{children}</main>
        
        {/* Footer */}
        <footer className="border-t mt-auto">
          <div className="px-6 py-4 sm:px-8 lg:px-10">
            <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
              <div className="text-sm text-muted-foreground">
                © 2024 CaixaHub. Todos os direitos reservados.
              </div>
              <div className="flex space-x-4 text-sm text-muted-foreground">
                <Link href="/terms" className="hover:text-foreground transition-colors">
                  Termos de Serviço
                </Link>
                <Link href="/privacy" className="hover:text-foreground transition-colors">
                  Política de Privacidade
                </Link>
                <Link href="/pricing" className="hover:text-foreground transition-colors">
                  Planos
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}