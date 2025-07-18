import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BanknotesIcon, ArrowLeftIcon } from "@heroicons/react/24/outline";

export default function TermsOfService() {
  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <BanknotesIcon className="h-8 w-8 text-primary" />
              <h1 className="text-2xl font-bold text-foreground">CaixaHub</h1>
            </Link>
            <Button variant="ghost" asChild>
              <Link href="/">
                <ArrowLeftIcon className="mr-2 h-4 w-4" />
                Voltar ao Início
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <section className="py-12 lg:py-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle className="text-3xl font-bold text-center">
                Termos de Serviço
              </CardTitle>
              <p className="text-center text-muted-foreground mt-2">
                Última atualização: {new Date().toLocaleDateString('pt-BR')}
              </p>
            </CardHeader>
            <CardContent className="prose prose-gray max-w-none">
              <h2 className="text-xl font-semibold mt-8 mb-4">1. Aceitação dos Termos</h2>
              <p className="mb-4">
                Ao acessar e usar a plataforma CaixaHub, você concorda em cumprir e estar vinculado aos seguintes 
                termos e condições de uso. Se você não concordar com qualquer parte destes termos, não deverá 
                usar nossa plataforma.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">2. Descrição do Serviço</h2>
              <p className="mb-4">
                O CaixaHub é uma plataforma de gestão financeira para pequenas e médias empresas brasileiras que oferece:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Conexão automática com contas bancárias via Open Banking</li>
                <li>Categorização inteligente de transações usando IA</li>
                <li>Geração de relatórios financeiros e análises</li>
                <li>Gestão de fluxo de caixa e planejamento financeiro</li>
                <li>Armazenamento seguro de dados financeiros</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">3. Requisitos de Elegibilidade</h2>
              <p className="mb-4">
                Para usar o CaixaHub, você deve:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Ser maior de 18 anos</li>
                <li>Ter capacidade legal para celebrar contratos vinculantes</li>
                <li>Possuir CNPJ ativo ou ser profissional autônomo com CPF</li>
                <li>Fornecer informações verdadeiras, precisas e completas</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">4. Conta de Usuário</h2>
              <p className="mb-4">
                Você é responsável por:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Manter a confidencialidade de sua senha e conta</li>
                <li>Todas as atividades que ocorram em sua conta</li>
                <li>Notificar imediatamente sobre qualquer uso não autorizado</li>
                <li>Não compartilhar suas credenciais de acesso</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">5. Conexão Bancária e Open Banking</h2>
              <p className="mb-4">
                Ao conectar suas contas bancárias:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Você autoriza o CaixaHub a acessar seus dados financeiros</li>
                <li>A conexão é realizada através de APIs seguras de Open Banking</li>
                <li>Utilizamos a plataforma Pluggy, certificada pelo Banco Central</li>
                <li>Você pode revogar o acesso a qualquer momento</li>
                <li>Os dados são atualizados automaticamente conforme disponibilidade dos bancos</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">6. Uso de Inteligência Artificial</h2>
              <p className="mb-4">
                Nossa plataforma utiliza IA para:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Categorizar transações automaticamente</li>
                <li>Gerar insights e recomendações financeiras</li>
                <li>Detectar padrões e anomalias em suas finanças</li>
                <li>Melhorar continuamente a precisão das análises</li>
              </ul>
              <p className="mb-4">
                As categorizações e análises são sugestões e devem ser revisadas pelo usuário.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">7. Planos e Pagamentos</h2>
              <p className="mb-4">
                <strong>Plano Gratuito:</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>1 conta bancária conectada</li>
                <li>Até 100 transações por mês</li>
                <li>Funcionalidades básicas de categorização</li>
              </ul>
              
              <p className="mb-4">
                <strong>Plano Pro (R$ 49,90/mês):</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Contas bancárias ilimitadas</li>
                <li>Transações ilimitadas</li>
                <li>Categorização avançada com IA</li>
                <li>Relatórios completos e exportação</li>
                <li>Suporte prioritário</li>
              </ul>

              <p className="mb-4">
                <strong>Plano Enterprise (Personalizado):</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Todas as funcionalidades do Pro</li>
                <li>Suporte dedicado</li>
                <li>SLA garantido</li>
                <li>Treinamento personalizado</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">8. Política de Cancelamento</h2>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Você pode cancelar sua assinatura a qualquer momento</li>
                <li>O acesso continua até o fim do período pago</li>
                <li>Não há reembolso para períodos não utilizados</li>
                <li>Seus dados permanecem disponíveis por 30 dias após o cancelamento</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">9. Propriedade Intelectual</h2>
              <p className="mb-4">
                Todo o conteúdo da plataforma CaixaHub, incluindo textos, gráficos, logos, ícones, imagens, 
                clipes de áudio, downloads digitais e compilações de dados, é propriedade do CaixaHub ou de 
                seus fornecedores de conteúdo e é protegido pelas leis brasileiras e internacionais de 
                propriedade intelectual.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">10. Limitação de Responsabilidade</h2>
              <p className="mb-4">
                O CaixaHub não será responsável por:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Decisões financeiras tomadas com base nas informações da plataforma</li>
                <li>Perdas resultantes de falhas técnicas ou indisponibilidade do serviço</li>
                <li>Erros ou atrasos na sincronização de dados bancários</li>
                <li>Danos indiretos, incidentais ou consequenciais</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">11. Segurança e Privacidade</h2>
              <p className="mb-4">
                Levamos a segurança dos seus dados muito a sério:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Utilizamos criptografia de ponta a ponta</li>
                <li>Cumprimos integralmente a LGPD</li>
                <li>Não vendemos ou compartilhamos seus dados com terceiros</li>
                <li>Realizamos auditorias de segurança regulares</li>
                <li>Consulte nossa Política de Privacidade para mais detalhes</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">12. Modificações dos Termos</h2>
              <p className="mb-4">
                Reservamo-nos o direito de modificar estes termos a qualquer momento. Notificaremos os usuários 
                sobre mudanças significativas por e-mail ou através da plataforma com pelo menos 30 dias de 
                antecedência.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">13. Lei Aplicável e Jurisdição</h2>
              <p className="mb-4">
                Estes termos são regidos pelas leis da República Federativa do Brasil. Qualquer disputa 
                relacionada a estes termos será submetida à jurisdição exclusiva dos tribunais brasileiros.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">14. Contato</h2>
              <p className="mb-4">
                Para questões sobre estes Termos de Serviço, entre em contato:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>E-mail: suporte@caixahub.com.br</li>
                <li>WhatsApp: (11) 9XXXX-XXXX</li>
                <li>Horário de atendimento: Segunda a Sexta, 9h às 18h</li>
              </ul>

              <div className="mt-12 p-6 bg-muted rounded-lg">
                <p className="text-sm text-center text-muted-foreground">
                  Ao usar o CaixaHub, você reconhece que leu, entendeu e concorda em estar vinculado a estes 
                  Termos de Serviço e nossa Política de Privacidade.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 mt-16">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2">
              <BanknotesIcon className="h-6 w-6 text-primary" />
              <span className="font-semibold">CaixaHub</span>
            </div>
            <div className="flex space-x-6 text-sm text-muted-foreground">
              <Link href="/privacy" className="hover:text-foreground">
                Política de Privacidade
              </Link>
              <Link href="/terms" className="hover:text-foreground">
                Termos de Serviço
              </Link>
              <Link href="/pricing" className="hover:text-foreground">
                Planos
              </Link>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2024 CaixaHub. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}