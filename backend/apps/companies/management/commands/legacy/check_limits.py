"""
Management command to check usage limits
Place this file at: backend/apps/companies/management/commands/check_limits.py
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from apps.companies.models import Company, CompanyUser


class Command(BaseCommand):
    help = 'Verifica empresas próximas aos limites de uso e envia alertas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=80,
            help='Percentual de uso para considerar como alerta (default: 80%)'
        )
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Enviar alertas por email para as empresas'
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        send_alerts = options['send_alerts']
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"VERIFICAÇÃO DE LIMITES DE USO")
        self.stdout.write(f"Limite de alerta: {threshold}%")
        self.stdout.write(f"{'='*60}\n")
        
        companies_checked = 0
        alerts_found = 0
        alerts_by_type = {
            'transactions': [],
            'bank_accounts': [],
            'users': [],
            'ai_requests': []
        }
        
        # Verificar todas as empresas ativas
        for company in Company.objects.filter(
            Q(subscription_status='active') | Q(subscription_status='trial'),
            subscription_plan__isnull=False,
            is_active=True
        ).select_related('subscription_plan', 'owner'):
            companies_checked += 1
            company_has_alert = False
            
            # Obter resumo de uso
            usage_summary = company.get_usage_summary()
            
            # Verificar cada tipo de limite
            for resource, data in usage_summary.items():
                if data['percentage'] >= threshold:
                    company_has_alert = True
                    alerts_found += 1
                    
                    alert_info = {
                        'company': company,
                        'resource': resource,
                        'used': data['used'],
                        'limit': data['limit'],
                        'percentage': data['percentage']
                    }
                    
                    alerts_by_type[resource].append(alert_info)
                    
                    # Mostrar alerta
                    self._display_alert(alert_info)
                    
                    # Enviar email se solicitado
                    if send_alerts and data['percentage'] >= 90:
                        self._send_email_alert(company, resource, data)
            
            # Verificar limites específicos que podem bloquear
            if company_has_alert:
                self._check_critical_limits(company)
        
        # Resumo
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"RESUMO DA VERIFICAÇÃO")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Empresas verificadas: {companies_checked}")
        self.stdout.write(f"Alertas encontrados: {alerts_found}")
        
        # Detalhamento por tipo
        self.stdout.write("\nAlertas por tipo de recurso:")
        for resource_type, alerts in alerts_by_type.items():
            if alerts:
                self.stdout.write(
                    f"  - {resource_type}: {len(alerts)} empresas"
                )
        
        # Empresas mais críticas
        self._show_critical_companies(alerts_by_type)
        
        if send_alerts:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Alertas enviados para empresas com uso acima de 90%"
                )
            )
    
    def _display_alert(self, alert_info):
        """Exibe um alerta formatado"""
        company = alert_info['company']
        resource = alert_info['resource']
        percentage = alert_info['percentage']
        
        # Definir cor baseada na severidade
        if percentage >= 100:
            style = self.style.ERROR
            icon = "🚫"
        elif percentage >= 90:
            style = self.style.WARNING
            icon = "⚠️"
        else:
            style = self.style.NOTICE
            icon = "📊"
        
        resource_names = {
            'transactions': 'Transações',
            'bank_accounts': 'Contas Bancárias',
            'users': 'Usuários',
            'ai_requests': 'Requisições IA'
        }
        
        self.stdout.write(
            style(
                f"{icon} {company.name}: "
                f"{resource_names.get(resource, resource)} em {percentage:.0f}% "
                f"({alert_info['used']}/{alert_info['limit']})"
            )
        )
    
    def _check_critical_limits(self, company):
        """Verifica se algum limite foi completamente atingido"""
        critical_limits = []
        
        # Verificar cada tipo de limite
        limit_types = ['transactions', 'bank_accounts', 'users', 'ai_requests']
        
        for limit_type in limit_types:
            is_at_limit, usage_info = company.check_plan_limits(limit_type)
            if is_at_limit:
                critical_limits.append(usage_info)
        
        if critical_limits:
            self.stdout.write(
                self.style.ERROR(
                    f"    ❌ LIMITES ATINGIDOS: {', '.join(critical_limits)}"
                )
            )
            self.stdout.write(
                "    → Recomendação: Fazer upgrade do plano"
            )
    
    def _show_critical_companies(self, alerts_by_type):
        """Mostra as empresas mais críticas"""
        # Coletar todas as empresas com alertas acima de 90%
        critical_companies = []
        
        for resource_type, alerts in alerts_by_type.items():
            for alert in alerts:
                if alert['percentage'] >= 90:
                    critical_companies.append(alert)
        
        if critical_companies:
            # Ordenar por percentual (mais crítico primeiro)
            critical_companies.sort(
                key=lambda x: x['percentage'], 
                reverse=True
            )
            
            self.stdout.write(
                self.style.WARNING(
                    f"\n🚨 EMPRESAS CRÍTICAS (>90% de uso):"
                )
            )
            
            for alert in critical_companies[:10]:  # Top 10
                company = alert['company']
                self.stdout.write(
                    f"  - {company.name} ({company.owner.email}): "
                    f"{alert['resource']} em {alert['percentage']:.0f}%"
                )
                
                # Mostrar plano atual e sugestão de upgrade
                current_plan = company.subscription_plan
                if current_plan:
                    self.stdout.write(
                        f"    Plano atual: {current_plan.name} | "
                        f"Status: {company.get_subscription_status_display()}"
                    )
    
    def _send_email_alert(self, company, resource, usage_data):
        """Envia alerta por email (placeholder para implementação real)"""
        # Aqui você integraria com seu serviço de email
        # Por exemplo: EmailService.send_usage_limit_warning(...)
        
        self.stdout.write(
            f"  📧 Email enviado para {company.owner.email} sobre {resource}"
        )