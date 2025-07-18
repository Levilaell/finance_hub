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
                <li>Informações de contas bancárias conectadas</li>
                <li>Histórico de transações bancárias</li>
                <li>Saldos e extratos</li>
                <li>Categorias de despesas e receitas</li>
                <li>Informações de cartões (apenas últimos 4 dígitos)</li>
              </ul>

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
                <li>Fornecer e melhorar nossos serviços de gestão financeira</li>
                <li>Categorizar automaticamente suas transações</li>
                <li>Gerar relatórios e análises financeiras personalizadas</li>
                <li>Enviar notificações importantes sobre sua conta</li>
                <li>Prevenir fraudes e atividades ilegais</li>
                <li>Cumprir obrigações legais e regulatórias</li>
                <li>Desenvolver novos recursos baseados em padrões de uso</li>
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
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Pluggy (Open Banking):</strong> Para conexão segura com instituições financeiras</li>
                <li><strong>Processadores de pagamento:</strong> Para processar assinaturas (apenas dados necessários)</li>
                <li><strong>Prestadores de serviço:</strong> Sob rigorosos acordos de confidencialidade</li>
                <li><strong>Autoridades legais:</strong> Quando exigido por lei ou ordem judicial</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">5. Segurança dos Dados</h2>
              <p className="mb-4">Implementamos medidas robustas de segurança:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Criptografia AES-256 para dados em repouso</li>
                <li>TLS 1.3 para dados em trânsito</li>
                <li>Autenticação de dois fatores (2FA)</li>
                <li>Monitoramento 24/7 contra ameaças</li>
                <li>Backups regulares em múltiplas localizações</li>
                <li>Testes de penetração periódicos</li>
                <li>Certificação ISO 27001 (em processo)</li>
              </ul>

              <h2 className="text-xl font-semibold mt-8 mb-4">6. Retenção de Dados</h2>
              <p className="mb-4">Mantemos seus dados pelo tempo necessário:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li><strong>Dados de conta:</strong> Durante a vigência da conta + 5 anos (obrigação legal)</li>
                <li><strong>Dados financeiros:</strong> 5 anos após a última transação</li>
                <li><strong>Logs de acesso:</strong> 6 meses</li>
                <li><strong>Dados de marketing:</strong> Até revogação do consentimento</li>
              </ul>

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
                Para exercer seus direitos, envie um e-mail para: privacidade@caixahub.com.br
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">8. Cookies e Tecnologias Similares</h2>
              <p className="mb-4">Utilizamos cookies para:</p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Manter você conectado à plataforma</li>
                <li>Lembrar suas preferências</li>
                <li>Analisar o uso da plataforma</li>
                <li>Melhorar a performance</li>
              </ul>
              <p className="mb-4">
                Você pode gerenciar cookies nas configurações do seu navegador, mas isso pode afetar 
                a funcionalidade da plataforma.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">9. Menores de Idade</h2>
              <p className="mb-4">
                O CaixaHub não é destinado a menores de 18 anos. Não coletamos intencionalmente 
                dados de menores. Se identificarmos tal coleta, excluiremos os dados imediatamente.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">10. Transferências Internacionais</h2>
              <p className="mb-4">
                Seus dados são processados e armazenados no Brasil. Caso seja necessária transferência 
                internacional, garantiremos proteção adequada conforme a LGPD, incluindo cláusulas 
                contratuais padrão.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">11. Alterações nesta Política</h2>
              <p className="mb-4">
                Podemos atualizar esta política periodicamente. Notificaremos sobre mudanças significativas 
                por e-mail ou através da plataforma com 30 dias de antecedência. O uso continuado após 
                as alterações constitui aceitação da nova política.
              </p>

              <h2 className="text-xl font-semibold mt-8 mb-4">12. Encarregado de Dados (DPO)</h2>
              <p className="mb-4">
                Nosso Encarregado de Proteção de Dados está disponível para esclarecer dúvidas:
              </p>
              <ul className="list-disc ml-6 mb-4 space-y-2">
                <li>Nome: [Nome do DPO]</li>
                <li>E-mail: dpo@caixahub.com.br</li>
                <li>Telefone: (11) 9XXXX-XXXX</li>
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
                <li>E-mail: privacidade@caixahub.com.br</li>
                <li>WhatsApp: (11) 9XXXX-XXXX</li>
                <li>Endereço: [Endereço da empresa]</li>
              </ul>

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