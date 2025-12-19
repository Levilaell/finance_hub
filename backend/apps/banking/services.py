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

from django.db import transaction as transaction_db
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

# Note: 'transaction_db' is used instead of 'transaction' to avoid
# confusion with the Transaction model (TransactionModel)


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
        'Dividendos e Rendimentos': '📈',

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
        'Transferência - DOC': '🏦',
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
        'Roupas': '👔',
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
        'Dividendos e Rendimentos': '#0891b2',  # cyan-600

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
        'Transferência - DOC': '#3730a3',  # indigo-800
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
        'Roupas': '#f9a8d4',  # pink-300
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
            'CREDIT': 'CREDIT_CARD',  # Pluggy sends 'CREDIT' for credit cards
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
            new_transactions = []  # Track new transactions for auto-match
            with transaction_db.atomic():
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

                    # Check if transaction already exists (to preserve user_category)
                    user = account.connection.user
                    existing_tx = TransactionModel.objects.filter(
                        pluggy_transaction_id=pluggy_tx['id']
                    ).first()

                    # Determine category to use
                    if existing_tx and existing_tx.user_category:
                        # Preserve existing user category (was manually categorized)
                        category_to_use = existing_tx.user_category
                    else:
                        # New transaction - try to apply category rules first
                        temp_tx = TransactionModel(
                            description=description,
                            merchant_name=merchant_name,
                            type=tx_type,
                            account=account
                        )
                        rule_category = CategoryRuleService.apply_rules_to_transaction(temp_tx)
                        if rule_category:
                            category_to_use = rule_category
                            logger.info(f"Applied category rule to transaction: {description[:30]}...")
                        else:
                            # Fallback to Pluggy category
                            category_to_use = get_or_create_category(user, pluggy_category, tx_type)

                    tx_obj, created = TransactionModel.objects.update_or_create(
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
                            'user_category': category_to_use,
                        }
                    )
                    synced_count += 1

                    # Track new transactions for auto-match
                    if created:
                        new_transactions.append(tx_obj)

            account.last_synced_at = timezone.now()
            account.save()

            sync_log.status = 'SUCCESS'
            sync_log.completed_at = timezone.now()
            sync_log.records_synced = synced_count
            sync_log.save()

            logger.info(f"Synced {synced_count} transactions for account {account.id}")

            # Auto-match new transactions with bills
            if new_transactions:
                match_service = TransactionMatchService()
                match_result = match_service.auto_match_transactions(user, new_transactions)
                logger.info(
                    f"Auto-match result: {len(match_result['matched'])} matched, "
                    f"{len(match_result['ambiguous'])} ambiguous, "
                    f"{len(match_result['no_match'])} no match"
                )

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


