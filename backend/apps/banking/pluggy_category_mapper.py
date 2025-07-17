"""
Pluggy Category Mapping Service
Maps Pluggy categories to CaixaHub categories
"""
import logging
from typing import Optional, Dict
from django.core.cache import cache

from apps.banking.models import TransactionCategory

logger = logging.getLogger(__name__)


class PluggyCategoryMapper:
    """
    Service to map Pluggy categories to internal categories
    """
    
    # Mapeamento das categorias da Pluggy para nossas categorias
    CATEGORY_MAPPING = {
        # === TRANSPORTE ===
        'AUTO': 'Transporte',
        'TRANSPORT': 'Transporte',
        'TRANSPORTATION': 'Transporte',
        'UBER': 'Transporte',
        'TAXI': 'Transporte',
        'CAR': 'Transporte',
        'VEHICLE': 'Transporte',
        'BUS': 'Transporte',
        'METRO': 'Transporte',
        'SUBWAY': 'Transporte',
        'TOLL': 'Transporte',
        'PARKING': 'Transporte',
        'TOLL_FEE': 'Transporte',
        'GAS': 'Transporte',
        'FUEL': 'Transporte',
        'GASOLINE': 'Transporte',
        'ETHANOL': 'Transporte',
        'GAS_STATION': 'Transporte',
        
        # === ALIMENTAÇÃO ===
        'FOOD': 'Alimentação',
        'FOOD_AND_DRINK': 'Alimentação',
        'RESTAURANT': 'Alimentação',
        'RESTAURANTS': 'Alimentação',
        'FAST_FOOD': 'Alimentação',
        'CAFE': 'Alimentação',
        'COFFEE': 'Alimentação',
        'BAKERY': 'Alimentação',
        'BAR': 'Alimentação',
        'DELIVERY': 'Alimentação',
        'FOOD_DELIVERY': 'Alimentação',
        'GROCERIES': 'Alimentação',
        'GROCERY': 'Alimentação',
        'SUPERMARKET': 'Alimentação',
        'MARKET': 'Alimentação',
        
        # === ENTRETENIMENTO ===
        'ENTERTAINMENT': 'Entretenimento',
        'STREAMING': 'Entretenimento',
        'NETFLIX': 'Entretenimento',
        'SPOTIFY': 'Entretenimento',
        'AMAZON_PRIME': 'Entretenimento',
        'GAMES': 'Entretenimento',
        'GAMING': 'Entretenimento',
        'MOVIES': 'Entretenimento',
        'CINEMA': 'Entretenimento',
        'THEATER': 'Entretenimento',
        'CONCERT': 'Entretenimento',
        'SPORTS': 'Entretenimento',
        'RECREATION': 'Entretenimento',
        
        # === CONTAS E UTILIDADES ===
        'BILLS': 'Contas de Consumo',
        'UTILITIES': 'Contas de Consumo',
        'ELECTRICITY': 'Contas de Consumo',
        'ENERGY': 'Contas de Consumo',
        'WATER': 'Contas de Consumo',
        'WATER_AND_SEWER': 'Contas de Consumo',
        'INTERNET': 'Contas de Consumo',
        'PHONE': 'Contas de Consumo',
        'MOBILE': 'Contas de Consumo',
        'TELEPHONE': 'Contas de Consumo',
        'CABLE': 'Contas de Consumo',
        'TV': 'Contas de Consumo',
        
        # === SAÚDE ===
        'HEALTH': 'Saúde',
        'HEALTHCARE': 'Saúde',
        'HEALTH_AND_FITNESS': 'Saúde',
        'PHARMACY': 'Saúde',
        'MEDICAL': 'Saúde',
        'DOCTOR': 'Saúde',
        'HOSPITAL': 'Saúde',
        'CLINIC': 'Saúde',
        'DENTIST': 'Saúde',
        'FITNESS': 'Saúde',
        'GYM': 'Saúde',
        'WELLNESS': 'Saúde',
        
        # === COMPRAS ===
        'SHOPPING': 'Outros Gastos',
        'GENERAL_MERCHANDISE': 'Outros Gastos',
        'RETAIL': 'Outros Gastos',
        'CLOTHING': 'Outros Gastos',
        'APPAREL': 'Outros Gastos',
        'FASHION': 'Outros Gastos',
        'ELECTRONICS': 'Software e Tecnologia',
        'TECHNOLOGY': 'Software e Tecnologia',
        'COMPUTERS': 'Software e Tecnologia',
        'SOFTWARE': 'Software e Tecnologia',
        'HOME': 'Outros Gastos',
        'HOME_AND_GARDEN': 'Outros Gastos',
        'FURNITURE': 'Outros Gastos',
        'HARDWARE': 'Outros Gastos',
        
        # === EDUCAÇÃO ===
        'EDUCATION': 'Educação',
        'SCHOOL': 'Educação',
        'UNIVERSITY': 'Educação',
        'COLLEGE': 'Educação',
        'BOOKS': 'Educação',
        'COURSES': 'Educação',
        'TRAINING': 'Educação',
        
        # === VIAGEM ===
        'TRAVEL': 'Viagem',
        'HOTEL': 'Viagem',
        'HOTELS': 'Viagem',
        'ACCOMMODATION': 'Viagem',
        'LODGING': 'Viagem',
        'FLIGHT': 'Viagem',
        'AIRLINE': 'Viagem',
        'TRAVEL_AGENCY': 'Viagem',
        
        # === FINANÇAS ===
        'TRANSFER': 'Transferências',
        'MONEY_TRANSFER': 'Transferências',
        'WIRE_TRANSFER': 'Transferências',
        'PIX': 'Transferências',
        'TED': 'Transferências',
        'DOC': 'Transferências',
        'BANK_TRANSFER': 'Transferências',
        
        # === RECEITAS ===
        'INCOME': 'Outros Recebimentos',
        'SALARY': 'Vendas',
        'REVENUE': 'Vendas',
        'PAYMENT': 'Vendas',
        'DEPOSIT': 'Outros Recebimentos',
        'INVESTMENT': 'Investimentos',
        'INVESTMENT_INCOME': 'Investimentos',
        'DIVIDENDS': 'Investimentos',
        'INTEREST': 'Investimentos',
        
        # === IMPOSTOS E TAXAS ===
        'TAX': 'Impostos',
        'TAXES': 'Impostos',
        'GOVERNMENT': 'Impostos',
        'FEES': 'Taxas Bancárias',
        'FEE': 'Taxas Bancárias',
        'BANK_FEES': 'Taxas Bancárias',
        'SERVICE_FEE': 'Taxas Bancárias',
        'FINE': 'Impostos',
        
        # === OUTROS ===
        'OTHER': 'Outros Gastos',
        'OTHERS': 'Outros Gastos',
        'MISCELLANEOUS': 'Outros Gastos',
        'CASH': 'Outros Gastos',
        'WITHDRAWAL': 'Outros Gastos',
        'ATM': 'Outros Gastos',
        'PERSONAL': 'Outros Gastos',
        'SERVICES': 'Outros Gastos',
        'INSURANCE': 'Seguros',
        'RENT': 'Aluguel e Condomínio',
        'MORTGAGE': 'Aluguel e Condomínio',
        'LOAN': 'Empréstimos',
        'CREDIT': 'Outros Gastos',
        
        # === FORNECEDORES (BUSINESS) ===
        'SUPPLIER': 'Fornecedores',
        'VENDORS': 'Fornecedores',
        'BUSINESS': 'Fornecedores',
        'B2B': 'Fornecedores',
        
        # === FOLHA DE PAGAMENTO ===
        'PAYROLL': 'Folha de Pagamento',
        'EMPLOYEE': 'Folha de Pagamento',
        'WAGES': 'Folha de Pagamento',
        
        # === MARKETING ===
        'MARKETING': 'Marketing',
        'ADVERTISING': 'Marketing',
        'ADS': 'Marketing',
        'PROMOTION': 'Marketing',
    }
    
    def __init__(self):
        self._category_cache = {}
        self._load_categories()
    
    def _load_categories(self):
        """Load all categories into memory for fast lookup"""
        try:
            # Check cache first
            cached = cache.get('pluggy_category_mapping')
            if cached:
                self._category_cache = cached
                return
            
            # Load from database
            categories = TransactionCategory.objects.filter(
                is_active=True
            ).values('id', 'name', 'slug', 'category_type')
            
            # Create lookup dictionaries
            self._category_cache = {
                'by_name': {cat['name'].lower(): cat for cat in categories},
                'by_slug': {cat['slug']: cat for cat in categories},
            }
            
            # Cache for 1 hour
            cache.set('pluggy_category_mapping', self._category_cache, 3600)
            
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            self._category_cache = {'by_name': {}, 'by_slug': {}}
    
    def map_category(self, pluggy_category: str, transaction_type: str = None) -> Optional[TransactionCategory]:
        """
        Map Pluggy category to internal category
        
        Args:
            pluggy_category: Category name from Pluggy
            transaction_type: Transaction type (credit/debit)
            
        Returns:
            TransactionCategory or None
        """
        if not pluggy_category:
            return None
        
        try:
            # Normalize category name
            pluggy_cat_upper = pluggy_category.upper().strip()
            
            # First, try direct mapping
            if pluggy_cat_upper in self.CATEGORY_MAPPING:
                mapped_name = self.CATEGORY_MAPPING[pluggy_cat_upper]
                
                # Look up in cache
                category_data = self._category_cache['by_name'].get(mapped_name.lower())
                if category_data:
                    # Verify category type matches transaction type
                    if transaction_type:
                        if transaction_type == 'credit' and category_data['category_type'] == 'expense':
                            return None
                        if transaction_type == 'debit' and category_data['category_type'] == 'income':
                            return None
                    
                    # Return the category
                    return TransactionCategory.objects.get(id=category_data['id'])
            
            # Try fuzzy matching
            pluggy_cat_lower = pluggy_category.lower()
            for cat_name, cat_data in self._category_cache['by_name'].items():
                if pluggy_cat_lower in cat_name or cat_name in pluggy_cat_lower:
                    # Verify category type
                    if transaction_type:
                        if transaction_type == 'credit' and cat_data['category_type'] == 'expense':
                            continue
                        if transaction_type == 'debit' and cat_data['category_type'] == 'income':
                            continue
                    
                    return TransactionCategory.objects.get(id=cat_data['id'])
            
            logger.warning(f"No mapping found for Pluggy category: {pluggy_category}")
            return None
            
        except Exception as e:
            logger.error(f"Error mapping category {pluggy_category}: {e}")
            return None
    
    def get_or_create_category(self, pluggy_category: str, transaction_type: str) -> Optional[TransactionCategory]:
        """
        Get or create a category based on Pluggy data
        
        Args:
            pluggy_category: Category name from Pluggy
            transaction_type: Transaction type (credit/debit)
            
        Returns:
            TransactionCategory or None
        """
        # First try to map existing category
        category = self.map_category(pluggy_category, transaction_type)
        if category:
            return category
        
        # If no mapping found, create a new category
        try:
            category_type = 'income' if transaction_type == 'credit' else 'expense'
            
            # Clean category name
            clean_name = pluggy_category.strip().title()
            
            # Create slug
            from django.utils.text import slugify
            slug = slugify(f"pluggy-{clean_name}")
            
            # Create category
            category, created = TransactionCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': clean_name,
                    'category_type': category_type,
                    'icon': '📌',  # Default icon for Pluggy categories
                    'color': '#6B7280',  # Gray color
                    'keywords': [pluggy_category, pluggy_category.lower()],
                    'is_system': False,
                    'confidence_threshold': 0.9,  # High confidence since from Pluggy
                }
            )
            
            if created:
                logger.info(f"Created new category from Pluggy: {clean_name}")
                # Reload cache
                self._load_categories()
            
            return category
            
        except Exception as e:
            logger.error(f"Error creating category {pluggy_category}: {e}")
            return None
    
    def clear_cache(self):
        """Clear category mapping cache"""
        cache.delete('pluggy_category_mapping')
        self._category_cache = {'by_name': {}, 'by_slug': {}}
        self._load_categories()


# Global mapper instance
pluggy_category_mapper = PluggyCategoryMapper()