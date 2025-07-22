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


def validate_cnpj(value):
    """
    Validates Brazilian CNPJ (Corporate Taxpayer Registry)
    """
    if not value:
        return
        
    # Remove non-numeric characters
    cnpj = re.sub(r'[^0-9]', '', str(value))
    
    # Check length
    if len(cnpj) != 14:
        raise ValidationError(_('CNPJ deve conter 14 dígitos.'))
    
    # Check for sequential numbers (invalid CNPJs)
    if cnpj in ['00000000000000', '11111111111111', '22222222222222',
                '33333333333333', '44444444444444', '55555555555555',
                '66666666666666', '77777777777777', '88888888888888',
                '99999999999999']:
        raise ValidationError(_('CNPJ inválido.'))
    
    # Validate check digits
    def calculate_digit(cnpj_partial, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # First check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit1 = calculate_digit(cnpj[:12], weights1)
    
    # Second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit2 = calculate_digit(cnpj[:13], weights2)
    
    if int(cnpj[12]) != digit1 or int(cnpj[13]) != digit2:
        raise ValidationError(_('CNPJ inválido.'))


def validate_phone(value):
    """
    Validates Brazilian phone numbers
    """
    if not value:
        return
        
    # Remove non-numeric characters
    phone = re.sub(r'[^0-9]', '', str(value))
    
    # Check length (10-11 digits)
    if len(phone) < 10 or len(phone) > 11:
        raise ValidationError(_('Telefone deve ter 10 ou 11 dígitos.'))
    
    # Check if starts with valid area code (11-99)
    if len(phone) >= 2:
        area_code = int(phone[:2])
        if area_code < 11 or area_code > 99:
            raise ValidationError(_('Código de área inválido.'))
    
    # For 11-digit numbers, 9th digit must be 9 (mobile)
    if len(phone) == 11 and phone[2] != '9':
        raise ValidationError(_('Para celular, o número deve começar com 9.'))


def validate_email_unique(email, exclude_user=None):
    """
    Validates email uniqueness
    """
    User = get_user_model()
    queryset = User.objects.filter(email=email)
    
    if exclude_user:
        queryset = queryset.exclude(pk=exclude_user.pk)
    
    if queryset.exists():
        raise ValidationError(_('Este e-mail já está cadastrado.'))


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