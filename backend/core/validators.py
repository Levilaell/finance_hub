# core/validators.py
"""
Centralized validators for the entire application
Avoids duplication and ensures consistency
"""
import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

# Import common validators
from .common_validators import (
    validate_cnpj as _validate_cnpj,
    validate_phone as _validate_phone,
    validate_email_unique as _validate_email_unique,
    format_cnpj,
    format_phone,
    format_cpf,
    validate_cpf
)


# Re-export common validators with the same interface
validate_cnpj = _validate_cnpj


validate_phone = _validate_phone


validate_email_unique = _validate_email_unique


def validate_password_strength(password):
    """
    Validates password strength according to security requirements
    """
    errors = []
    
    if len(password) < 8:
        errors.append(_('A senha deve ter pelo menos 8 caracteres.'))
    
    if len(password) > 128:
        errors.append(_('A senha não pode ter mais de 128 caracteres.'))
    
    if not re.search(r'[A-Z]', password):
        errors.append(_('A senha deve conter pelo menos uma letra maiúscula.'))
    
    if not re.search(r'[a-z]', password):
        errors.append(_('A senha deve conter pelo menos uma letra minúscula.'))
    
    if not re.search(r'[0-9]', password):
        errors.append(_('A senha deve conter pelo menos um número.'))
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append(_('A senha deve conter pelo menos um caractere especial.'))
    
    # Check for common weak passwords
    weak_passwords = [
        '12345678', 'password', 'senha123', '123456789',
        'qwerty123', 'admin123', 'password123'
    ]
    if password.lower() in weak_passwords:
        errors.append(_('Esta senha é muito comum. Escolha uma senha mais forte.'))
    
    if errors:
        raise ValidationError(errors)


def validate_monetary_value(value, min_value=None, max_value=None):
    """
    Validates monetary values with consistent rules
    """
    if value is None:
        return
    
    # Convert to Decimal for precise handling
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except (ValueError, TypeError):
            raise ValidationError(_('Valor monetário inválido.'))
    
    # Check minimum value
    if min_value is not None and value < Decimal(str(min_value)):
        raise ValidationError(_(f'Valor deve ser maior ou igual a {min_value}.'))
    
    # Check maximum value
    if max_value is not None and value > Decimal(str(max_value)):
        raise ValidationError(_(f'Valor deve ser menor ou igual a {max_value}.'))
    
    # Check decimal places (max 2 for currency)
    if value.as_tuple().exponent < -2:
        raise ValidationError(_('Valor monetário deve ter no máximo 2 casas decimais.'))


def validate_credit_card_number(card_number):
    """
    Validates credit card number using Luhn algorithm
    """
    if not card_number:
        return
    
    # Remove spaces and non-numeric characters
    card_number = re.sub(r'[^0-9]', '', str(card_number))
    
    # Check length
    if len(card_number) < 13 or len(card_number) > 19:
        raise ValidationError(_('Número do cartão deve ter entre 13 e 19 dígitos.'))
    
    # Luhn algorithm validation
    def luhn_check(card_num):
        total = 0
        reverse_digits = card_num[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:  # Every second digit from right
                n *= 2
                if n > 9:
                    n = n // 10 + n % 10
            total += n
        
        return total % 10 == 0
    
    if not luhn_check(card_number):
        raise ValidationError(_('Número do cartão inválido.'))


def validate_date_range(start_date, end_date):
    """
    Validates that start_date is before end_date
    """
    if start_date and end_date and start_date >= end_date:
        raise ValidationError(_('A data de início deve ser anterior à data de fim.'))


def validate_business_hours(time_str):
    """
    Validates business hours format (HH:MM)
    """
    if not time_str:
        return
    
    time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(time_pattern, time_str):
        raise ValidationError(_('Formato de horário inválido. Use HH:MM (ex: 09:00).'))


def validate_percentage(value):
    """
    Validates percentage values (0-100)
    """
    if value is None:
        return
    
    try:
        percentage = float(value)
    except (ValueError, TypeError):
        raise ValidationError(_('Porcentagem deve ser um número.'))
    
    if percentage < 0 or percentage > 100:
        raise ValidationError(_('Porcentagem deve estar entre 0 e 100.'))


def validate_company_size(employee_count):
    """
    Validates employee count for business classification
    """
    if employee_count is None:
        return
    
    if employee_count < 1:
        raise ValidationError(_('Número de funcionários deve ser maior que zero.'))
    
    if employee_count > 10000:
        raise ValidationError(_('Para empresas com mais de 10.000 funcionários, entre em contato conosco.'))


def validate_file_size(file, max_size_mb=5):
    """
    Validates file size
    """
    if file and hasattr(file, 'size'):
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise ValidationError(_(f'Arquivo muito grande. Tamanho máximo: {max_size_mb}MB.'))


def validate_image_dimensions(image, max_width=1920, max_height=1080):
    """
    Validates image dimensions
    """
    if image and hasattr(image, 'width') and hasattr(image, 'height'):
        if image.width > max_width or image.height > max_height:
            raise ValidationError(
                _(f'Imagem muito grande. Dimensões máximas: {max_width}x{max_height} pixels.'))