"""
Email service for sending notifications
"""
import logging
from typing import List, Dict, Any, Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)


class EmailService:
    """Service for handling email notifications"""
    
    @staticmethod
    def send_email(
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        recipient_list: List[str],
        from_email: Optional[str] = None
    ) -> bool:
        """Send an email using a template"""
        try:
            # Use default from email if not provided
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            
            # Render email templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send(fail_silently=False)
            
            logger.info(f"Email sent successfully to {recipient_list}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, reset_url: str) -> bool:
        """Send password reset email"""
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject='Redefinir Sua Senha',
            template_name='password_reset',
            context=context,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_verification_email(user, verification_url: str) -> bool:
        """Send email verification"""
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject='Verifique Seu Endereço de E-mail',
            template_name='email_verification',
            context=context,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_invitation_email(email: str, inviter, company, invitation_url: str) -> bool:
        """Send company invitation email"""
        context = {
            'inviter': inviter,
            'company': company,
            'invitation_url': invitation_url,
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject=f'{inviter.get_full_name()} convidou você para participar de {company.name}',
            template_name='company_invitation',
            context=context,
            recipient_list=[email]
        )
    
    @staticmethod
    def send_report_ready_email(user, report) -> bool:
        """Send report ready notification"""
        context = {
            'user': user,
            'report': report,
            'download_url': f"{settings.FRONTEND_URL}/reports/{report.id}/download",
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject='Seu Relatório está Pronto',
            template_name='report_ready',
            context=context,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_bank_connection_error_email(user, bank_name: str, error_message: str) -> bool:
        """Send bank connection error notification"""
        context = {
            'user': user,
            'bank_name': bank_name,
            'error_message': error_message,
            'reconnect_url': f"{settings.FRONTEND_URL}/accounts",
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject=f'Problema com sua conexão {bank_name}',
            template_name='bank_connection_error',
            context=context,
            recipient_list=[user.email]
        )
    
    @staticmethod
    def send_subscription_confirmation_email(user, plan) -> bool:
        """Send subscription confirmation"""
        context = {
            'user': user,
            'plan': plan,
            'manage_url': f"{settings.FRONTEND_URL}/settings/subscription",
            'site_name': 'Caixa Digital',
            'support_email': 'suporte@caixadigital.com.br'
        }
        
        return EmailService.send_email(
            subject='Assinatura Confirmada',
            template_name='subscription_confirmation',
            context=context,
            recipient_list=[user.email]
        )


# Celery tasks for async email sending
@shared_task
def send_email_task(
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    recipient_list: List[str],
    from_email: Optional[str] = None
):
    """Async task to send email"""
    return EmailService.send_email(
        subject=subject,
        template_name=template_name,
        context=context,
        recipient_list=recipient_list,
        from_email=from_email
    )


@shared_task
def send_password_reset_email_task(user_id: int, reset_url: str):
    """Async task to send password reset email"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        return EmailService.send_password_reset_email(user, reset_url)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email")
        return False


@shared_task
def send_verification_email_task(user_id: int, verification_url: str):
    """Async task to send verification email"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        return EmailService.send_verification_email(user, verification_url)
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for verification email")
        return False