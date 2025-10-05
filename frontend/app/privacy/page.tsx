import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BanknotesIcon, ArrowLeftIcon } from "@heroicons/react/24/outline";

export default function PrivacyPolicy() {
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
                Política de Privacidade
              </CardTitle>
              <p className="text-center text-muted-foreground mt-2">
                Última atualização: {new Date().toLocaleDateString('pt-BR')}
              </p>
            </CardHeader>
            <CardContent className="prose prose-gray max-w-none">
              <div className="p-6 bg-primary/10 rounded-lg mb-8">
                <p className="text-lg font-semibold mb-2">Nosso Compromisso com Sua Privacidade</p>
                <p>
                  No CaixaHub, a proteção dos seus dados é nossa prioridade máxima. Esta política detalha 
                  como coletamos, usamos, armazenamos e protegemos suas informações, em total conformidade 
                  com a Lei Geral de Proteção de Dados (LGPD).
                </p>
              </div>

              <h2 className="text-xl font-semibold mt-8 mb-4">1. Informações que Coletamos</h2>
              
              <h3 className="text-lg font-medium mt-6 mb-3">1.1 Dados de Cadastro</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Nome completo e/ou razão social</li>
                <li>CPF ou CNPJ</li>
                <li>Endereço de e-mail</li>
                <li>Número de telefone</li>
                <li>Endereço comercial</li>
              </ul>

              <h3 className="text-lg font-medium mt-6 mb-3">1.2 Dados Financeiros</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Informações de contas bancárias conectadas via Open Banking (Pluggy)</li>
                <li>Histórico de transações bancárias em modo somente leitura</li>
                <li>Saldos, limites e extratos bancários</li>
                <li>Categorias de despesas e receitas (atribuídas manualmente ou por IA)</li>
                <li>Informações de cartões de crédito processadas pela Stripe (não armazenamos dados completos)</li>
              </ul>

              <p className="mb-4 text-sm bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                <strong>Importante:</strong> Não armazenamos senhas bancárias. O acesso aos bancos é feito exclusivamente
                via Open Banking regulamentado pelo Banco Central, em modo somente leitura.
              </p>

              <h3 className="text-lg font-medium mt-6 mb-3">1.3 Dados de Uso</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Endereço IP</li>
                <li>Tipo de navegador e dispositivo</li>
                <li>Páginas visitadas e funcionalidades utilizadas</li>
                <li>Data e hora de acesso</li>
                <li>Preferências de configuração</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">2. Como Usamos Suas Informações</h2>
              <p className="mb-4">Utilizamos seus dados para:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Fornecer e melhorar nossos serviços de gestão financeira automatizada</li>
                <li>Categorizar automaticamente suas transações usando inteligência artificial</li>
                <li>Gerar relatórios, análises financeiras e insights personalizados</li>
                <li>Sincronizar automaticamente suas contas bancárias via Open Banking</li>
                <li>Processar pagamentos de assinatura através da Stripe</li>
                <li>Enviar notificações importantes sobre sua conta, trial e cobranças</li>
                <li>Prevenir fraudes e atividades ilegais</li>
                <li>Cumprir obrigações legais e regulatórias (LGPD, Banco Central)</li>
                <li>Desenvolver novos recursos baseados em padrões de uso (dados anonimizados)</li>
                <li>Enviar dados anonimizados para serviços de IA para melhorar a categorização</li>
              </ul>

              <h3 className="text-lg font-medium mt-6 mb-3">2.1 Uso de Inteligência Artificial</h3>
              <p className="mb-4">
                Utilizamos serviços de IA de terceiros (como OpenAI) para processar suas transações e gerar insights.
                Estes dados são enviados de forma <strong>anonimizada</strong>, sem informações que possam identificá-lo pessoalmente.
                A IA ajuda a:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Categorizar transações com base em descrições e histórico</li>
                <li>Gerar insights e recomendações financeiras personalizadas</li>
                <li>Detectar padrões e anomalias nas finanças</li>
                <li>Criar análises preditivas e projeções</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">3. Base Legal para Processamento</h2>
              <p className="mb-4">
                Processamos seus dados com base nas seguintes bases legais previstas na LGPD:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Execução de contrato:</strong> Para fornecer os serviços contratados</li>
                <li><strong>Consentimento:</strong> Para funcionalidades opcionais e comunicações de marketing</li>
                <li><strong>Legítimo interesse:</strong> Para melhorar nossos serviços e prevenir fraudes</li>
                <li><strong>Cumprimento de obrigação legal:</strong> Para atender requisitos regulatórios</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">4. Compartilhamento de Dados</h2>
              <p className="mb-4">
                <strong>Nunca vendemos seus dados.</strong> Compartilhamos informações apenas com:
              </p>

              <h3 className="text-lg font-medium mt-6 mb-3">4.1 Serviços de Terceiros Essenciais</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>
                  <strong>Pluggy (Open Banking):</strong> Para conexão segura com instituições financeiras.
                  Compartilhamos: credenciais bancárias (criptografadas), dados de transações.
                  Pluggy é certificado pelo Banco Central do Brasil.
                </li>
                <li>
                  <strong>Stripe (Pagamentos):</strong> Para processar pagamentos de assinatura.
                  Compartilhamos: nome, e-mail, informações de cartão (processadas diretamente pela Stripe).
                  Stripe é certificado PCI-DSS Nível 1.
                </li>
                <li>
                  <strong>Serviços de IA (OpenAI e outros):</strong> Para categorização e insights.
                  Compartilhamos: descrições de transações <strong>anonimizadas</strong>, sem dados pessoais identificáveis.
                </li>
              </ul>

              <h3 className="text-lg font-medium mt-6 mb-3">4.2 Outras Situações</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Prestadores de serviço:</strong> Hospedagem, análise de dados - sob rigorosos acordos de confidencialidade (DPA)</li>
                <li><strong>Autoridades legais:</strong> Quando exigido por lei, ordem judicial ou investigação oficial</li>
                <li><strong>Sucessores de negócio:</strong> Em caso de fusão, aquisição ou venda de ativos (com notificação prévia)</li>
              </ul>

              <p className="mb-4 text-sm bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <strong>Garantia:</strong> Todos os parceiros são selecionados com base em rigorosos critérios de segurança
                e conformidade com a LGPD. Estabelecemos acordos de processamento de dados (DPA) com todos os prestadores.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">5. Segurança dos Dados</h2>
              <p className="mb-4">Implementamos medidas robustas de segurança:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Criptografia AES-256 para dados em repouso</li>
                <li>TLS 1.3 para dados em trânsito</li>
                <li>Autenticação segura e controle de acesso</li>
                <li>Monitoramento 24/7 contra ameaças e atividades suspeitas</li>
                <li>Backups automáticos diários em múltiplas localizações</li>
                <li>Testes de segurança e penetração periódicos</li>
                <li>Certificação ISO 27001 (em processo)</li>
                <li>Logs de auditoria para rastreabilidade</li>
              </ul>

              <h3 className="text-lg font-medium mt-6 mb-3">5.1 Incidentes de Segurança</h3>
              <p className="mb-4">
                Em caso de incidente de segurança que possa causar risco aos seus dados:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Notificaremos você em até 72 horas após a descoberta do incidente</li>
                <li>Informaremos a ANPD conforme exigido pela LGPD</li>
                <li>Forneceremos informações sobre o incidente, dados afetados e medidas tomadas</li>
                <li>Implementaremos medidas corretivas imediatas para mitigar riscos</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">6. Retenção de Dados</h2>
              <p className="mb-4">Mantemos seus dados pelo tempo necessário:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Durante conta ativa:</strong> Todos os dados são mantidos para operação da plataforma</li>
                <li><strong>Durante trial de 7 dias:</strong> Dados completos mantidos para conversão em assinatura paga</li>
                <li><strong>Após cancelamento:</strong> Dados disponíveis por 30 dias para possível reativação</li>
                <li><strong>Após 30 dias do cancelamento:</strong> Dados financeiros são anonimizados para fins estatísticos</li>
                <li><strong>Dados fiscais/legais:</strong> Retidos por até 5 anos conforme legislação brasileira (Receita Federal)</li>
                <li><strong>Dados de pagamento (Stripe):</strong> Mantidos conforme política da Stripe e requisitos PCI-DSS</li>
                <li><strong>Logs de segurança:</strong> 12 meses para investigação de incidentes</li>
                <li><strong>Dados de marketing:</strong> Até revogação do consentimento</li>
              </ul>

              <p className="mb-4 text-sm bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                <strong>Direito de exclusão:</strong> Você pode solicitar a exclusão completa de seus dados a qualquer momento,
                exceto aqueles que devemos reter por obrigação legal. Entre em contato via WhatsApp para exercer esse direito.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">7. Seus Direitos (LGPD)</h2>
              <p className="mb-4">Você tem direito a:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Acesso:</strong> Solicitar cópia de todos os seus dados</li>
                <li><strong>Correção:</strong> Corrigir dados incompletos ou desatualizados</li>
                <li><strong>Exclusão:</strong> Solicitar a exclusão de seus dados</li>
                <li><strong>Portabilidade:</strong> Receber seus dados em formato estruturado</li>
                <li><strong>Revogação:</strong> Revogar consentimentos a qualquer momento</li>
                <li><strong>Oposição:</strong> Opor-se a determinados processamentos</li>
                <li><strong>Informação:</strong> Saber com quem compartilhamos seus dados</li>
              </ul>
              <p className="mb-4">
                Para exercer seus direitos, entre em contato:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>WhatsApp: <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">(17) 99267-9645</a></li>
                <li>Horário: Segunda a Sexta, 9h às 18h</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">8. Cookies e Tecnologias Similares</h2>

              <h3 className="text-lg font-medium mt-6 mb-3">8.1 Tipos de Cookies</h3>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Cookies essenciais:</strong> Necessários para autenticação e funcionamento da plataforma</li>
                <li><strong>Cookies de preferência:</strong> Armazenam suas configurações e preferências de uso</li>
                <li><strong>Cookies de desempenho:</strong> Coletam informações sobre como você usa a plataforma (anonimizados)</li>
                <li><strong>Cookies de segurança:</strong> Ajudam a detectar fraudes e proteger sua conta</li>
              </ul>

              <h3 className="text-lg font-medium mt-6 mb-3">8.2 Gerenciamento de Cookies</h3>
              <p className="mb-4">
                Você pode gerenciar cookies nas configurações do seu navegador. No entanto, desabilitar cookies
                essenciais pode afetar a funcionalidade da plataforma (ex: você não conseguirá fazer login).
              </p>
              <p className="mb-4">
                Cookies de desempenho e preferência podem ser desabilitados sem afetar funcionalidades básicas.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">9. Menores de Idade</h2>
              <p className="mb-4">
                O CaixaHub não é destinado a menores de 18 anos. Não coletamos intencionalmente 
                dados de menores. Se identificarmos tal coleta, excluiremos os dados imediatamente.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">10. Transferências Internacionais</h2>
              <p className="mb-4">
                <strong>Armazenamento principal:</strong> Seus dados são processados e armazenados no Brasil.
              </p>
              <p className="mb-4">
                <strong>Transferências para terceiros:</strong> Alguns serviços que utilizamos podem processar dados fora do Brasil:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>
                  <strong>Stripe (EUA):</strong> Processa dados de pagamento com proteção adequada conforme LGPD.
                  Stripe possui certificação PCI-DSS e cláusulas contratuais padrão (SCCs).
                </li>
                <li>
                  <strong>Serviços de IA (EUA/Europa):</strong> Recebem dados <strong>anonimizados</strong> para processamento.
                  Não há transferência de dados pessoais identificáveis.
                </li>
                <li>
                  <strong>Infraestrutura de nuvem:</strong> Utilizamos servidores com data centers no Brasil, mas backups
                  podem ser replicados em outras regiões com criptografia adequada.
                </li>
              </ul>
              <p className="mb-4">
                Todas as transferências internacionais são realizadas com garantias adequadas conforme Art. 33 da LGPD,
                incluindo cláusulas contratuais padrão, certificações de segurança e acordos de proteção de dados.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">11. Alterações nesta Política</h2>
              <p className="mb-4">
                Podemos atualizar esta política periodicamente. Notificaremos sobre mudanças significativas 
                por e-mail ou através da plataforma com 30 dias de antecedência. O uso continuado após 
                as alterações constitui aceitação da nova política.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">12. Encarregado de Dados (DPO)</h2>
              <p className="mb-4">
                Estamos em processo de designação formal de um Encarregado de Proteção de Dados (DPO).
                Enquanto isso, todas as questões relacionadas à privacidade e LGPD devem ser direcionadas para:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>WhatsApp: <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">(17) 99267-9645</a></li>
                <li>Horário: Segunda a Sexta, 9h às 18h</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">13. Autoridade Nacional de Proteção de Dados</h2>
              <p className="mb-4">
                Você tem o direito de apresentar reclamação à Autoridade Nacional de Proteção de Dados (ANPD):
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Website: www.gov.br/anpd</li>
                <li>E-mail: ouvidoria@anpd.gov.br</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">14. Contato</h2>
              <p className="mb-4">
                Para questões sobre privacidade e proteção de dados:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>WhatsApp: <a href="https://wa.me/5517992679645" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">(17) 99267-9645</a></li>
                <li>Horário de atendimento: Segunda a Sexta, 9h às 18h</li>
              </ul>

              <p className="mt-4 mb-4">
                <strong>Tempo de resposta:</strong> Responderemos sua solicitação em até 15 dias úteis, conforme estabelecido pela LGPD.
                Em casos complexos, podemos prorrogar por mais 15 dias, com notificação prévia.
              </p>

              <div className="mt-12 p-6 bg-muted rounded-lg">
                <p className="text-sm text-center text-muted-foreground">
                  Esta Política de Privacidade é parte integrante dos nossos Termos de Serviço. 
                  Ao usar o CaixaHub, você confirma que leu e compreendeu como tratamos seus dados pessoais.
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