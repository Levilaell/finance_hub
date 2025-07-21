"""
Validators for company-related fields
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cnpj(value):
    """
    Validate Brazilian CNPJ number
    """
    # Remove non-numeric characters
    cnpj = re.sub(r'[^0-9]', '', value)
    
    # CNPJ must have 14 digits
    if len(cnpj) != 14:
        raise ValidationError(
            _('CNPJ deve conter exatamente 14 números. Você digitou {} números.').format(len(cnpj)),
            code='invalid_length'
        )
    
    # Known invalid CNPJs
    if cnpj in [
        '00000000000000', '11111111111111', '22222222222222',
        '33333333333333', '44444444444444', '55555555555555',
        '66666666666666', '77777777777777', '88888888888888',
        '99999999999999'
    ]:
        raise ValidationError(
            _('CNPJ inválido. Não use números repetidos.'),
            code='invalid'
        )
    
    # Calculate first check digit
    sum_digit = 0
    for i in range(12):
        sum_digit += int(cnpj[i]) * (5 - i if i < 4 else 13 - i)
    
    remainder = sum_digit % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    
    if int(cnpj[12]) != digit1:
        raise ValidationError(
            _('CNPJ inválido. Verifique se digitou corretamente.'),
            code='invalid'
        )
    
    # Calculate second check digit
    sum_digit = 0
    for i in range(13):
        sum_digit += int(cnpj[i]) * (6 - i if i < 5 else 14 - i)
    
    remainder = sum_digit % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    
    if int(cnpj[13]) != digit2:
        raise ValidationError(
            _('CNPJ inválido. Verifique se digitou corretamente.'),
            code='invalid'
        )
    
    return cnpj


def format_cnpj(cnpj):
    """
    Format CNPJ to XX.XXX.XXX/XXXX-XX
    """
    # Remove non-numeric characters
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return cnpj
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"


def validate_phone(value):
    """
    Validate Brazilian phone number
    """
    # Remove non-numeric characters
    phone = re.sub(r'[^0-9]', '', value)
    
    # Brazilian phone must have 10 or 11 digits (with area code)
    if len(phone) < 10 or len(phone) > 11:
        raise ValidationError(
            _('Telefone deve ter 10 ou 11 números incluindo DDD. Você digitou {} números. Exemplo: (11) 98765-4321').format(len(phone)),
            code='invalid_length'
        )
    
    # Validate area code (first 2 digits)
    valid_area_codes = [
        11, 12, 13, 14, 15, 16, 17, 18, 19,  # São Paulo
        21, 22, 24,  # Rio de Janeiro
        27, 28,  # Espírito Santo
        31, 32, 33, 34, 35, 37, 38,  # Minas Gerais
        41, 42, 43, 44, 45, 46,  # Paraná
        47, 48, 49,  # Santa Catarina
        51, 53, 54, 55,  # Rio Grande do Sul
        61,  # Distrito Federal
        62, 64,  # Goiás
        63,  # Tocantins
        65, 66,  # Mato Grosso
        67,  # Mato Grosso do Sul
        68,  # Acre
        69,  # Rondônia
        71, 73, 74, 75, 77,  # Bahia
        79,  # Sergipe
        81, 87,  # Pernambuco
        82,  # Alagoas
        83,  # Paraíba
        84,  # Rio Grande do Norte
        85, 88,  # Ceará
        86, 89,  # Piauí
        91, 93, 94,  # Pará
        92, 97,  # Amazonas
        95,  # Roraima
        96,  # Amapá
        98, 99,  # Maranhão
    ]
    
    area_code = int(phone[:2])
    if area_code not in valid_area_codes:
        raise ValidationError(
            _('DDD {} não é válido. Use um código de área brasileiro válido.').format(area_code),
            code='invalid_area_code'
        )
    
    # For mobile numbers (11 digits), the 3rd digit must be 9
    if len(phone) == 11 and phone[2] != '9':
        raise ValidationError(
            _('Celular deve começar com 9 após o DDD. Exemplo: (11) 9xxxx-xxxx'),
            code='invalid_mobile'
        )
    
    return phone


def format_phone(phone):
    """
    Format phone to (XX) XXXXX-XXXX or (XX) XXXX-XXXX
    """
    # Remove non-numeric characters
    phone = re.sub(r'[^0-9]', '', phone)
    
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    
    return phone