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
  BookOpen,
  FileTextIcon,
} from "lucide-react";
import { BanknotesIcon } from "@heroicons/react/24/outline";

interface MainLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Transações", href: "/transactions", icon: Receipt },
  { name: "Contas Bancárias", href: "/accounts", icon: Wallet },
  { name: "Contas", href: "/bills", icon: FileTextIcon },
  { name: "Categorias", href: "/categories", icon: Tags },
  { name: "Insights", href: "/ai-insights", icon: Sparkles, beta: true },
  { name: "Relatórios", href: "/reports", icon: FileText },
  { name: "Como Usar", href: "/how-to-use", icon: BookOpen },
  { name: "Configurações", href: "/settings", icon: Settings },
];

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore(); // ✅ Removed _hasHydrated
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);

  // ✅ Simplified user functions - removed hydration checks
  const getUserInitials = () => {
    if (!user) return '??';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return first + last || user.email?.[0]?.toUpperCase() || '??';
  };

  const getUserFullName = () => {
    if (!user) return 'Usuário';
    return `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Usuário';
  };

  const getUserEmail = () => {
    return user?.email || '';
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
              <div className="h-10 w-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <BanknotesIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                CaixaHub
              </span>
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
                    "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-300 relative",
                    isActive
                      ? "bg-white/10 text-white border border-white/20"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  <span className="flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{item.name}</span>
                  {item.beta && (
                    <span className="ml-auto px-1.5 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-400 rounded uppercase flex-shrink-0">
                      Beta
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {getUserInitials()}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">
                  {getUserFullName()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {getUserEmail()}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="mt-4 w-full justify-start hover:bg-destructive/10 hover:text-destructive transition-all duration-300"
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
              <div className="h-10 w-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <BanknotesIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">
                CaixaHub
              </span>
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
                    "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-300 relative",
                    isActive
                      ? "bg-white/10 text-white border border-white/20"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  <span className="flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{item.name}</span>
                  {item.beta && (
                    <span className="ml-auto px-1.5 py-0.5 text-[10px] font-semibold bg-blue-500/20 text-blue-400 rounded uppercase flex-shrink-0">
                      Beta
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
          <div className="border-t p-4">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {getUserInitials()}
                </span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">
                  {getUserFullName()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {getUserEmail()}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              className="mt-4 w-full justify-start hover:bg-destructive/10 hover:text-destructive transition-all duration-300"
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
        <header className="sticky top-0 z-40 flex h-16 items-center border-b bg-background px-4 sm:px-6 lg:px-8 xl:px-10">
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
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center shadow-sm">
                  <span className="text-sm font-medium text-blue-800">
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
                      className="block px-4 py-2 text-sm text-foreground hover:bg-muted transition-all duration-200"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Configurações
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full px-4 py-2 text-left text-sm text-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
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
        <main className="flex-1 p-4 sm:p-6 lg:p-8 xl:p-10">{children}</main>
        
        {/* Footer */}
        <footer className="border-t mt-auto">
          <div className="px-4 py-4 sm:px-6 lg:px-8 xl:px-10">
            <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
              <div className="text-sm text-muted-foreground">
                © 2025 CaixaHub. Todos os direitos reservados.
              </div>
              <div className="flex space-x-4 text-sm text-muted-foreground">
                <a
                  href="https://wa.me/5517992679645?text=Olá%2C%20vim%20do%20CaixaHub%20e%20gostaria%20de%20falar%20com%20o%20suporte"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  Contato
                </a>
                <Link href="/terms" className="hover:text-foreground transition-colors">
                  Termos de Serviço
                </Link>
                <Link href="/privacy" className="hover:text-foreground transition-colors">
                  Política de Privacidade
                </Link>
                <Link href="/pricing" className="hover:text-foreground transition-colors">
                  Plano
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}