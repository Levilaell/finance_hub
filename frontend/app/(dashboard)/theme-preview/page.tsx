'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Info,
  Sparkles,
  Moon,
  Sun,
  CreditCard,
  TrendingUp,
  Wallet
} from 'lucide-react';

export default function ThemePreviewPage() {
  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white">Sistema de Cores CaixaHub</h1>
        <p className="text-muted-foreground text-lg">
          Design System oficial com cores do cores_design.md
        </p>
        <div className="flex justify-center gap-4">
          <Badge className="glass">Dark Theme Padrão</Badge>
          <Badge className="shimmer">Animações Otimizadas</Badge>
          <Badge className="gradient-shift text-white">Gradientes Vibrantes</Badge>
        </div>
      </div>

      {/* Color Palette */}
      <Card className="glass">
        <CardHeader>
          <CardTitle>Paleta de Cores</CardTitle>
          <CardDescription>Cores principais do tema</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="h-20 bg-background rounded-lg border"></div>
            <p className="text-sm text-muted-foreground">Background</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-primary rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Primary</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-secondary rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Secondary</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-accent rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Accent</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-card rounded-lg border"></div>
            <p className="text-sm text-muted-foreground">Card</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-muted rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Muted</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-destructive rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Destructive</p>
          </div>
          <div className="space-y-2">
            <div className="h-20 bg-gradient-primary rounded-lg"></div>
            <p className="text-sm text-muted-foreground">Gradient</p>
          </div>
        </CardContent>
      </Card>

      {/* Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Botões</CardTitle>
          <CardDescription>Diferentes estilos de botões</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Button>Primary Button</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button className="btn-gradient text-white">Gradient</Button>
          </div>
          <div className="flex flex-wrap gap-4">
            <Button size="sm">Small</Button>
            <Button>Default</Button>
            <Button size="lg">Large</Button>
            <Button disabled>Disabled</Button>
          </div>
        </CardContent>
      </Card>

      {/* Cards with Glass Effect */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="glass glass-hover hover-lift">
          <CardHeader>
            <Wallet className="h-8 w-8 text-primary mb-2" />
            <CardTitle>Saldo Total</CardTitle>
            <CardDescription>Visão geral financeira</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">R$ 12.450,00</p>
            <p className="text-sm text-muted-foreground mt-2">+12.5% este mês</p>
          </CardContent>
        </Card>

        <Card className="glass glass-hover hover-lift">
          <CardHeader>
            <TrendingUp className="h-8 w-8 text-secondary mb-2" />
            <CardTitle>Receitas</CardTitle>
            <CardDescription>Entradas do mês</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">R$ 8.200,00</p>
            <p className="text-sm text-success mt-2">↑ 8% vs mês anterior</p>
          </CardContent>
        </Card>

        <Card className="glass glass-hover hover-lift">
          <CardHeader>
            <CreditCard className="h-8 w-8 text-accent mb-2" />
            <CardTitle>Despesas</CardTitle>
            <CardDescription>Gastos do mês</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">R$ 5.750,00</p>
            <p className="text-sm text-destructive mt-2">↑ 3% vs mês anterior</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Alertas e Notificações</CardTitle>
          <CardDescription>Estados semânticos</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3 p-4 bg-success/10 text-success rounded-lg">
            <CheckCircle2 className="h-5 w-5" />
            <span>Operação realizada com sucesso!</span>
          </div>
          <div className="flex items-center gap-3 p-4 bg-destructive/10 text-destructive rounded-lg">
            <XCircle className="h-5 w-5" />
            <span>Erro ao processar solicitação</span>
          </div>
          <div className="flex items-center gap-3 p-4 bg-warning/10 text-warning rounded-lg">
            <AlertCircle className="h-5 w-5" />
            <span>Atenção: verificar informações</span>
          </div>
          <div className="flex items-center gap-3 p-4 bg-info/10 text-info rounded-lg">
            <Info className="h-5 w-5" />
            <span>Informação importante</span>
          </div>
        </CardContent>
      </Card>

      {/* Form Elements */}
      <Card>
        <CardHeader>
          <CardTitle>Elementos de Formulário</CardTitle>
          <CardDescription>Inputs e controles</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="seu@email.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="disabled">Campo Desabilitado</Label>
            <Input id="disabled" disabled placeholder="Campo desabilitado" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="focus">Campo com Foco</Label>
            <Input id="focus" placeholder="Clique para ver o foco" className="focus:ring-2 focus:ring-primary" />
          </div>
        </CardContent>
      </Card>

      {/* Special Effects */}
      <Card className="overflow-hidden">
        <CardHeader className="bg-gradient-subtle">
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 animate-glow" />
            Efeitos Especiais do Design System
          </CardTitle>
          <CardDescription>Animações e gradientes conforme cores_design.md</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button className="animate-glow">Animação Glow</Button>
            <Button className="hover-glow">Hover Glow</Button>
            <Button className="accent-glow bg-accent">Accent Glow</Button>
            <Button variant="outline" className="shimmer">Efeito Shimmer</Button>
          </div>
          
          <div className="p-6 gradient-shift rounded-lg text-white text-center cursor-pointer">
            <p className="text-xl font-semibold">Gradiente Animado (6s loop)</p>
          </div>
          
          <div className="p-6 bg-gradient-primary rounded-lg text-white text-center hover-glow cursor-pointer">
            <p className="text-xl font-semibold">Gradiente Primary → Accent</p>
          </div>
          
          <div className="p-6 glass rounded-lg hover-lift cursor-pointer flex items-center justify-center gap-4">
            <div className="w-8 h-8 spinner"></div>
            <p className="text-lg">Spinner com Glass Morphism</p>
          </div>
          
          <div className="p-4 bg-card rounded-lg shimmer">
            <p className="text-muted-foreground">Loading com Shimmer Effect...</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}