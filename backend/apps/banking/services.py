"""
Banking services for Pluggy integration and data synchronization.
Ref: https://docs.pluggy.ai/docs/creating-an-use-case-from-scratch
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from django.db import transaction
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import (
    Connector, BankConnection, BankAccount,
    Transaction as TransactionModel, SyncLog, Category
)
from .pluggy_client import PluggyClient

User = get_user_model()
logger = logging.getLogger(__name__)


# Load Pluggy categories translations
def load_category_translations() -> Dict[str, str]:
    """
    Load category translations from pluggy_categories.json.
    Returns a dict mapping English category names to Portuguese translations.
    """
    json_path = os.path.join(os.path.dirname(__file__), 'pluggy_categories.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Create mapping: English description -> Portuguese translation
        translations = {}
        for category in data.get('results', []):
            english_name = category.get('description', '')
            portuguese_name = category.get('descriptionTranslated', '')
            if english_name and portuguese_name:
                translations[english_name] = portuguese_name

        logger.info(f"Loaded {len(translations)} category translations")
        return translations
    except Exception as e:
        logger.error(f"Failed to load category translations: {e}")
        return {}


# Global cache for translations
_CATEGORY_TRANSLATIONS = None


def get_category_translations() -> Dict[str, str]:
    """Get cached category translations."""
    global _CATEGORY_TRANSLATIONS
    if _CATEGORY_TRANSLATIONS is None:
        _CATEGORY_TRANSLATIONS = load_category_translations()
    return _CATEGORY_TRANSLATIONS


def get_category_icon(category_name_pt: str) -> str:
    """
    Get the best emoji icon for a category based on its Portuguese name.
    Returns a default icon if category is not found.
    """
    # Mapping of Portuguese category names to emojis
    CATEGORY_ICONS = {
        # Income categories
        'Renda': '💰',
        'Salário': '💵',
        'Aposentadoria': '👴',
        'Atividades de empreendedorismo': '💼',
        'Auxílio do governo': '🏛️',
        'Renda não-recorrente': '💸',
        'Juros de rendimentos de dividendos': '📈',

        # Loans and financing
        'Empréstimos e financiamento': '🏦',
        'Atraso no pagamento e custos de cheque especial': '⚠️',
        'Juros cobrados': '📊',
        'Financiamento': '🏗️',
        'Financiamento imobiliário': '🏠',
        'Financiamento de veículos': '🚗',
        'Empréstimo estudantil': '🎓',
        'Empréstimos': '💳',

        # Investments
        'Investimentos': '📊',
        'Investimento automático': '🤖',
        'Renda fixa': '📉',
        'Fundos multimercado': '📈',
        'Renda variável': '📊',
        'Ajuste de margem': '⚖️',
        'Pensão': '👵',

        # Transfers
        'Transferência mesma titularidade': '🔄',
        'Transferência mesma titularidade - Dinheiro': '💵',
        'Transferência mesma titularidade - PIX': '⚡',
        'Transferência mesma titularidade - TED': '🏦',
        'Transferências': '💸',
        'Transferência - Boleto bancário': '📄',
        'Transferência - Dinheiro': '💵',
        'Transferência - Cheque': '📝',
        'Transferências- DOC': '🏦',
        'Transferência - Câmbio': '💱',
        'Transferência - Mesma instituição': '🏦',
        'Transferência - PIX': '⚡',
        'Transferência - TED': '🏦',
        'Transferências para terceiros': '👥',
        'Transferência para terceiros - Boleto bancário': '📄',
        'Transferência para terceiros - Débito': '💳',
        'Transferência para terceiros - DOC': '🏦',
        'Transferência para terceiros - PIX': '⚡',
        'Transferência para terceiros - TED': '🏦',
        'Pagamento de cartão de crédito': '💳',

        # Legal obligations
        'Obrigações legais': '⚖️',
        'Saldo bloqueado': '🔒',
        'Pensão alimentícia': '👨‍👩‍👧',

        # Services
        'Serviços': '🛠️',
        'Telecomunicação': '📱',
        'Internet': '🌐',
        'Celular': '📱',
        'TV': '📺',
        'Educação': '📚',
        'Cursos online': '💻',
        'Universidade': '🎓',
        'Escola': '🏫',
        'Creche': '👶',
        'Saúde e bem-estar': '💪',
        'Academia e centros de lazer': '🏋️',
        'Prática de esportes': '⚽',
        'Bem-estar': '🧘',
        'Bilhetes': '🎫',
        'Estádios e arenas': '🏟️',
        'Museus e pontos turísticos': '🏛️',
        'Cinema, Teatro e Concertos': '🎭',

        # Shopping
        'Compras': '🛍️',
        'Compras online': '🛒',
        'Eletrônicos': '📱',
        'Pet Shops e veterinários': '🐾',
        'Vestiário': '👔',
        'Artigos infantis': '🧸',
        'Livraria': '📚',
        'Artigos esportivos': '⚽',
        'Papelaria': '✏️',
        'Cashback': '💰',

        # Digital services
        'Serviços digitais': '💻',
        'Jogos e videogames': '🎮',
        'Streaming de vídeo': '📺',
        'Streaming de música': '🎵',

        # Food
        'Supermercado': '🛒',
        'Alimentos e bebidas': '🍽️',
        'Restaurantes, bares e lanchonetes': '🍕',
        'Delivery de alimentos': '🚚',

        # Travel
        'Viagens': '✈️',
        'Aeroportos e cias. aéreas': '✈️',
        'Hospedagem': '🏨',
        'Programas de milhagem': '🎯',
        'Passagem de ônibus': '🚌',

        # Others
        'Doações': '❤️',
        'Apostas': '🎰',
        'Loteria': '🎲',
        'Apostas online': '🎰',

        # Taxes
        'Impostos': '🏛️',
        'Imposto de renda': '💼',
        'Imposto sobre investimentos': '📊',
        'Impostos sobre operações financeiras': '🏦',

        # Bank fees
        'Taxas bancárias': '🏦',
        'Taxas de conta corrente': '💳',
        'Taxas sobre transferências e caixa eletrônico': '🏧',
        'Taxas de cartão de crédito': '💳',

        # Housing
        'Moradia': '🏠',
        'Aluguel': '🔑',
        'Serviços de utilidade pública': '⚡',
        'Água': '💧',
        'Eletricidade': '💡',
        'Gás': '🔥',
        'Utensílios para casa': '🛋️',
        'Impostos sobre moradia': '🏠',

        # Healthcare
        'Saúde': '🏥',
        'Dentista': '🦷',
        'Farmácia': '💊',
        'Ótica': '👓',
        'Hospitais, clínicas e laboratórios': '🏥',

        # Transportation
        'Transporte': '🚗',
        'Táxi e transporte privado urbano': '🚕',
        'Transporte público': '🚌',
        'Aluguel de veículos': '🚗',
        'Aluguel de bicicletas': '🚴',
        'Serviços automotivos': '🔧',
        'Postos de gasolina': '⛽',
        'Estacionamentos': '🅿️',
        'Pedágios e pagamentos no veículo': '🛣️',
        'Taxas e impostos sobre veículos': '🚗',
        'Manutenção de veículos': '🔧',
        'Multas de trânsito': '🚨',

        # Insurance
        'Seguros': '🛡️',
        'Seguro de vida': '❤️',
        'Seguro residencial': '🏠',
        'Seguro saúde': '🏥',
        'Seguro de veículos': '🚗',

        # Leisure
        'Lazer': '🎉',

        # Other
        'Outros': '📁',
    }

    return CATEGORY_ICONS.get(category_name_pt, '📁')


def get_category_color(category_name_pt: str) -> str:
    """
    Get the appropriate color for a category based on its Portuguese name.
    Returns a default color if category is not found.
    Colors are in hex format (#RRGGBB).
    """
    # Mapping of Portuguese category names to colors
    CATEGORY_COLORS = {
        # Income categories - Green tones
        'Renda': '#10b981',  # emerald-500
        'Salário': '#059669',  # emerald-600
        'Aposentadoria': '#047857',  # emerald-700
        'Atividades de empreendedorismo': '#34d399',  # emerald-400
        'Auxílio do governo': '#6ee7b7',  # emerald-300
        'Renda não-recorrente': '#a7f3d0',  # emerald-200
        'Juros de rendimentos de dividendos': '#0891b2',  # cyan-600

        # Loans and financing - Red/Orange tones
        'Empréstimos e financiamento': '#dc2626',  # red-600
        'Atraso no pagamento e custos de cheque especial': '#b91c1c',  # red-700
        'Juros cobrados': '#991b1b',  # red-800
        'Financiamento': '#ea580c',  # orange-600
        'Financiamento imobiliário': '#c2410c',  # orange-700
        'Financiamento de veículos': '#9a3412',  # orange-800
        'Empréstimo estudantil': '#f97316',  # orange-500
        'Empréstimos': '#dc2626',  # red-600

        # Investments - Blue/Cyan tones
        'Investimentos': '#0ea5e9',  # sky-500
        'Investimento automático': '#0284c7',  # sky-600
        'Renda fixa': '#0369a1',  # sky-700
        'Fundos multimercado': '#38bdf8',  # sky-400
        'Renda variável': '#0891b2',  # cyan-600
        'Ajuste de margem': '#06b6d4',  # cyan-500
        'Pensão': '#0e7490',  # cyan-700

        # Transfers - Indigo/Purple tones
        'Transferência mesma titularidade': '#6366f1',  # indigo-500
        'Transferência mesma titularidade - Dinheiro': '#4f46e5',  # indigo-600
        'Transferência mesma titularidade - PIX': '#8b5cf6',  # violet-500
        'Transferência mesma titularidade - TED': '#7c3aed',  # violet-600
        'Transferências': '#6366f1',  # indigo-500
        'Transferência - Boleto bancário': '#818cf8',  # indigo-400
        'Transferência - Dinheiro': '#4f46e5',  # indigo-600
        'Transferência - Cheque': '#4338ca',  # indigo-700
        'Transferências- DOC': '#3730a3',  # indigo-800
        'Transferência - Câmbio': '#a78bfa',  # violet-400
        'Transferência - Mesma instituição': '#6366f1',  # indigo-500
        'Transferência - PIX': '#8b5cf6',  # violet-500
        'Transferência - TED': '#7c3aed',  # violet-600
        'Transferências para terceiros': '#6366f1',  # indigo-500
        'Transferência para terceiros - Boleto bancário': '#818cf8',  # indigo-400
        'Transferência para terceiros - Débito': '#a78bfa',  # violet-400
        'Transferência para terceiros - DOC': '#4338ca',  # indigo-700
        'Transferência para terceiros - PIX': '#8b5cf6',  # violet-500
        'Transferência para terceiros - TED': '#7c3aed',  # violet-600
        'Pagamento de cartão de crédito': '#ec4899',  # pink-500

        # Legal obligations - Gray tones
        'Obrigações legais': '#64748b',  # slate-500
        'Saldo bloqueado': '#475569',  # slate-600
        'Pensão alimentícia': '#334155',  # slate-700

        # Services - Teal tones
        'Serviços': '#14b8a6',  # teal-500
        'Telecomunicação': '#0d9488',  # teal-600
        'Internet': '#0f766e',  # teal-700
        'Celular': '#2dd4bf',  # teal-400
        'TV': '#5eead4',  # teal-300
        'Educação': '#f59e0b',  # amber-500
        'Cursos online': '#d97706',  # amber-600
        'Universidade': '#b45309',  # amber-700
        'Escola': '#92400e',  # amber-800
        'Creche': '#fbbf24',  # amber-400
        'Saúde e bem-estar': '#8b5cf6',  # violet-500
        'Academia e centros de lazer': '#a78bfa',  # violet-400
        'Prática de esportes': '#7c3aed',  # violet-600
        'Bem-estar': '#c4b5fd',  # violet-300
        'Bilhetes': '#ec4899',  # pink-500
        'Estádios e arenas': '#db2777',  # pink-600
        'Museus e pontos turísticos': '#be185d',  # pink-700
        'Cinema, Teatro e Concertos': '#f472b6',  # pink-400

        # Shopping - Pink/Rose tones
        'Compras': '#ec4899',  # pink-500
        'Compras online': '#db2777',  # pink-600
        'Eletrônicos': '#be185d',  # pink-700
        'Pet Shops e veterinários': '#f472b6',  # pink-400
        'Vestiário': '#f9a8d4',  # pink-300
        'Artigos infantis': '#fbcfe8',  # pink-200
        'Livraria': '#be185d',  # pink-700
        'Artigos esportivos': '#db2777',  # pink-600
        'Papelaria': '#ec4899',  # pink-500
        'Cashback': '#10b981',  # emerald-500

        # Digital services - Purple tones
        'Serviços digitais': '#a855f7',  # purple-500
        'Jogos e videogames': '#9333ea',  # purple-600
        'Streaming de vídeo': '#7e22ce',  # purple-700
        'Streaming de música': '#c084fc',  # purple-400

        # Food - Orange/Yellow tones
        'Supermercado': '#f59e0b',  # amber-500
        'Alimentos e bebidas': '#f97316',  # orange-500
        'Restaurantes, bares e lanchonetes': '#ea580c',  # orange-600
        'Delivery de alimentos': '#fb923c',  # orange-400

        # Travel - Sky blue tones
        'Viagens': '#0ea5e9',  # sky-500
        'Aeroportos e cias. aéreas': '#0284c7',  # sky-600
        'Hospedagem': '#0369a1',  # sky-700
        'Programas de milhagem': '#38bdf8',  # sky-400
        'Passagem de ônibus': '#7dd3fc',  # sky-300

        # Others - Various
        'Doações': '#ef4444',  # red-500
        'Apostas': '#dc2626',  # red-600
        'Loteria': '#b91c1c',  # red-700
        'Apostas online': '#dc2626',  # red-600

        # Taxes - Gray/Red tones
        'Impostos': '#64748b',  # slate-500
        'Imposto de renda': '#475569',  # slate-600
        'Imposto sobre investimentos': '#334155',  # slate-700
        'Impostos sobre operações financeiras': '#1e293b',  # slate-800

        # Bank fees - Slate tones
        'Taxas bancárias': '#64748b',  # slate-500
        'Taxas de conta corrente': '#475569',  # slate-600
        'Taxas sobre transferências e caixa eletrônico': '#334155',  # slate-700
        'Taxas de cartão de crédito': '#1e293b',  # slate-800

        # Housing - Brown/Amber tones
        'Moradia': '#92400e',  # amber-800
        'Aluguel': '#78350f',  # amber-900
        'Serviços de utilidade pública': '#b45309',  # amber-700
        'Água': '#06b6d4',  # cyan-500
        'Eletricidade': '#fbbf24',  # amber-400
        'Gás': '#f97316',  # orange-500
        'Utensílios para casa': '#d97706',  # amber-600
        'Impostos sobre moradia': '#92400e',  # amber-800

        # Healthcare - Red/Rose tones
        'Saúde': '#ef4444',  # red-500
        'Dentista': '#dc2626',  # red-600
        'Farmácia': '#b91c1c',  # red-700
        'Ótica': '#f87171',  # red-400
        'Hospitais, clínicas e laboratórios': '#991b1b',  # red-800

        # Transportation - Lime/Green tones
        'Transporte': '#84cc16',  # lime-500
        'Táxi e transporte privado urbano': '#65a30d',  # lime-600
        'Transporte público': '#4d7c0f',  # lime-700
        'Aluguel de veículos': '#a3e635',  # lime-400
        'Aluguel de bicicletas': '#bef264',  # lime-300
        'Serviços automotivos': '#65a30d',  # lime-600
        'Postos de gasolina': '#4d7c0f',  # lime-700
        'Estacionamentos': '#84cc16',  # lime-500
        'Pedágios e pagamentos no veículo': '#a3e635',  # lime-400
        'Taxas e impostos sobre veículos': '#4d7c0f',  # lime-700
        'Manutenção de veículos': '#65a30d',  # lime-600
        'Multas de trânsito': '#dc2626',  # red-600

        # Insurance - Blue tones
        'Seguros': '#3b82f6',  # blue-500
        'Seguro de vida': '#2563eb',  # blue-600
        'Seguro residencial': '#1d4ed8',  # blue-700
        'Seguro saúde': '#60a5fa',  # blue-400
        'Seguro de veículos': '#93c5fd',  # blue-300

        # Leisure - Yellow tones
        'Lazer': '#eab308',  # yellow-500

        # Other
        'Outros': '#6b7280',  # gray-500
    }

    return CATEGORY_COLORS.get(category_name_pt, '#d946ef')


def get_or_create_category(user: User, category_name: str, transaction_type: str) -> Optional[Category]:
    """
    Get or create a category for a user based on the Pluggy category name.
    Automatically translates category names to Portuguese.

    Args:
        user: The user who owns the category
        category_name: The category name from Pluggy (in English)
        transaction_type: 'CREDIT' or 'DEBIT' to determine category type

    Returns:
        Category instance or None if category_name is empty
    """
    if not category_name or not category_name.strip():
        return None

    category_name = category_name.strip()

    # Get translation for the category name
    translations = get_category_translations()
    translated_name = translations.get(category_name, category_name)

    # Map transaction type to category type
    category_type = 'income' if transaction_type == 'CREDIT' else 'expense'

    # Try to get existing category (case-insensitive, by translated name)
    category = Category.objects.filter(
        user=user,
        name__iexact=translated_name,
        type=category_type
    ).first()

    if not category:
        # Get the appropriate emoji and color for this category
        category_icon = get_category_icon(translated_name)
        category_color = get_category_color(translated_name)

        # Create new category with translated name, appropriate icon and color
        category = Category.objects.create(
            user=user,
            name=translated_name,
            type=category_type,
            color=category_color,
            icon=category_icon,
            is_system=False
        )
        logger.info(f"Created new category '{translated_name}' {category_icon} ({category_type}) for user {user.id}")

    return category


class ConnectorService:
    """
    Service for managing bank connectors.
    Ref: https://docs.pluggy.ai/reference/connectors
    """

    def __init__(self):
        self.client = PluggyClient()

    def sync_connectors(self, country: str = 'BR', sandbox: Optional[bool] = None) -> int:
        """
        Sync available connectors from Pluggy.
        Returns the number of connectors synced.
        """
        sync_log = SyncLog.objects.create(
            sync_type='CONNECTORS',
            status='IN_PROGRESS'
        )

        try:
            pluggy_connectors = self.client.get_connectors(country=country, sandbox=sandbox)
            synced_count = 0

            for pluggy_connector in pluggy_connectors:
                connector, created = Connector.objects.update_or_create(
                    pluggy_id=pluggy_connector['id'],
                    defaults={
                        'name': pluggy_connector['name'],
                        'institution_name': pluggy_connector.get('institutionName', ''),
                        'institution_url': pluggy_connector.get('institutionUrl', ''),
                        'country': pluggy_connector.get('countries', ['BR'])[0],
                        'primary_color': pluggy_connector.get('primaryColor', ''),
                        'logo_url': pluggy_connector.get('logoUrl', ''),
                        'type': pluggy_connector.get('type', 'PERSONAL_BANK'),
                        'credentials_schema': pluggy_connector.get('credentials', {}),
                        'supports_mfa': pluggy_connector.get('hasMfa', False),
                        'is_sandbox': pluggy_connector.get('isSandbox', False),
                        'is_active': pluggy_connector.get('isEnabled', True),
                    }
                )
                synced_count += 1

            sync_log.status = 'SUCCESS'
            sync_log.completed_at = timezone.now()
            sync_log.records_synced = synced_count
            sync_log.save()

            logger.info(f"Synced {synced_count} connectors")
            return synced_count

        except Exception as e:
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Failed to sync connectors: {e}")
            raise

    def get_active_connectors(self, country: str = 'BR') -> List[Connector]:
        """Get all active connectors for a country."""
        return Connector.objects.filter(
            country=country,
            is_active=True
        ).order_by('name')


class BankConnectionService:
    """
    Service for managing bank connections (Items in Pluggy).
    Ref: https://docs.pluggy.ai/docs/connect-an-account
    """

    def __init__(self):
        self.client = PluggyClient()

    def create_connection_from_item(self, user: User, item_id: str) -> BankConnection:
        """
        Create a connection from an existing Pluggy item (after widget auth).
        Ref: https://docs.pluggy.ai/docs/connect-widget-overview
        """
        logger.info(f"Creating connection from item {item_id} for user {user.id}")

        try:
            # Check if connection already exists
            existing = BankConnection.objects.filter(
                pluggy_item_id=item_id,
                user=user
            ).first()

            if existing:
                logger.info(f"Connection already exists for item {item_id}")
                return existing

            logger.info(f"Fetching item details from Pluggy for item {item_id}")
            # Get item details from Pluggy
            pluggy_item = self.client.get_item(item_id)
            logger.info(f"Pluggy item retrieved: {pluggy_item}")

            # Get connector
            connector = Connector.objects.filter(
                pluggy_id=pluggy_item['connector']['id']
            ).first()

            if not connector:
                # Try to sync connectors and get again
                connector_service = ConnectorService()
                connector_service.sync_connectors()
                connector = Connector.objects.filter(
                    pluggy_id=pluggy_item['connector']['id']
                ).first()

            if not connector:
                raise ValueError(f"Connector {pluggy_item['connector']['id']} not found")

            # Create local connection record
            connection = BankConnection.objects.create(
                user=user,
                connector=connector,
                pluggy_item_id=item_id,
                status=pluggy_item['status'],
                status_detail=pluggy_item.get('statusDetail'),
                execution_status=pluggy_item.get('executionStatus', ''),
                last_updated_at=timezone.now()
            )

            # If connection is ready, sync accounts
            if connection.status == 'UPDATED':
                self.sync_accounts(connection)

            logger.info(f"Created bank connection {connection.id} from item {item_id}")
            return connection

        except Exception as e:
            logger.error(f"Failed to create connection from item: {e}")
            raise

    def create_connection(self, user: User, connector_id: int,
                         credentials: Dict[str, str]) -> BankConnection:
        """
        Create a new bank connection for a user.
        Ref: https://docs.pluggy.ai/reference/items-create
        """
        try:
            connector = Connector.objects.get(pluggy_id=connector_id)

            # Build webhook URL
            webhook_url = None
            if hasattr(settings, 'WEBHOOK_BASE_URL'):
                webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/banking/webhooks/pluggy/"

            # Create item in Pluggy
            pluggy_item = self.client.create_item(
                connector_id=connector_id,
                credentials=credentials,
                webhook_url=webhook_url,
                user_data={'id': str(user.id), 'email': user.email}
            )

            # Create local connection record
            connection = BankConnection.objects.create(
                user=user,
                connector=connector,
                pluggy_item_id=pluggy_item['id'],
                status='UPDATING',
                webhook_url=webhook_url or ''
            )

            logger.info(f"Created bank connection {connection.id} for user {user.id}")
            return connection

        except Connector.DoesNotExist:
            logger.error(f"Connector {connector_id} not found")
            raise ValueError(f"Connector {connector_id} not found")
        except Exception as e:
            logger.error(f"Failed to create bank connection: {e}")
            raise

    def update_connection_status(self, connection: BankConnection) -> BankConnection:
        """
        Update connection status from Pluggy.
        Ref: https://docs.pluggy.ai/reference/items-retrieve
        """
        try:
            pluggy_item = self.client.get_item(connection.pluggy_item_id)

            connection.status = pluggy_item['status']
            connection.status_detail = pluggy_item.get('statusDetail')
            connection.execution_status = pluggy_item.get('executionStatus', '')
            connection.last_updated_at = timezone.now()
            connection.save()

            # If connection is ready, sync accounts
            if connection.status == 'UPDATED':
                self.sync_accounts(connection)

            return connection

        except Exception as e:
            logger.error(f"Failed to update connection status: {e}")
            raise

    def trigger_manual_sync(self, connection: BankConnection) -> Dict:
        """
        Trigger a manual synchronization for a connection.
        This updates the item in Pluggy to fetch new data from the financial institution.

        Returns:
            Dict with sync status and any required actions
        """
        try:
            logger.info(f"Triggering manual sync for connection {connection.id}")

            # First, check current item status
            current_item = self.client.get_item(connection.pluggy_item_id)
            current_status = current_item['status']

            logger.info(f"Current item status: {current_status}")

            # Handle different status scenarios
            if current_status == 'WAITING_USER_INPUT':
                # MFA is required
                parameter = current_item.get('parameter', {})
                logger.warning(f"Item requires MFA. Parameter: {parameter}")
                return {
                    'status': 'MFA_REQUIRED',
                    'message': 'Multi-factor authentication required',
                    'parameter': parameter,
                    'item_status': current_status
                }

            elif current_status == 'LOGIN_ERROR':
                # Credentials are invalid
                logger.warning(f"Item has login error. Need to update credentials.")
                return {
                    'status': 'CREDENTIALS_REQUIRED',
                    'message': 'Invalid credentials, please reconnect',
                    'item_status': current_status
                }

            elif current_status in ['UPDATED', 'OUTDATED']:
                # Item can be updated - trigger sync
                logger.info(f"Triggering item update for sync")
                updated_item = self.client.trigger_item_update(connection.pluggy_item_id)

                # Update local status
                connection.status = updated_item['status']
                connection.status_detail = updated_item.get('statusDetail')
                connection.execution_status = updated_item.get('executionStatus', '')
                connection.last_updated_at = timezone.now()
                connection.save()

                return {
                    'status': 'SYNC_TRIGGERED',
                    'message': 'Synchronization started successfully',
                    'item_status': updated_item['status']
                }

            elif current_status == 'UPDATING':
                # Already updating
                logger.info(f"Item is already updating")
                return {
                    'status': 'ALREADY_SYNCING',
                    'message': 'Synchronization already in progress',
                    'item_status': current_status
                }

            else:
                # Unknown status
                logger.warning(f"Unknown item status: {current_status}")
                return {
                    'status': 'UNKNOWN',
                    'message': f'Unknown item status: {current_status}',
                    'item_status': current_status
                }

        except Exception as e:
            logger.error(f"Failed to trigger manual sync: {e}")
            raise

    def sync_accounts(self, connection: BankConnection) -> int:
        """
        Sync accounts for a connection.
        Ref: https://docs.pluggy.ai/reference/accounts-list
        """
        try:
            pluggy_accounts = self.client.get_accounts(connection.pluggy_item_id)
            synced_count = 0

            for pluggy_account in pluggy_accounts:
                account_type = self._map_account_type(pluggy_account.get('type', 'BANK'))
                pluggy_type = pluggy_account.get('type', 'BANK')

                # Prepare default fields
                defaults = {
                    'connection': connection,
                    'type': account_type,
                    'subtype': pluggy_account.get('subtype', ''),
                    'name': pluggy_account.get('name', ''),
                    'number': pluggy_account.get('number', ''),
                    'balance': Decimal(str(pluggy_account.get('balance', 0))),
                    'currency_code': pluggy_account.get('currencyCode', 'BRL'),
                    'bank_data': pluggy_account.get('bankData') or {},
                    'last_synced_at': timezone.now(),
                }

                # Handle credit card specific fields
                if pluggy_type == 'CREDIT':
                    credit_data = pluggy_account.get('creditData') or {}
                    defaults['credit_data'] = credit_data
                    defaults['available_credit_limit'] = Decimal(str(credit_data.get('availableCreditLimit', 0)))
                    defaults['credit_limit'] = Decimal(str(credit_data.get('creditLimit', 0)))
                    logger.info(f"Credit card synced - Available: {defaults['available_credit_limit']}, Total: {defaults['credit_limit']}, Balance: {defaults['balance']}")
                else:
                    # For non-credit accounts, clear credit fields
                    defaults['credit_data'] = {}
                    defaults['available_credit_limit'] = None
                    defaults['credit_limit'] = None

                BankAccount.objects.update_or_create(
                    pluggy_account_id=pluggy_account['id'],
                    defaults=defaults
                )
                synced_count += 1

            logger.info(f"Synced {synced_count} accounts for connection {connection.id}")
            return synced_count

        except Exception as e:
            logger.error(f"Failed to sync accounts: {e}")
            raise

    def delete_connection(self, connection: BankConnection) -> bool:
        """
        Delete a bank connection and all associated data.
        Ref: https://docs.pluggy.ai/reference/items-delete
        """
        try:
            # Delete from Pluggy first
            try:
                self.client.delete_item(connection.pluggy_item_id)
            except Exception as pluggy_error:
                logger.warning(f"Failed to delete from Pluggy: {pluggy_error}")
                # Continue with local deletion even if Pluggy deletion fails

            # Store connection ID for logging
            connection_id = connection.id

            # Delete from database (will cascade delete accounts and transactions)
            connection.delete()

            logger.info(f"Deleted connection {connection_id} and all associated data")
            return True

        except Exception as e:
            logger.error(f"Failed to delete connection: {e}")
            return False

    def _map_account_type(self, pluggy_type: str) -> str:
        """Map Pluggy account type to our model choices."""
        mapping = {
            'BANK': 'CHECKING',
            'CHECKING': 'CHECKING',
            'SAVINGS': 'SAVINGS',
            'CREDIT_CARD': 'CREDIT_CARD',
            'LOAN': 'LOAN',
            'INVESTMENT': 'INVESTMENT',
        }
        return mapping.get(pluggy_type, 'CHECKING')


class TransactionService:
    """
    Service for managing transactions.
    Ref: https://docs.pluggy.ai/reference/transactions
    """

    def __init__(self):
        self.client = PluggyClient()

    def sync_transactions(self, account: BankAccount,
                         days_back: int = 90,
                         trigger_update: bool = True) -> int:
        """
        Sync transactions for an account.
        By default, triggers an item update first to get fresh data.
        Ref: https://docs.pluggy.ai/reference/transactions-list

        Args:
            account: The bank account to sync
            days_back: How many days of transactions to sync
            trigger_update: Whether to trigger item update before syncing (default: True)
        """
        sync_log = SyncLog.objects.create(
            connection=account.connection,
            sync_type='TRANSACTIONS',
            status='IN_PROGRESS',
            details={'account_id': str(account.id)}
        )

        try:
            # Trigger item update for manual syncs to get fresh data
            if trigger_update:
                logger.info(f"Triggering item update before syncing transactions for account {account.id}")
                connection_service = BankConnectionService()
                sync_status = connection_service.trigger_manual_sync(account.connection)

                if sync_status['status'] == 'MFA_REQUIRED':
                    sync_log.status = 'FAILED'
                    sync_log.error_message = 'MFA required for sync'
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                    raise ValueError('MFA required. Please complete authentication through the app.')

                elif sync_status['status'] == 'CREDENTIALS_REQUIRED':
                    sync_log.status = 'FAILED'
                    sync_log.error_message = 'Invalid credentials'
                    sync_log.completed_at = timezone.now()
                    sync_log.save()
                    raise ValueError('Invalid credentials. Please reconnect your account.')

                elif sync_status['status'] not in ['SYNC_TRIGGERED', 'ALREADY_SYNCING']:
                    logger.warning(f"Unexpected sync status: {sync_status}")

                # Wait a moment for the update to start processing
                import time
                time.sleep(2)

            date_from = timezone.now() - timedelta(days=days_back)
            date_to = timezone.now()

            pluggy_transactions = self.client.get_transactions(
                account_id=account.pluggy_account_id,
                date_from=date_from,
                date_to=date_to
            )

            synced_count = 0
            with transaction.atomic():
                for pluggy_tx in pluggy_transactions:
                    tx_type = 'CREDIT' if pluggy_tx['type'] == 'CREDIT' else 'DEBIT'

                    # Get merchant info safely - ensure we never pass None
                    merchant = pluggy_tx.get('merchant') or {}
                    merchant_name = merchant.get('name', '') if merchant else ''
                    merchant_category = merchant.get('category', '') if merchant else ''

                    # Ensure merchant fields are never None
                    merchant_name = merchant_name if merchant_name is not None else ''
                    merchant_category = merchant_category if merchant_category is not None else ''

                    # Ensure all string fields are never None
                    description = pluggy_tx.get('description', '')
                    description = description if description is not None else ''

                    pluggy_category = pluggy_tx.get('category', '')
                    pluggy_category = pluggy_category if pluggy_category is not None else ''

                    pluggy_category_id = pluggy_tx.get('categoryId', '')
                    pluggy_category_id = pluggy_category_id if pluggy_category_id is not None else ''

                    # Get or create category for this transaction
                    user = account.connection.user
                    category = get_or_create_category(user, pluggy_category, tx_type)

                    TransactionModel.objects.update_or_create(
                        pluggy_transaction_id=pluggy_tx['id'],
                        defaults={
                            'account': account,
                            'type': tx_type,
                            'description': description,
                            'amount': abs(Decimal(str(pluggy_tx.get('amount', 0)))),
                            'currency_code': pluggy_tx.get('currencyCode', 'BRL'),
                            'date': datetime.fromisoformat(pluggy_tx['date'].replace('Z', '+00:00')),
                            'pluggy_category': pluggy_category,
                            'pluggy_category_id': pluggy_category_id,
                            'merchant_name': merchant_name,
                            'merchant_category': merchant_category,
                            'payment_data': pluggy_tx.get('paymentData'),
                            'user_category': category,  # Assign the auto-created category
                        }
                    )
                    synced_count += 1

            account.last_synced_at = timezone.now()
            account.save()

            sync_log.status = 'SUCCESS'
            sync_log.completed_at = timezone.now()
            sync_log.records_synced = synced_count
            sync_log.save()

            logger.info(f"Synced {synced_count} transactions for account {account.id}")
            return synced_count

        except Exception as e:
            sync_log.status = 'FAILED'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            logger.error(f"Failed to sync transactions: {e}")
            raise

    def sync_all_accounts_transactions(self, connection: BankConnection,
                                      trigger_update: bool = True) -> Dict[str, int]:
        """
        Sync transactions for all accounts in a connection.

        Args:
            connection: The bank connection
            trigger_update: Whether to trigger item update before syncing (default: True)
        """
        results = {}

        # Only trigger update once for the connection, not for each account
        if trigger_update:
            logger.info(f"Triggering item update for connection {connection.id}")
            connection_service = BankConnectionService()
            sync_status = connection_service.trigger_manual_sync(connection)

            if sync_status['status'] == 'MFA_REQUIRED':
                raise ValueError('MFA required. Please complete authentication through the app.')
            elif sync_status['status'] == 'CREDENTIALS_REQUIRED':
                raise ValueError('Invalid credentials. Please reconnect your account.')

            # Wait for update to process
            import time
            time.sleep(3)

        for account in connection.accounts.filter(is_active=True):
            try:
                # Don't trigger update again since we did it for the connection
                count = self.sync_transactions(account, trigger_update=False)
                results[str(account.id)] = count
            except Exception as e:
                logger.error(f"Failed to sync transactions for account {account.id}: {e}")
                results[str(account.id)] = 0

        return results
