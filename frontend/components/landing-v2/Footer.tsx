export const Footer = () => {
  return (
    <footer className="py-12 bg-muted/50 border-t border-border/50">
      <div className="container mx-auto px-4">
        <div className="text-center space-y-6">
          <div className="text-xl font-bold text-foreground">
            Caixa<span className="text-primary">Hub</span>
          </div>
          
          <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground">
            <a href="/privacy" className="hover:text-primary transition-colors duration-300">
              Política de Privacidade
            </a>
            <span>|</span>
            <a href="/terms" className="hover:text-primary transition-colors duration-300">
              Termos de Uso
            </a>
          </div>

          <p className="text-sm text-muted-foreground">
            © 2025 CaixaHub - Gestão financeira automática para pequenos negócios
          </p>
        </div>
      </div>
    </footer>
  );
};