class TransactionMatchService:
    """
    Service for matching transactions with bills (accounts payable/receivable).
    Handles automatic and manual linking of bank transactions to bills.
    """

    def get_eligible_bills_for_transaction(self, transaction: TransactionModel) -> List['Bill']:
        """
        Find bills that can be linked to a transaction.

        Eligibility criteria:
        - Same user as transaction owner
        - Status = 'pending' (no prior payments)
        - amount_paid = 0 (virgin bill)
        - No linked_transaction yet
        - Exact amount match
        - Compatible type (CREDIT -> receivable, DEBIT -> payable)
        """
        from .models import Bill

        user = transaction.account.connection.user

        # Determine compatible bill type
        bill_type = 'receivable' if transaction.type == 'CREDIT' else 'payable'

        eligible_bills = Bill.objects.filter(
            user=user,
            type=bill_type,
            status='pending',
            amount_paid=Decimal('0.00'),
            linked_transaction__isnull=True,
            amount=transaction.amount
        ).select_related('category').order_by('due_date')

        return list(eligible_bills)

    def get_all_pending_bills_for_transaction(self, transaction: TransactionModel) -> List[Dict]:
        """
        Get ALL pending bills for manual linking (no amount filter).
        Returns bills with match info for UI display.

        Criteria:
        - Same user as transaction owner
        - Status in ['pending', 'partially_paid']
        - No linked_transaction (legacy link)
        - Compatible type (CREDIT -> receivable, DEBIT -> payable)
        - Has remaining amount > 0
        """
        from .models import Bill

        user = transaction.account.connection.user

        # Determine compatible bill type
        bill_type = 'receivable' if transaction.type == 'CREDIT' else 'payable'

        bills = Bill.objects.filter(
            user=user,
            type=bill_type,
            status__in=['pending', 'partially_paid'],
            linked_transaction__isnull=True
        ).select_related('category').order_by('due_date')

        result = []
        for bill in bills:
            # Skip bills with no remaining amount
            if bill.amount_remaining <= 0:
                continue

            amount_diff = float(transaction.amount) - float(bill.amount_remaining)
            # Compare with amount_remaining for partially paid bills
            amount_match = transaction.amount == bill.amount_remaining
            result.append({
                'bill': bill,
                'amount_match': amount_match,
                'amount_diff': amount_diff,
                'would_overpay': amount_diff > 0,
                'relevance_score': self.calculate_relevance_score(transaction, bill)
            })

        # Sort by relevance score descending
        result.sort(key=lambda x: x['relevance_score'], reverse=True)
        return result

    def link_transaction_to_bill_forced(
        self,
        transaction: TransactionModel,
        bill: 'Bill'
    ) -> 'Bill':
        """
        Force link a transaction to a bill, handling different amounts.

        - If transaction amount <= bill remaining: register as partial payment
        - If transaction amount > bill remaining: register full payment (caps at remaining)
        """
        from .models import Bill, BillPayment
        from django.db import transaction as db_transaction

        # Validations
        if bill.status == 'paid':
            raise ValueError("Bill is already fully paid.")

        if bill.status == 'cancelled':
            raise ValueError("Bill is cancelled.")

        if bill.amount_remaining <= 0:
            raise ValueError("Bill has no remaining amount to pay.")

        if transaction.amount <= 0:
            raise ValueError("Transaction amount must be greater than zero.")

        if bill.linked_transaction is not None:
            raise ValueError("Bill is already linked to another transaction (legacy).")

        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            raise ValueError("Transaction is already linked to another bill.")

        # Check type compatibility
        expected_tx_type = 'CREDIT' if bill.type == 'receivable' else 'DEBIT'
        if transaction.type != expected_tx_type:
            raise ValueError(
                f"Type mismatch. Bill type '{bill.type}' requires transaction type '{expected_tx_type}'"
            )

        # Check same user
        if transaction.account.connection.user != bill.user:
            raise ValueError("Transaction and bill must belong to the same user")

        # Check if transaction is already used in a BillPayment
        existing_payment = BillPayment.objects.filter(transaction=transaction).first()
        if existing_payment:
            raise ValueError(f"Transaction is already linked to bill '{existing_payment.bill.description}'")

        # Determine payment amount (cap at remaining)
        payment_amount = min(transaction.amount, bill.amount_remaining)

        # Use atomic transaction for data integrity
        with db_transaction.atomic():
            # Create BillPayment
            payment = BillPayment.objects.create(
                bill=bill,
                amount=payment_amount,
                payment_date=transaction.date.date() if hasattr(transaction.date, 'date') else transaction.date,
                transaction=transaction,
                notes=f"Vinculado manualmente. Transacao: {transaction.description[:50]}"
            )

            # Refresh bill to get updated state
            bill.refresh_from_db()

        return bill

    def get_eligible_transactions_for_bill(self, bill: 'Bill') -> List[TransactionModel]:
        """
        Find transactions that can be linked to a bill.

        Eligibility criteria:
        - Same user as bill owner
        - No linked_bill yet
        - Exact amount match
        - Compatible type (receivable -> CREDIT, payable -> DEBIT)
        """
        user = bill.user

        # Determine compatible transaction type
        tx_type = 'CREDIT' if bill.type == 'receivable' else 'DEBIT'

        eligible_transactions = TransactionModel.objects.filter(
            account__connection__user=user,
            account__connection__is_active=True,
            type=tx_type,
            amount=bill.amount,
            linked_bill__isnull=True
        ).select_related(
            'account',
            'account__connection',
            'user_category'
        ).order_by('-date')

        return list(eligible_transactions)

    def calculate_relevance_score(self, transaction: TransactionModel, bill: 'Bill') -> int:
        """
        Calculate relevance score (0-100) for ranking suggestions.
        Higher score = more relevant match.
        """
        score = 0

        # 1. Date proximity (up to 50 points)
        tx_date = transaction.date.date() if hasattr(transaction.date, 'date') else transaction.date
        days_diff = abs((tx_date - bill.due_date).days)

        if days_diff == 0:
            score += 50
        elif days_diff <= 3:
            score += 40
        elif days_diff <= 7:
            score += 30
        elif days_diff <= 15:
            score += 20
        elif days_diff <= 30:
            score += 10

        # 2. Description similarity (up to 30 points)
        tx_text = f"{transaction.description} {transaction.merchant_name or ''}".lower()
        bill_text = f"{bill.description} {bill.customer_supplier or ''}".lower()

        tx_words = set(tx_text.split())
        bill_words = set(bill_text.split())
        common_words = tx_words & bill_words

        # Remove common stopwords
        stopwords = {'de', 'da', 'do', 'para', 'a', 'o', 'e', 'em', 'com', 'por', '-', ''}
        common_words = common_words - stopwords

        score += min(len(common_words) * 10, 30)

        # 3. Same category (up to 20 points)
        if transaction.user_category_id and bill.category_id:
            if transaction.user_category_id == bill.category_id:
                score += 20

        return score

    def get_suggested_transactions_for_bill(self, bill: 'Bill', limit: int = 10) -> List[Dict]:
        """
        Get transactions suggested for linking to a bill, ordered by relevance.
        Returns list of dicts with transaction data and relevance score.
        """
        if bill.status != 'pending' or bill.amount_paid > 0 or bill.linked_transaction:
            return []

        transactions = self.get_eligible_transactions_for_bill(bill)

        # Calculate scores and sort
        suggestions = []
        for tx in transactions:
            score = self.calculate_relevance_score(tx, bill)
            suggestions.append({
                'transaction': tx,
                'relevance_score': score
            })

        # Sort by score descending
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)

        return suggestions[:limit]

    def get_suggested_bills_for_transaction(self, transaction: TransactionModel, limit: int = 10) -> List[Dict]:
        """
        Get bills suggested for linking to a transaction, ordered by relevance.
        Returns list of dicts with bill data and relevance score.
        """
        # Check if transaction already linked
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            return []

        bills = self.get_eligible_bills_for_transaction(transaction)

        # Calculate scores and sort
        suggestions = []
        for bill in bills:
            score = self.calculate_relevance_score(transaction, bill)
            suggestions.append({
                'bill': bill,
                'relevance_score': score
            })

        # Sort by score descending
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)

        return suggestions[:limit]

    def link_transaction_to_bill(self, transaction: TransactionModel, bill: 'Bill') -> 'Bill':
        """
        Link a transaction to a bill and mark bill as paid.

        Raises ValueError if linking is not allowed.
        """
        from .models import Bill

        # Validations
        if bill.status != 'pending':
            raise ValueError(f"Bill must be pending. Current status: {bill.status}")

        if bill.amount_paid > 0:
            raise ValueError("Bill already has prior payments. Only virgin bills can be linked.")

        if bill.linked_transaction is not None:
            raise ValueError("Bill is already linked to another transaction.")

        # Check if transaction is already linked
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            raise ValueError("Transaction is already linked to another bill.")

        if transaction.amount != bill.amount:
            raise ValueError(
                f"Amount mismatch. Transaction: {transaction.amount}, Bill: {bill.amount}"
            )

        # Check type compatibility
        expected_tx_type = 'CREDIT' if bill.type == 'receivable' else 'DEBIT'
        if transaction.type != expected_tx_type:
            raise ValueError(
                f"Type mismatch. Bill type '{bill.type}' requires transaction type '{expected_tx_type}'"
            )

        # Check same user
        tx_user = transaction.account.connection.user
        if tx_user != bill.user:
            raise ValueError("Transaction and bill must belong to the same user.")

        # Link and update bill
        with transaction_db.atomic():
            bill.linked_transaction = transaction
            bill.amount_paid = bill.amount
            bill.paid_at = transaction.date
            bill.status = 'paid'
            bill.save()

        logger.info(
            f"Linked transaction {transaction.id} to bill {bill.id}. "
            f"Bill marked as paid."
        )

        return bill

    def unlink_transaction_from_bill(self, bill: 'Bill') -> 'Bill':
        """
        Remove link between transaction and bill.

        Se a bill tiver BillPayments, recalcula o status a partir deles.
        Caso contrário, reverte para pending.
        """
        if bill.linked_transaction is None:
            raise ValueError("Bill is not linked to any transaction.")

        tx_id = bill.linked_transaction.id

        with transaction_db.atomic():
            # Remove apenas o vínculo legacy
            bill.linked_transaction = None
            bill.save(update_fields=['linked_transaction'])

            # Recalcula a partir dos BillPayments existentes
            # Se não houver BillPayments, amount_paid será 0 e status será 'pending'
            # update_status() já cuida de resetar paid_at quando necessário
            bill.recalculate_payments()

        logger.info(
            f"Unlinked transaction {tx_id} from bill {bill.id}. "
            f"Bill status: {bill.status}, amount_paid: {bill.amount_paid}"
        )

        return bill

    def auto_match_transactions(
        self,
        user,
        transactions: List[TransactionModel]
    ) -> Dict[str, List]:
        """
        Automatically match transactions to bills.

        Only matches if:
        - User has auto_match_transactions enabled
        - Exactly ONE bill matches the transaction

        Returns:
            {
                'matched': [{'transaction': tx, 'bill': bill}, ...],
                'ambiguous': [{'transaction': tx, 'bills': [bill1, bill2]}, ...],
                'no_match': [tx, ...]
            }
        """
        from apps.authentication.models import UserSettings

        # Check user settings
        settings = UserSettings.get_or_create_for_user(user)

        result = {
            'matched': [],
            'ambiguous': [],
            'no_match': []
        }

        if not settings.auto_match_transactions:
            logger.info(f"Auto-match disabled for user {user.id}")
            result['no_match'] = list(transactions)
            return result

        for tx in transactions:
            # Skip if already linked
            if hasattr(tx, 'linked_bill') and tx.linked_bill:
                continue

            eligible_bills = self.get_eligible_bills_for_transaction(tx)

            if len(eligible_bills) == 0:
                result['no_match'].append(tx)
            elif len(eligible_bills) == 1:
                # Single match - auto link
                bill = eligible_bills[0]
                try:
                    self.link_transaction_to_bill(tx, bill)
                    result['matched'].append({
                        'transaction': tx,
                        'bill': bill
                    })
                    logger.info(f"Auto-matched transaction {tx.id} to bill {bill.id}")
                except ValueError as e:
                    logger.warning(f"Failed to auto-match transaction {tx.id}: {e}")
                    result['no_match'].append(tx)
            else:
                # Multiple matches - ambiguous, user must decide
                result['ambiguous'].append({
                    'transaction': tx,
                    'bills': eligible_bills
                })
                logger.info(
                    f"Ambiguous match for transaction {tx.id}: "
                    f"{len(eligible_bills)} bills with same value"
                )

        return result

    # ============================================================
    # MÉTODOS PARA PAGAMENTOS PARCIAIS (BillPayment)
    # ============================================================

    def get_eligible_transactions_for_partial_payment(
        self,
        bill: 'Bill',
        max_amount: Optional[Decimal] = None
    ) -> List[TransactionModel]:
        """
        Encontra transações elegíveis para pagamento parcial.

        Critérios:
        - Mesmo usuário da bill
        - Não vinculada a nenhuma bill (via BillPayment ou legacy)
        - Tipo compatível (receivable -> CREDIT, payable -> DEBIT)
        - Valor <= valor restante (ou max_amount se especificado)
        """
        from .models import Bill, BillPayment

        user = bill.user
        remaining = max_amount or bill.amount_remaining

        # Tipo de transação compatível
        tx_type = 'CREDIT' if bill.type == 'receivable' else 'DEBIT'

        # IDs de transações já vinculadas via BillPayment
        linked_via_payment = set(
            BillPayment.objects.filter(
                transaction__isnull=False
            ).values_list('transaction_id', flat=True)
        )

        # IDs de transações vinculadas via legacy (Bill.linked_transaction)
        linked_via_legacy = set(
            Bill.objects.filter(
                linked_transaction__isnull=False
            ).values_list('linked_transaction_id', flat=True)
        )

        excluded_ids = linked_via_payment | linked_via_legacy

        eligible = TransactionModel.objects.filter(
            account__connection__user=user,
            account__connection__is_active=True,
            type=tx_type,
            amount__lte=remaining,
            amount__gt=0
        ).exclude(
            id__in=excluded_ids
        ).select_related(
            'account',
            'account__connection',
            'user_category'
        ).order_by('-date')

        return list(eligible)

    def link_transaction_as_partial_payment(
        self,
        transaction: TransactionModel,
        bill: 'Bill',
        notes: str = ''
    ) -> 'BillPayment':
        """
        Vincula uma transação como pagamento parcial a uma bill.

        Cria um BillPayment e atualiza o status da bill.

        Raises:
            ValueError: Se a vinculação não for permitida
        """
        from .models import Bill, BillPayment

        # Validações
        if not bill.can_add_payment:
            raise ValueError(f"Bill não pode receber pagamentos. Status: {bill.status}")

        if transaction.amount > bill.amount_remaining:
            raise ValueError(
                f"Valor da transação ({transaction.amount}) excede o restante "
                f"({bill.amount_remaining})"
            )

        # Verifica se transação já está vinculada via BillPayment
        if BillPayment.objects.filter(transaction=transaction).exists():
            raise ValueError("Transação já está vinculada a outra conta")

        # Verifica se transação está vinculada via legacy
        if hasattr(transaction, 'linked_bill') and transaction.linked_bill:
            raise ValueError("Transação já está vinculada (legacy) a outra conta")

        # Verifica compatibilidade de tipo
        expected_tx_type = 'CREDIT' if bill.type == 'receivable' else 'DEBIT'
        if transaction.type != expected_tx_type:
            raise ValueError(
                f"Tipo incompatível. Bill tipo '{bill.type}' requer "
                f"transação tipo '{expected_tx_type}'"
            )

        # Verifica mesmo usuário
        tx_user = transaction.account.connection.user
        if tx_user != bill.user:
            raise ValueError("Transação e bill devem pertencer ao mesmo usuário")

        # Cria o BillPayment
        with transaction_db.atomic():
            payment = BillPayment.objects.create(
                bill=bill,
                transaction=transaction,
                amount=transaction.amount,
                payment_date=transaction.date,
                notes=notes
            )
            # recalculate_payments é chamado automaticamente no save() do BillPayment

        logger.info(
            f"Criado pagamento parcial {payment.id}: "
            f"Transação {transaction.id} -> Bill {bill.id} "
            f"(Valor: {transaction.amount})"
        )

        return payment

    def unlink_payment(self, payment: 'BillPayment') -> 'Bill':
        """
        Remove um pagamento de uma bill.

        Deleta o BillPayment e recalcula o status da bill.
        """
        bill = payment.bill
        payment_id = payment.id
        tx_id = payment.transaction_id

        with transaction_db.atomic():
            payment.delete()
            # recalculate_payments é chamado automaticamente no delete() do BillPayment

        logger.info(
            f"Removido pagamento {payment_id} da bill {bill.id}. "
            f"Transação {tx_id} agora está livre."
        )

        return bill

    def get_suggested_transactions_for_partial(
        self,
        bill: 'Bill',
        limit: int = 20
    ) -> List[Dict]:
        """
        Retorna transações sugeridas para pagamento parcial, ordenadas por relevância.

        Adiciona bônus para valores que dividem igualmente o total.
        """
        if not bill.can_add_payment:
            return []

        transactions = self.get_eligible_transactions_for_partial_payment(bill)

        suggestions = []
        for tx in transactions:
            score = self.calculate_relevance_score(tx, bill)

            # Bônus para valores que dividem igualmente
            if bill.amount > 0 and tx.amount > 0:
                if bill.amount % tx.amount == 0:
                    score += 10

            suggestions.append({
                'transaction': tx,
                'relevance_score': min(score, 100),
                'would_complete_bill': tx.amount >= bill.amount_remaining
            })

        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        return suggestions[:limit]


