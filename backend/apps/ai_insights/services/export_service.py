"""
Serviço de Exportação para AI Insights
Permite exportar conversas e insights em diferentes formatos
"""
import json
import logging
import csv
from io import StringIO, BytesIO
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from ..models import AIConversation, AIMessage, AIInsight

logger = logging.getLogger(__name__)


class ExportService:
    """Serviço para exportar dados de AI Insights"""
    
    @classmethod
    def export_conversation_to_json(cls, conversation: AIConversation) -> Dict[str, Any]:
        """
        Exporta conversa para formato JSON
        
        Args:
            conversation: Instância da conversa
            
        Returns:
            Dict com dados da conversa
        """
        try:
            messages = conversation.messages.order_by('created_at')
            
            conversation_data = {
                'conversation': {
                    'id': str(conversation.id),
                    'title': conversation.title,
                    'status': conversation.status,
                    'created_at': conversation.created_at.isoformat(),
                    'updated_at': conversation.updated_at.isoformat(),
                    'message_count': conversation.message_count,
                    'total_credits_used': conversation.total_credits_used,
                    'insights_generated': conversation.insights_generated,
                    'company': {
                        'id': str(conversation.company.id),
                        'name': conversation.company.name
                    },
                    'user': {
                        'id': str(conversation.user.id),
                        'email': conversation.user.email,
                        'name': conversation.user.get_full_name()
                    }
                },
                'messages': [
                    {
                        'id': str(msg.id),
                        'role': msg.role,
                        'type': msg.type,
                        'content': msg.content,
                        'credits_used': msg.credits_used,
                        'tokens_used': msg.tokens_used,
                        'model_used': msg.model_used,
                        'structured_data': msg.structured_data,
                        'insights': msg.insights,
                        'helpful': msg.helpful,
                        'user_feedback': msg.user_feedback,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in messages
                ],
                'metadata': {
                    'exported_at': timezone.now().isoformat(),
                    'export_version': '1.0',
                    'total_messages': messages.count()
                }
            }
            
            return conversation_data
            
        except Exception as e:
            logger.error(f"Erro ao exportar conversa para JSON: {str(e)}")
            raise
    
    @classmethod
    def export_conversation_to_csv(cls, conversation: AIConversation) -> str:
        """
        Exporta conversa para formato CSV
        
        Args:
            conversation: Instância da conversa
            
        Returns:
            String CSV
        """
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # Cabeçalho
            writer.writerow([
                'ID Mensagem', 'Papel', 'Tipo', 'Conteúdo', 'Créditos Usados',
                'Tokens Usados', 'Modelo', 'Útil', 'Feedback', 'Data/Hora'
            ])
            
            # Dados
            messages = conversation.messages.order_by('created_at')
            for msg in messages:
                writer.writerow([
                    str(msg.id),
                    msg.role,
                    msg.type,
                    msg.content[:500] + '...' if len(msg.content) > 500 else msg.content,
                    msg.credits_used,
                    msg.tokens_used,
                    msg.model_used,
                    'Sim' if msg.helpful else 'Não' if msg.helpful is False else 'N/A',
                    msg.user_feedback[:200] + '...' if msg.user_feedback and len(msg.user_feedback) > 200 else msg.user_feedback or '',
                    msg.created_at.strftime('%d/%m/%Y %H:%M:%S')
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao exportar conversa para CSV: {str(e)}")
            raise
    
    @classmethod
    def export_conversation_to_pdf(cls, conversation: AIConversation) -> bytes:
        """
        Exporta conversa para formato PDF
        
        Args:
            conversation: Instância da conversa
            
        Returns:
            Bytes do PDF
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Estilo customizado
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor('#2563eb')
            )
            
            user_style = ParagraphStyle(
                'UserMessage',
                parent=styles['Normal'],
                leftIndent=20,
                rightIndent=50,
                fontSize=10,
                textColor=colors.HexColor('#1f2937')
            )
            
            ai_style = ParagraphStyle(
                'AIMessage',
                parent=styles['Normal'],
                leftIndent=50,
                rightIndent=20,
                fontSize=10,
                textColor=colors.HexColor('#059669'),
                backColor=colors.HexColor('#f0fdf4')
            )
            
            story = []
            
            # Título
            story.append(Paragraph(f"Conversa AI: {conversation.title}", title_style))
            story.append(Spacer(1, 20))
            
            # Informações da conversa
            info_data = [
                ['Empresa:', conversation.company.name],
                ['Usuário:', conversation.user.get_full_name()],
                ['Criada em:', conversation.created_at.strftime('%d/%m/%Y %H:%M')],
                ['Total de mensagens:', str(conversation.message_count)],
                ['Créditos utilizados:', str(conversation.total_credits_used)],
                ['Insights gerados:', str(conversation.insights_generated)]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # Mensagens
            story.append(Paragraph("Histórico da Conversa", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            messages = conversation.messages.order_by('created_at')
            for i, msg in enumerate(messages):
                # Cabeçalho da mensagem
                role_text = "👤 Usuário" if msg.role == 'user' else "🤖 Assistente AI"
                timestamp = msg.created_at.strftime('%d/%m/%Y %H:%M')
                
                header_style = ParagraphStyle(
                    'MessageHeader',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.HexColor('#6b7280'),
                    spaceBefore=10,
                    spaceAfter=5
                )
                
                story.append(Paragraph(f"{role_text} - {timestamp}", header_style))
                
                # Conteúdo da mensagem
                content_style = user_style if msg.role == 'user' else ai_style
                
                # Limita conteúdo para não quebrar o PDF
                content = msg.content
                if len(content) > 1000:
                    content = content[:1000] + "... [conteúdo truncado]"
                
                story.append(Paragraph(content, content_style))
                
                # Informações extras para mensagens AI
                if msg.role == 'assistant' and (msg.credits_used or msg.tokens_used):
                    extra_info = f"Créditos: {msg.credits_used} | Tokens: {msg.tokens_used}"
                    if msg.model_used:
                        extra_info += f" | Modelo: {msg.model_used}"
                    
                    extra_style = ParagraphStyle(
                        'ExtraInfo',
                        parent=styles['Normal'],
                        fontSize=8,
                        textColor=colors.HexColor('#9ca3af'),
                        leftIndent=50
                    )
                    
                    story.append(Paragraph(extra_info, extra_style))
                
                story.append(Spacer(1, 10))
                
                # Quebra de página a cada 10 mensagens
                if (i + 1) % 10 == 0 and i < len(messages) - 1:
                    story.append(Spacer(1, 50))
            
            # Rodapé
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#9ca3af'),
                alignment=1  # Centro
            )
            
            story.append(Paragraph(
                f"Exportado em {timezone.now().strftime('%d/%m/%Y %H:%M')} - CaixaHub AI Insights",
                footer_style
            ))
            
            # Gerar PDF
            doc.build(story)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao exportar conversa para PDF: {str(e)}")
            raise
    
    @classmethod
    def export_insights_to_json(cls, insights: List[AIInsight]) -> Dict[str, Any]:
        """
        Exporta insights para formato JSON
        
        Args:
            insights: Lista de insights
            
        Returns:
            Dict com dados dos insights
        """
        try:
            insights_data = {
                'insights': [
                    {
                        'id': str(insight.id),
                        'type': insight.type,
                        'priority': insight.priority,
                        'status': insight.status,
                        'title': insight.title,
                        'description': insight.description,
                        'action_items': insight.action_items,
                        'potential_impact': float(insight.potential_impact) if insight.potential_impact else None,
                        'impact_percentage': float(insight.impact_percentage) if insight.impact_percentage else None,
                        'data_context': insight.data_context,
                        'is_automated': insight.is_automated,
                        'action_taken': insight.action_taken,
                        'action_taken_at': insight.action_taken_at.isoformat() if insight.action_taken_at else None,
                        'actual_impact': float(insight.actual_impact) if insight.actual_impact else None,
                        'user_feedback': insight.user_feedback,
                        'created_at': insight.created_at.isoformat(),
                        'viewed_at': insight.viewed_at.isoformat() if insight.viewed_at else None,
                        'expires_at': insight.expires_at.isoformat() if insight.expires_at else None,
                        'company': {
                            'id': str(insight.company.id),
                            'name': insight.company.name
                        }
                    }
                    for insight in insights
                ],
                'metadata': {
                    'total_insights': len(insights),
                    'by_type': cls._get_insights_stats_by_field(insights, 'type'),
                    'by_priority': cls._get_insights_stats_by_field(insights, 'priority'),
                    'by_status': cls._get_insights_stats_by_field(insights, 'status'),
                    'total_potential_impact': sum(
                        float(i.potential_impact) for i in insights 
                        if i.potential_impact
                    ),
                    'total_actual_impact': sum(
                        float(i.actual_impact) for i in insights 
                        if i.actual_impact
                    ),
                    'exported_at': timezone.now().isoformat(),
                    'export_version': '1.0'
                }
            }
            
            return insights_data
            
        except Exception as e:
            logger.error(f"Erro ao exportar insights para JSON: {str(e)}")
            raise
    
    @classmethod
    def export_insights_to_csv(cls, insights: List[AIInsight]) -> str:
        """
        Exporta insights para formato CSV
        
        Args:
            insights: Lista de insights
            
        Returns:
            String CSV
        """
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # Cabeçalho
            writer.writerow([
                'ID', 'Tipo', 'Prioridade', 'Status', 'Título', 'Descrição',
                'Impacto Potencial (R$)', 'Impacto %', 'Ação Tomada',
                'Impacto Real (R$)', 'Automatizado', 'Criado em',
                'Visualizado em', 'Expira em'
            ])
            
            # Dados
            for insight in insights:
                writer.writerow([
                    str(insight.id),
                    insight.get_type_display(),
                    insight.get_priority_display(),
                    insight.get_status_display(),
                    insight.title,
                    insight.description[:200] + '...' if len(insight.description) > 200 else insight.description,
                    f"R$ {insight.potential_impact:,.2f}" if insight.potential_impact else '',
                    f"{insight.impact_percentage:.1f}%" if insight.impact_percentage else '',
                    'Sim' if insight.action_taken else 'Não',
                    f"R$ {insight.actual_impact:,.2f}" if insight.actual_impact else '',
                    'Sim' if insight.is_automated else 'Não',
                    insight.created_at.strftime('%d/%m/%Y %H:%M'),
                    insight.viewed_at.strftime('%d/%m/%Y %H:%M') if insight.viewed_at else '',
                    insight.expires_at.strftime('%d/%m/%Y') if insight.expires_at else ''
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao exportar insights para CSV: {str(e)}")
            raise
    
    @classmethod
    def _get_insights_stats_by_field(cls, insights: List[AIInsight], field: str) -> Dict[str, int]:
        """Calcula estatísticas por campo"""
        stats = {}
        for insight in insights:
            value = getattr(insight, field)
            stats[value] = stats.get(value, 0) + 1
        return stats
    
    @classmethod
    def create_export_response(
        cls,
        data: Any,
        filename: str,
        content_type: str,
        format_type: str = 'json'
    ) -> HttpResponse:
        """
        Cria resposta HTTP para download
        
        Args:
            data: Dados para exportar
            filename: Nome do arquivo
            content_type: Tipo de conteúdo HTTP
            format_type: Formato de exportação
            
        Returns:
            HttpResponse para download
        """
        try:
            response = HttpResponse(content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            if format_type == 'json':
                response.write(json.dumps(data, ensure_ascii=False, indent=2))
            elif format_type == 'csv':
                response.write(data)
            elif format_type == 'pdf':
                response.write(data)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao criar resposta de exportação: {str(e)}")
            raise