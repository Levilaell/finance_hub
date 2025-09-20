"""
Common validators for the entire project
Consolidates validation logic to avoid duplication
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cnpj(value):
    """
    Validates Brazilian CNPJ (Corporate Taxpayer Registry)
    """
    # Remove non-numeric characters
    cnpj = ''.join(filter(str.isdigit, str(value)))
    
    # Check if has 14 digits
    if len(cnpj) != 14:
        raise ValidationError(_('CNPJ deve conter 14 dígitos.'))
    
    # Check for known invalid CNPJs
    if cnpj in ['00000000000000', '11111111111111', '22222222222222', 
                '33333333333333', '44444444444444', '55555555555555',
                '66666666666666', '77777777777777', '88888888888888', 
                '99999999999999']:
        raise ValidationError(_('CNPJ inválido.'))
    
    # Calculate first check digit
    sum = 0
    weight = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(12):
        sum += int(cnpj[i]) * weight[i]
    
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    
    if int(cnpj[12]) != digit:
        raise ValidationError(_('CNPJ inválido.'))
    
    # Calculate second check digit
    sum = 0
    weight = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(13):
        sum += int(cnpj[i]) * weight[i]
    
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    
    if int(cnpj[13]) != digit:
        raise ValidationError(_('CNPJ inválido.'))
    
    return cnpj


def validate_phone(value):
    """
    Validates Brazilian phone numbers
    """
    # Remove non-numeric characters
    phone = ''.join(filter(str.isdigit, str(value)))
    
    # Check length (10 or 11 digits)
    if len(phone) not in [10, 11]:
        raise ValidationError(_('Telefone deve conter 10 ou 11 dígitos.'))
    
    # Check area code (first 2 digits)
    valid_area_codes = [
        '11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
        '21', '22', '24',  # RJ
        '27', '28',  # ES
        '31', '32', '33', '34', '35', '37', '38',  # MG
        '41', '42', '43', '44', '45', '46',  # PR
        '47', '48', '49',  # SC
        '51', '53', '54', '55',  # RS
        '61',  # DF
        '62', '64',  # GO
        '63',  # TO
        '65', '66',  # MT
        '67',  # MS
        '68',  # AC
        '69',  # RO
        '71', '73', '74', '75', '77',  # BA
        '79',  # SE
        '81', '87',  # PE
        '82',  # AL
        '83',  # PB
        '84',  # RN
        '85', '88',  # CE
        '86', '89',  # PI
        '91', '93', '94',  # PA
        '92', '97',  # AM
        '95',  # RR
        '96',  # AP
        '98', '99',  # MA
    ]
    
    if phone[:2] not in valid_area_codes:
        raise ValidationError(_('Código de área inválido.'))
    
    # For mobile (11 digits), third digit must be 9
    if len(phone) == 11 and phone[2] != '9':
        raise ValidationError(_('Para celular, o número deve começar com 9.'))
    
    return phone


def format_cnpj(cnpj):
    """
    Format CNPJ to display format: XX.XXX.XXX/XXXX-XX
    """
    cnpj = ''.join(filter(str.isdigit, str(cnpj)))
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"


def format_phone(phone):
    """
    Format phone to display format: (XX) XXXXX-XXXX or (XX) XXXX-XXXX
    """
    phone = ''.join(filter(str.isdigit, str(phone)))
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    return phone