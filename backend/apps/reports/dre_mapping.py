"""
DRE (Demonstrativo de Resultado do Exercício) mapping configuration.

Maps Pluggy category IDs to DRE groups for financial reporting.
Based on Brazilian accounting standards for SMEs (NBC TG 1000).
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DREGroup(Enum):
    """DRE group identifiers."""
    RECEITAS_OPERACIONAIS = "receitas_operacionais"
    RECEITAS_FINANCEIRAS = "receitas_financeiras"
    DESPESAS_OPERACIONAIS = "despesas_operacionais"
    DESPESAS_FINANCEIRAS = "despesas_financeiras"
    EXCLUIDAS = "excluidas"  # Transfers, investments (not income/expense)


@dataclass
class DREGroupConfig:
    """Configuration for a DRE group."""
    id: str
    name: str
    name_en: str
    sign: str  # '+' for income, '-' for expenses
    order: int  # Display order in report
    pluggy_prefixes: List[str]  # Category ID prefixes to match
    pluggy_ids: List[str]  # Specific category IDs to match
    except_ids: List[str]  # IDs to exclude from this group
    fallback_type: Optional[str]  # Transaction type for fallback ('CREDIT' or 'DEBIT')


# DRE Group configurations
DRE_GROUPS: Dict[str, DREGroupConfig] = {
    DREGroup.RECEITAS_OPERACIONAIS.value: DREGroupConfig(
        id=DREGroup.RECEITAS_OPERACIONAIS.value,
        name="Receitas Operacionais",
        name_en="Operating Revenue",
        sign="+",
        order=1,
        pluggy_prefixes=["01"],  # Income category
        pluggy_ids=[],
        except_ids=[],
        fallback_type="CREDIT",  # Uncategorized CREDIT transactions
    ),
    DREGroup.RECEITAS_FINANCEIRAS.value: DREGroupConfig(
        id=DREGroup.RECEITAS_FINANCEIRAS.value,
        name="Receitas Financeiras",
        name_en="Financial Revenue",
        sign="+",
        order=4,
        pluggy_prefixes=[],
        pluggy_ids=["03060000"],  # Proceeds, interests and dividends
        except_ids=[],
        fallback_type=None,
    ),
    DREGroup.DESPESAS_OPERACIONAIS.value: DREGroupConfig(
        id=DREGroup.DESPESAS_OPERACIONAIS.value,
        name="Despesas Operacionais",
        name_en="Operating Expenses",
        sign="-",
        order=2,
        pluggy_prefixes=[
            "06",  # Legal obligations
            "07",  # Services (telecom, education, wellness)
            "08",  # Shopping
            "09",  # Digital services
            "10",  # Groceries
            "11",  # Food and drinks
            "12",  # Travel
            "13",  # Donations
            "14",  # Gambling
            "15",  # Taxes
            "17",  # Housing
            "18",  # Healthcare
            "19",  # Transportation
            "20",  # Insurance
            "21",  # Leisure
            "99",  # Other
        ],
        pluggy_ids=["05100000"],  # Credit card payment (operational)
        except_ids=[],
        fallback_type="DEBIT",  # Uncategorized DEBIT transactions
    ),
    DREGroup.DESPESAS_FINANCEIRAS.value: DREGroupConfig(
        id=DREGroup.DESPESAS_FINANCEIRAS.value,
        name="Despesas Financeiras",
        name_en="Financial Expenses",
        sign="-",
        order=3,
        pluggy_prefixes=[
            "02",  # Loans and financing
            "16",  # Bank fees
        ],
        pluggy_ids=[],
        except_ids=[],
        fallback_type=None,
    ),
    DREGroup.EXCLUIDAS.value: DREGroupConfig(
        id=DREGroup.EXCLUIDAS.value,
        name="Movimentações Excluídas",
        name_en="Excluded Movements",
        sign="",
        order=99,
        pluggy_prefixes=[
            "03",  # Investments (except dividends)
            "04",  # Same person transfer
            "05",  # Transfers (except credit card payment)
        ],
        pluggy_ids=[],
        except_ids=[
            "03060000",  # Dividends go to financial revenue
            "05100000",  # Credit card payment goes to operational
        ],
        fallback_type=None,
    ),
}


def get_dre_group_for_category(
    pluggy_category_id: Optional[str],
    transaction_type: str
) -> Optional[str]:
    """
    Determine which DRE group a transaction belongs to based on its category.

    Args:
        pluggy_category_id: The Pluggy category ID (e.g., "01010000")
        transaction_type: "CREDIT" or "DEBIT"

    Returns:
        DRE group ID or None if transaction should be excluded
    """
    if not pluggy_category_id:
        # Fallback for uncategorized transactions
        if transaction_type == "CREDIT":
            return DREGroup.RECEITAS_OPERACIONAIS.value
        elif transaction_type == "DEBIT":
            return DREGroup.DESPESAS_OPERACIONAIS.value
        return None

    # Check each group for matching category
    for group_id, config in DRE_GROUPS.items():
        if group_id == DREGroup.EXCLUIDAS.value:
            continue  # Check excluded last

        # Check specific IDs first
        if pluggy_category_id in config.pluggy_ids:
            return group_id

        # Check prefixes
        for prefix in config.pluggy_prefixes:
            if pluggy_category_id.startswith(prefix):
                # Make sure it's not in except_ids
                if pluggy_category_id not in config.except_ids:
                    return group_id

    # Check if it should be excluded
    excluded_config = DRE_GROUPS[DREGroup.EXCLUIDAS.value]
    for prefix in excluded_config.pluggy_prefixes:
        if pluggy_category_id.startswith(prefix):
            if pluggy_category_id not in excluded_config.except_ids:
                return None  # Exclude from DRE

    # Final fallback based on transaction type
    if transaction_type == "CREDIT":
        return DREGroup.RECEITAS_OPERACIONAIS.value
    elif transaction_type == "DEBIT":
        return DREGroup.DESPESAS_OPERACIONAIS.value

    return None


def get_dre_structure() -> List[Dict]:
    """
    Get the DRE structure for display.

    Returns:
        List of DRE groups in display order
    """
    groups = []
    for group_id, config in sorted(DRE_GROUPS.items(), key=lambda x: x[1].order):
        if group_id != DREGroup.EXCLUIDAS.value:
            groups.append({
                "id": config.id,
                "name": config.name,
                "name_en": config.name_en,
                "sign": config.sign,
                "order": config.order,
            })
    return groups


# Mapping of Pluggy category IDs to translated names (for display)
PLUGGY_CATEGORY_TRANSLATIONS = {
    # Income
    "01000000": "Renda",
    "01010000": "Salário",
    "01020000": "Aposentadoria",
    "01030000": "Atividades de Empreendedorismo",
    "01040000": "Auxílio do Governo",
    "01050000": "Renda Não-recorrente",

    # Loans and financing
    "02000000": "Empréstimos e Financiamento",
    "02010000": "Atraso e Cheque Especial",
    "02020000": "Juros Cobrados",
    "02030000": "Financiamento",
    "02040000": "Empréstimos",

    # Investments
    "03000000": "Investimentos",
    "03060000": "Dividendos e Rendimentos",

    # Services
    "07000000": "Serviços",
    "07010000": "Telecomunicação",
    "07020000": "Educação",
    "07030000": "Saúde e Bem-estar",

    # Shopping
    "08000000": "Compras",

    # Digital services
    "09000000": "Serviços Digitais",

    # Groceries
    "10000000": "Supermercado",

    # Food and drinks
    "11000000": "Alimentação",
    "11010000": "Restaurantes e Bares",
    "11020000": "Delivery",

    # Travel
    "12000000": "Viagens",

    # Taxes
    "15000000": "Impostos",

    # Bank fees
    "16000000": "Taxas Bancárias",

    # Housing
    "17000000": "Moradia",
    "17010000": "Aluguel",
    "17020000": "Utilidades",

    # Healthcare
    "18000000": "Saúde",

    # Transportation
    "19000000": "Transporte",
    "19050000": "Serviços Automotivos",

    # Insurance
    "20000000": "Seguros",

    # Leisure
    "21000000": "Lazer",

    # Other
    "99999999": "Outros",
}


def get_category_display_name(
    pluggy_category_id: Optional[str],
    pluggy_category_name: Optional[str] = None
) -> str:
    """
    Get display name for a category, using translation if available.

    Args:
        pluggy_category_id: The Pluggy category ID
        pluggy_category_name: The original category name from Pluggy

    Returns:
        Translated or original category name
    """
    if pluggy_category_id and pluggy_category_id in PLUGGY_CATEGORY_TRANSLATIONS:
        return PLUGGY_CATEGORY_TRANSLATIONS[pluggy_category_id]

    if pluggy_category_name:
        return pluggy_category_name

    return "Outros"


def get_parent_category_id(pluggy_category_id: Optional[str]) -> Optional[str]:
    """
    Get the parent category ID for hierarchical grouping.

    Pluggy uses hierarchical IDs:
    - 01000000 = parent (Income)
    - 01010000 = child (Salary)
    - 01020000 = child (Retirement)

    Args:
        pluggy_category_id: The Pluggy category ID

    Returns:
        Parent category ID or None
    """
    if not pluggy_category_id or len(pluggy_category_id) < 8:
        return None

    # Check if this is already a parent (ends with 000000)
    if pluggy_category_id.endswith("000000"):
        return None

    # Get parent by replacing last 4 digits with 0000
    # e.g., 01010000 -> 01000000
    if pluggy_category_id[4:6] != "00":
        # Third level, get second level parent
        return pluggy_category_id[:4] + "0000"

    # Second level, get first level parent
    return pluggy_category_id[:2] + "000000"