class CategoryRuleService:
    """
    Serviço para gerenciamento de regras de categorização automática.
    Permite encontrar transações similares e aplicar categorias automaticamente.
    """

    STOPWORDS = {'de', 'da', 'do', 'para', 'a', 'o', 'e', 'em', 'com', 'por', 'pix', 'ted', 'doc', 'pagto'}

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto para comparação de similaridade.
        Remove acentos, converte para lowercase e strip.
        """
        if not text:
            return ''
        try:
            from unidecode import unidecode
            return unidecode(text.lower().strip())
        except ImportError:
            # Fallback se unidecode não estiver instalado
            return text.lower().strip()

    @staticmethod
    def find_similar_transactions(user, transaction, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Encontra transações similares à transação dada.

        Critérios de similaridade (em ordem de prioridade):
        1. Mesmo merchant_name (se disponível) - score: 1.0
        2. Prefixo comum >= 8 chars - score: 0.9
        3. Similaridade fuzzy >= 70% - score: variável

        Args:
            user: Usuário dono das transações
            transaction: Transação base para comparação
            limit: Número máximo de transações a retornar

        Returns:
            Lista de dicts com 'transaction', 'score' e 'match_type'
        """
        from difflib import SequenceMatcher

        base_desc = CategoryRuleService.normalize_text(transaction.description)
        base_merchant = CategoryRuleService.normalize_text(transaction.merchant_name)

        # Limita a últimos 6 meses, mesmo tipo de transação
        six_months_ago = timezone.now() - timedelta(days=180)
        candidates = TransactionModel.objects.filter(
            account__connection__user=user,
            type=transaction.type,
            date__gte=six_months_ago,
        ).exclude(
            id=transaction.id
        ).select_related('user_category', 'account', 'account__connection')[:500]

        similar = []
        for t in candidates:
            # Pula se já foi categorizada manualmente (user_category diferente do pluggy)
            if t.user_category:
                translated_pluggy = get_category_translations().get(t.pluggy_category, t.pluggy_category)
                if t.user_category.name != translated_pluggy:
                    continue

            score = 0.0
            match_type = None
            t_desc = CategoryRuleService.normalize_text(t.description)

            # 1. Match por merchant_name (mais confiável)
            if base_merchant and t.merchant_name:
                t_merchant = CategoryRuleService.normalize_text(t.merchant_name)
                if base_merchant == t_merchant:
                    score = 1.0
                    match_type = 'merchant'

            # 2. Match por prefixo (primeiros 12 chars)
            if not match_type and len(base_desc) >= 8 and len(t_desc) >= 8:
                prefix_len = min(12, len(base_desc), len(t_desc))
                if base_desc[:prefix_len] == t_desc[:prefix_len]:
                    score = 0.9
                    match_type = 'prefix'

            # 3. Fuzzy match (similaridade >= 70%)
            if not match_type and len(base_desc) >= 5 and len(t_desc) >= 5:
                ratio = SequenceMatcher(None, base_desc, t_desc).ratio()
                if ratio >= 0.70:
                    score = ratio
                    match_type = 'fuzzy'

            if match_type:
                similar.append({
                    'transaction': t,
                    'score': score,
                    'match_type': match_type
                })

        # Ordena por score decrescente e limita
        return sorted(similar, key=lambda x: -x['score'])[:limit]

    @staticmethod
    def create_rule_from_transaction(user, transaction, category) -> 'CategoryRule':
        """
        Cria uma regra de categorização baseada em uma transação.

        Args:
            user: Usuário dono da regra
            transaction: Transação que servirá de base para o padrão
            category: Categoria a ser aplicada

        Returns:
            CategoryRule criada ou atualizada

        Raises:
            ValueError: Se o padrão for muito curto (< 3 chars)
        """
        from .models import CategoryRule

        # Determina o melhor padrão baseado nos dados disponíveis
        if transaction.merchant_name:
            pattern = CategoryRuleService.normalize_text(transaction.merchant_name)
            match_type = 'contains'
        else:
            desc = CategoryRuleService.normalize_text(transaction.description)
            pattern = desc[:12].strip()
            match_type = 'prefix'

        # Valida tamanho mínimo do padrão
        if len(pattern) < 3:
            raise ValueError("Padrão muito curto para criar regra automática")

        # Cria ou atualiza a regra
        rule, created = CategoryRule.objects.get_or_create(
            user=user,
            pattern=pattern,
            match_type=match_type,
            defaults={
                'category': category,
                'created_from_transaction': transaction
            }
        )

        if not created:
            # Atualiza categoria se a regra já existia
            rule.category = category
            rule.save(update_fields=['category', 'updated_at'])

        logger.info(
            f"{'Created' if created else 'Updated'} category rule: "
            f"'{pattern}' ({match_type}) -> {category.name} for user {user.id}"
        )

        return rule

    @staticmethod
    def apply_rules_to_transaction(transaction) -> Optional[Category]:
        """
        Aplica regras de categorização a uma transação.

        Verifica todas as regras ativas do usuário e retorna a primeira
        categoria que fizer match (ordenado por data de criação).

        Args:
            transaction: Transação a ser categorizada

        Returns:
            Category se encontrar match, None caso contrário
        """
        from difflib import SequenceMatcher
        from .models import CategoryRule

        user = transaction.account.connection.user
        rules = CategoryRule.objects.filter(
            user=user,
            is_active=True
        ).select_related('category').order_by('created_at')

        t_desc = CategoryRuleService.normalize_text(transaction.description)
        t_merchant = CategoryRuleService.normalize_text(transaction.merchant_name)

        for rule in rules:
            matched = False

            if rule.match_type == 'prefix':
                matched = t_desc.startswith(rule.pattern)
            elif rule.match_type == 'contains':
                matched = rule.pattern in t_desc or rule.pattern in t_merchant
            elif rule.match_type == 'fuzzy':
                ratio = SequenceMatcher(None, rule.pattern, t_desc).ratio()
                matched = ratio >= 0.70

            if matched:
                # Incrementa contador de aplicações
                CategoryRule.objects.filter(id=rule.id).update(
                    applied_count=models.F('applied_count') + 1
                )
                logger.debug(
                    f"Rule '{rule.pattern}' matched transaction {transaction.id}, "
                    f"applying category {rule.category.name}"
                )
                return rule.category

        return None
