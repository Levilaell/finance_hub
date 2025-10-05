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
                O CaixaHub é uma plataforma de gestão financeira automatizada para pequenas e médias empresas brasileiras que oferece:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Conexão automática com mais de 20 bancos via Open Banking (Pluggy)</li>
                <li>Sincronização automática e em tempo real de transações bancárias</li>
                <li>Categorização inteligente de transações usando IA</li>
                <li>Dashboard financeiro completo com visão consolidada</li>
                <li>Geração de relatórios financeiros detalhados (PDF e Excel)</li>
                <li>Insights inteligentes e análises preditivas</li>
                <li>Gestão de categorias personalizadas</li>
                <li>Armazenamento seguro e criptografado de dados financeiros</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">3. Requisitos de Elegibilidade</h2>
              <p className="mb-4">
                Para usar o CaixaHub, você deve:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Ser maior de 18 anos</li>
                <li>Ter capacidade legal para celebrar contratos vinculantes</li>
                <li>Possuir CNPJ ativo ou ser profissional autônomo com CPF</li>
                <li>Fornecer informações verdadeiras, precisas e completas durante o cadastro</li>
                <li>Possuir cartão de crédito válido para iniciar o trial</li>
                <li>Concordar com estes Termos de Serviço e nossa Política de Privacidade</li>
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
                Nossa plataforma utiliza serviços de IA de terceiros (como OpenAI e outros) para:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Categorizar transações automaticamente com base no histórico e descrição</li>
                <li>Gerar insights e recomendações financeiras personalizadas</li>
                <li>Detectar padrões e anomalias em suas finanças</li>
                <li>Criar análises preditivas e projeções financeiras</li>
                <li>Melhorar continuamente a precisão das categorizações através de aprendizado</li>
              </ul>
              <p className="mb-4">
                <strong>Importante:</strong> As categorizações, insights e análises geradas pela IA são sugestões baseadas
                em algoritmos e devem ser revisadas pelo usuário. Não substituem consultoria financeira profissional.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">7. Planos e Pagamentos</h2>
              <p className="mb-4">
                <strong>Trial Gratuito (7 dias):</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Acesso completo a todos os recursos por 7 dias</li>
                <li>Requer cadastro de cartão de crédito</li>
                <li>Sem cobranças durante o período de trial</li>
                <li>Cancelamento gratuito a qualquer momento</li>
              </ul>

              <p className="mb-4">
                <strong>Plano Pro (R$ 97,00/mês):</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Conexão ilimitada com bancos via Open Banking</li>
                <li>Sincronização automática de transações</li>
                <li>Transações ilimitadas</li>
                <li>Categorização automática por IA</li>
                <li>Dashboard financeiro completo</li>
                <li>Relatórios detalhados (PDF e Excel)</li>
                <li>Categorias personalizadas</li>
                <li>Insights inteligentes ilimitados</li>
                <li>Suporte via WhatsApp</li>
                <li>Atualizações e novos recursos incluídos</li>
              </ul>

              <p className="mb-4">
                <strong>Processamento de Pagamentos:</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Processado de forma segura pela Stripe, líder global em pagamentos online</li>
                <li>Cartões aceitos: Visa, Mastercard, American Express, Elo</li>
                <li>Cobrança mensal automática após o período de trial</li>
                <li>Seus dados de pagamento são armazenados de forma criptografada pela Stripe</li>
                <li>Não armazenamos informações de cartão de crédito em nossos servidores</li>
                <li>Sem fidelidade ou multa por cancelamento</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">8. Trial e Política de Cancelamento</h2>
              <p className="mb-4">
                <strong>Durante o Trial:</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Você pode cancelar a qualquer momento durante os 7 dias de trial</li>
                <li>Não haverá nenhuma cobrança se cancelar durante o trial</li>
                <li>Após o trial, a cobrança mensal será iniciada automaticamente</li>
              </ul>

              <p className="mb-4">
                <strong>Após o Trial:</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Você pode cancelar sua assinatura a qualquer momento</li>
                <li>Sem fidelidade ou multa por cancelamento</li>
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

              <h2 className="text-xl font-semibold mt-8 mb-4">10. Serviços de Terceiros</h2>
              <p className="mb-4">
                O CaixaHub utiliza os seguintes serviços de terceiros para operar:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Pluggy:</strong> Para conexão com bancos via Open Banking</li>
                <li><strong>Stripe:</strong> Para processamento de pagamentos</li>
                <li><strong>Serviços de IA:</strong> Para categorização e análise de transações</li>
              </ul>
              <p className="mb-4">
                Estes serviços estão sujeitos aos seus próprios termos de uso e políticas de privacidade.
                O CaixaHub não tem controle sobre a disponibilidade ou funcionamento destes serviços externos.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">11. Limitação de Responsabilidade</h2>
              <p className="mb-4">
                O CaixaHub não será responsável por:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Decisões financeiras tomadas com base nas informações ou insights da plataforma</li>
                <li>Perdas resultantes de falhas técnicas, indisponibilidade do serviço ou de serviços de terceiros</li>
                <li>Erros ou atrasos na sincronização de dados bancários causados por instituições financeiras ou Pluggy</li>
                <li>Imprecisões na categorização automática por IA</li>
                <li>Falhas no processamento de pagamentos pela Stripe</li>
                <li>Danos indiretos, incidentais, especiais ou consequenciais</li>
                <li>Perda de lucros, receitas ou dados</li>
              </ul>
              <p className="mb-4">
                A plataforma fornece ferramentas de gestão financeira, mas não constitui consultoria financeira,
                contábil ou jurídica. Recomendamos consultar profissionais qualificados para decisões importantes.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">12. Segurança e Privacidade</h2>
              <p className="mb-4">
                Levamos a segurança dos seus dados muito a sério:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Criptografia de ponta a ponta para todos os dados sensíveis</li>
                <li>Conformidade integral com a LGPD (Lei Geral de Proteção de Dados)</li>
                <li>Acesso bancário apenas em modo leitura via Open Banking</li>
                <li>Não armazenamos senhas bancárias ou dados de cartão em nossos servidores</li>
                <li>Não vendemos ou compartilhamos seus dados financeiros com terceiros</li>
                <li>Dados de pagamento processados exclusivamente pela Stripe (PCI-DSS compliant)</li>
                <li>Dados de IA enviados de forma anonimizada para serviços de terceiros</li>
                <li>Auditorias de segurança e testes de penetração regulares</li>
                <li>Backups automáticos e recuperação de desastres</li>
              </ul>
              <p className="mb-4">
                Consulte nossa Política de Privacidade para mais detalhes sobre como coletamos, usamos e
                protegemos seus dados pessoais e financeiros.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">13. Retenção e Exclusão de Dados</h2>
              <p className="mb-4">
                Em conformidade com a LGPD, você tem direito a:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Solicitar acesso a todos os seus dados armazenados</li>
                <li>Solicitar correção de dados incorretos ou incompletos</li>
                <li>Solicitar exclusão de seus dados pessoais</li>
                <li>Revogar consentimento para processamento de dados</li>
                <li>Exportar seus dados em formato legível por máquina</li>
              </ul>
              <p className="mb-4">
                <strong>Retenção de Dados:</strong>
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Dados ativos são mantidos enquanto você tiver uma conta ativa</li>
                <li>Após cancelamento, seus dados permanecem disponíveis por 30 dias</li>
                <li>Após 30 dias, dados financeiros são anonimizados para fins estatísticos</li>
                <li>Dados fiscais podem ser retidos por até 5 anos conforme legislação brasileira</li>
                <li>Você pode solicitar exclusão completa a qualquer momento via WhatsApp</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">14. Notificações e Comunicações</h2>
              <p className="mb-4">
                Ao usar o CaixaHub, você concorda em receber comunicações eletrônicas:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>E-mails transacionais (confirmação de cadastro, avisos de cobrança, etc.)</li>
                <li>Avisos sobre término do trial e início da cobrança</li>
                <li>Notificações sobre atualizações importantes da plataforma</li>
                <li>Alertas de segurança ou problemas na conta</li>
                <li>Comunicados sobre mudanças nos Termos de Serviço</li>
              </ul>
              <p className="mb-4">
                Você pode optar por não receber comunicações de marketing, mas e-mails transacionais
                e de segurança são obrigatórios para o funcionamento da plataforma.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">15. Modificações dos Termos</h2>
              <p className="mb-4">
                Reservamo-nos o direito de modificar estes termos a qualquer momento. Notificaremos os usuários
                sobre mudanças significativas por e-mail ou através da plataforma com pelo menos 30 dias de
                antecedência.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">16. Lei Aplicável e Jurisdição</h2>
              <p className="mb-4">
                Estes termos são regidos pelas leis da República Federativa do Brasil. Qualquer disputa
                relacionada a estes termos será submetida à jurisdição exclusiva dos tribunais brasileiros.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">17. Contato</h2>
              <p className="mb-4">
                Para questões sobre estes Termos de Serviço, entre em contato:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>WhatsApp: <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">(17) 99267-9645</a></li>
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
              <a
                href="https://wa.me/5517992679645?text=Olá%2C%20vim%20do%20CaixaHub%20e%20gostaria%20de%20falar%20com%20o%20suporte"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-foreground"
              >
                Contato
              </a>
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
              © 2025 CaixaHub. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}