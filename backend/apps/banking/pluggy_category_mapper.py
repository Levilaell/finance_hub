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
        # Pluggy Category -> Nossa Categoria
        'AUTO': 'Transporte',
        'TRANSPORT': 'Transporte',
        'TRANSPORTATION': 'Transporte',
        'UBER': 'Transporte',
        'TAXI': 'Transporte',
        'GAS': 'Combustível',
        'FUEL': 'Combustível',
        'PARKING': 'Estacionamento',
        
        'FOOD': 'Alimentação',
        'RESTAURANT': 'Restaurante',
        'GROCERIES': 'Mercado',
        'SUPERMARKET': 'Mercado',
        'DELIVERY': 'Delivery',
        
        'ENTERTAINMENT': 'Entretenimento',
        'STREAMING': 'Streaming',
        'NETFLIX': 'Streaming',
        'SPOTIFY': 'Streaming',
        'GAMES': 'Jogos',
        'MOVIES': 'Cinema',
        
        'BILLS': 'Contas',
        'UTILITIES': 'Utilidades',
        'ELECTRICITY': 'Energia',
        'WATER': 'Água',
        'INTERNET': 'Internet',
        'PHONE': 'Telefone',
        'MOBILE': 'Celular',
        
        'HEALTH': 'Saúde',
        'PHARMACY': 'Farmácia',
        'MEDICAL': 'Médico',
        'HEALTHCARE': 'Saúde',
        'FITNESS': 'Academia',
        'GYM': 'Academia',
        
        'SHOPPING': 'Compras',
        'CLOTHING': 'Roupas',
        'ELECTRONICS': 'Eletrônicos',
        'HOME': 'Casa',
        'FURNITURE': 'Móveis',
        
        'EDUCATION': 'Educação',
        'BOOKS': 'Livros',
        'COURSES': 'Cursos',
        
        'TRAVEL': 'Viagem',
        'HOTEL': 'Hotel',
        'FLIGHT': 'Passagem Aérea',
        'ACCOMMODATION': 'Hospedagem',
        
        'TRANSFER': 'Transferências',
        'PIX': 'PIX',
        'TED': 'TED',
        'DOC': 'DOC',
        
        'INCOME': 'Receitas',
        'SALARY': 'Salário',
        'REVENUE': 'Receitas',
        'INVESTMENT': 'Investimentos',
        
        'TAX': 'Impostos',
        'FEES': 'Taxas',
        'BANK_FEES': 'Taxas Bancárias',
        
        'OTHER': 'Outros',
        'CASH': 'Dinheiro',
        'WITHDRAWAL': 'Saque',
        'DEPOSIT': 'Depósito',
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