"""
Pluggy Category Mapper
Maps Pluggy categories to internal TransactionCategory model
"""
import logging
from typing import Optional
from django.core.cache import cache
from .models import TransactionCategory

logger = logging.getLogger(__name__)


class PluggyCategoryMapper:
    """
    Maps Pluggy categories to our internal category system
    """
    
    # Mapping of Pluggy categories to our internal categories
    CATEGORY_MAPPING = {
        # Food & Dining
        'FOOD_AND_DRINK': 'food_dining',
        'GROCERIES': 'groceries',
        'RESTAURANT': 'food_dining',
        'FAST_FOOD': 'food_dining',
        'COFFEE_SHOP': 'food_dining',
        'BARS': 'entertainment',
        
        # Transportation
        'TRANSPORTATION': 'transportation',
        'GAS': 'transportation',
        'PARKING': 'transportation',
        'PUBLIC_TRANSPORTATION': 'transportation',
        'TAXI': 'transportation',
        'TOLLS': 'transportation',
        'UBER': 'transportation',
        'AUTO_AND_VEHICLES': 'transportation',
        'AUTO_INSURANCE': 'insurance',
        
        # Shopping
        'SHOPPING': 'shopping',
        'CLOTHING': 'shopping',
        'ELECTRONICS': 'shopping',
        'HOME': 'home',
        'HOME_IMPROVEMENT': 'home',
        'PHARMACY': 'health',
        
        # Bills & Utilities
        'BILLS_AND_UTILITIES': 'utilities',
        'MOBILE_PHONE': 'utilities',
        'INTERNET': 'utilities',
        'ELECTRICITY': 'utilities',
        'WATER': 'utilities',
        'CABLE_TV': 'utilities',
        'RENT': 'housing',
        'MORTGAGE': 'housing',
        
        # Financial
        'TRANSFER': 'transfer',
        'DEPOSIT': 'income',
        'WITHDRAWAL': 'cash',
        'BANK_FEES': 'fees',
        'INTEREST': 'fees',
        'INVESTMENT': 'investments',
        'LOAN_PAYMENT': 'loans',
        'CREDIT_CARD_PAYMENT': 'credit_card',
        
        # Entertainment & Services
        'ENTERTAINMENT': 'entertainment',
        'MOVIES': 'entertainment',
        'MUSIC': 'entertainment',
        'GAMES': 'entertainment',
        'SPORTS': 'entertainment',
        'TRAVEL': 'travel',
        'HOTEL': 'travel',
        'VACATION': 'travel',
        
        # Health & Wellness
        'HEALTH_AND_FITNESS': 'health',
        'DOCTOR': 'health',
        'DENTIST': 'health',
        'HOSPITAL': 'health',
        'GYM': 'health',
        'PERSONAL_CARE': 'personal_care',
        'HAIR': 'personal_care',
        'SPA': 'personal_care',
        
        # Education
        'EDUCATION': 'education',
        'BOOKS': 'education',
        'TUITION': 'education',
        'STUDENT_LOAN': 'education',
        
        # Business & Work
        'BUSINESS_SERVICES': 'business',
        'ADVERTISING': 'business',
        'OFFICE_SUPPLIES': 'business',
        'SHIPPING': 'business',
        
        # Others
        'DONATION': 'donations',
        'GIFT': 'gifts',
        'TAXES': 'taxes',
        'INSURANCE': 'insurance',
        'LEGAL': 'legal',
        'CHILDCARE': 'family',
        'PET': 'pets',
        'OTHER': 'other',
        'UNCATEGORIZED': 'other'
    }
    
    # Default category names and icons
    DEFAULT_CATEGORIES = {
        'food_dining': {'name': 'Alimentação', 'icon': 'utensils', 'color': '#FF6B6B'},
        'groceries': {'name': 'Supermercado', 'icon': 'shopping-cart', 'color': '#4ECDC4'},
        'transportation': {'name': 'Transporte', 'icon': 'car', 'color': '#45B7D1'},
        'shopping': {'name': 'Compras', 'icon': 'shopping-bag', 'color': '#96CEB4'},
        'health': {'name': 'Saúde', 'icon': 'heart', 'color': '#FF6B9D'},
        'utilities': {'name': 'Contas e Serviços', 'icon': 'file-invoice', 'color': '#C44569'},
        'housing': {'name': 'Moradia', 'icon': 'home', 'color': '#574B90'},
        'entertainment': {'name': 'Lazer', 'icon': 'gamepad', 'color': '#F7DC6F'},
        'education': {'name': 'Educação', 'icon': 'graduation-cap', 'color': '#52B788'},
        'home': {'name': 'Casa', 'icon': 'couch', 'color': '#E8B4B8'},
        'personal_care': {'name': 'Cuidados Pessoais', 'icon': 'spa', 'color': '#A8E6CF'},
        'travel': {'name': 'Viagem', 'icon': 'plane', 'color': '#7FCDCD'},
        'business': {'name': 'Negócios', 'icon': 'briefcase', 'color': '#6C5B7B'},
        'income': {'name': 'Receitas', 'icon': 'dollar-sign', 'color': '#2ECC71'},
        'transfer': {'name': 'Transferências', 'icon': 'exchange-alt', 'color': '#3498DB'},
        'cash': {'name': 'Dinheiro', 'icon': 'money-bill', 'color': '#95A5A6'},
        'fees': {'name': 'Taxas', 'icon': 'percentage', 'color': '#E74C3C'},
        'investments': {'name': 'Investimentos', 'icon': 'chart-line', 'color': '#8E44AD'},
        'loans': {'name': 'Empréstimos', 'icon': 'hand-holding-usd', 'color': '#D35400'},
        'credit_card': {'name': 'Cartão de Crédito', 'icon': 'credit-card', 'color': '#2C3E50'},
        'insurance': {'name': 'Seguros', 'icon': 'shield-alt', 'color': '#16A085'},
        'donations': {'name': 'Doações', 'icon': 'hands-helping', 'color': '#E91E63'},
        'gifts': {'name': 'Presentes', 'icon': 'gift', 'color': '#9C27B0'},
        'taxes': {'name': 'Impostos', 'icon': 'receipt', 'color': '#795548'},
        'legal': {'name': 'Legal', 'icon': 'balance-scale', 'color': '#607D8B'},
        'family': {'name': 'Família', 'icon': 'users', 'color': '#FF5722'},
        'pets': {'name': 'Pets', 'icon': 'paw', 'color': '#00BCD4'},
        'other': {'name': 'Outros', 'icon': 'ellipsis-h', 'color': '#9E9E9E'}
    }
    
    def __init__(self):
        self._ensure_default_categories()
    
    def _ensure_default_categories(self):
        """
        Ensure all default categories exist in the database
        """
        for slug, data in self.DEFAULT_CATEGORIES.items():
            TransactionCategory.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': data['name'],
                    'icon': data['icon'],
                    'color': data['color'],
                    'is_system': True,
                    'is_active': True
                }
            )
    
    def get_or_create_category(self, pluggy_category: str) -> Optional[TransactionCategory]:
        """
        Get or create a category based on Pluggy category string
        """
        if not pluggy_category:
            return None
        
        # Check cache first
        cache_key = f'pluggy_category_map_{pluggy_category}'
        cached_category_id = cache.get(cache_key)
        
        if cached_category_id:
            try:
                return TransactionCategory.objects.get(id=cached_category_id)
            except TransactionCategory.DoesNotExist:
                cache.delete(cache_key)
        
        # Map Pluggy category to our category slug
        internal_slug = self.CATEGORY_MAPPING.get(
            pluggy_category.upper(),
            'other'  # Default to 'other' if not mapped
        )
        
        # Get or create the category
        try:
            category = TransactionCategory.objects.get(slug=internal_slug)
            cache.set(cache_key, category.id, 3600)  # Cache for 1 hour
            return category
        except TransactionCategory.DoesNotExist:
            # This shouldn't happen if _ensure_default_categories worked
            logger.error(f"Category not found: {internal_slug}")
            
            # Create it on the fly
            default_data = self.DEFAULT_CATEGORIES.get(internal_slug, self.DEFAULT_CATEGORIES['other'])
            category = TransactionCategory.objects.create(
                slug=internal_slug,
                name=default_data['name'],
                icon=default_data['icon'],
                color=default_data['color'],
                is_system=True,
                is_active=True
            )
            
            cache.set(cache_key, category.id, 3600)
            return category
    
    def map_categories_bulk(self, pluggy_categories: list) -> dict:
        """
        Map multiple Pluggy categories at once
        Returns a dict mapping pluggy_category -> TransactionCategory
        """
        result = {}
        
        for pluggy_cat in pluggy_categories:
            if pluggy_cat:
                category = self.get_or_create_category(pluggy_cat)
                if category:
                    result[pluggy_cat] = category
        
        return result