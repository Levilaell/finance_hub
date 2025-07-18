/**
 * Brazilian document validation utilities
 */

/**
 * Validate CNPJ (Brazilian company registration number)
 */
export function validateCNPJ(cnpj: string): boolean {
  // Remove non-numeric characters
  const cleanCNPJ = cnpj.replace(/[^\d]/g, '');

  // CNPJ must have 14 digits
  if (cleanCNPJ.length !== 14) {
    return false;
  }

  // Known invalid CNPJs
  if (/^(\d)\1+$/.test(cleanCNPJ)) {
    return false;
  }

  // Calculate first check digit
  let sum = 0;
  let weight = 5;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(cleanCNPJ[i]) * weight;
    weight = weight === 2 ? 9 : weight - 1;
  }

  let digit = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (parseInt(cleanCNPJ[12]) !== digit) {
    return false;
  }

  // Calculate second check digit
  sum = 0;
  weight = 6;
  for (let i = 0; i < 13; i++) {
    sum += parseInt(cleanCNPJ[i]) * weight;
    weight = weight === 2 ? 9 : weight - 1;
  }

  digit = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (parseInt(cleanCNPJ[13]) !== digit) {
    return false;
  }

  return true;
}

/**
 * Format CNPJ to XX.XXX.XXX/XXXX-XX
 */
export function formatCNPJ(cnpj: string): string {
  const cleanCNPJ = cnpj.replace(/[^\d]/g, '');
  
  if (cleanCNPJ.length !== 14) {
    return cnpj;
  }

  return cleanCNPJ.replace(
    /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
    '$1.$2.$3/$4-$5'
  );
}

/**
 * CNPJ input mask
 */
export function cnpjMask(value: string): string {
  const cleanValue = value.replace(/[^\d]/g, '');
  
  if (cleanValue.length <= 2) {
    return cleanValue;
  } else if (cleanValue.length <= 5) {
    return cleanValue.replace(/(\d{2})(\d)/, '$1.$2');
  } else if (cleanValue.length <= 8) {
    return cleanValue.replace(/(\d{2})(\d{3})(\d)/, '$1.$2.$3');
  } else if (cleanValue.length <= 12) {
    return cleanValue.replace(/(\d{2})(\d{3})(\d{3})(\d)/, '$1.$2.$3/$4');
  } else {
    return cleanValue.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d)/, '$1.$2.$3/$4-$5');
  }
}

/**
 * Validate Brazilian phone number
 */
export function validatePhone(phone: string): boolean {
  const cleanPhone = phone.replace(/[^\d]/g, '');

  // Brazilian phone must have 10 or 11 digits
  if (cleanPhone.length < 10 || cleanPhone.length > 11) {
    return false;
  }

  // Valid Brazilian area codes
  const validAreaCodes = [
    '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '21', '22', '24', '27', '28',
    '31', '32', '33', '34', '35', '37', '38',
    '41', '42', '43', '44', '45', '46',
    '47', '48', '49',
    '51', '53', '54', '55',
    '61', '62', '63', '64', '65', '66', '67', '68', '69',
    '71', '73', '74', '75', '77', '79',
    '81', '82', '83', '84', '85', '86', '87', '88', '89',
    '91', '92', '93', '94', '95', '96', '97', '98', '99'
  ];

  const areaCode = cleanPhone.substring(0, 2);
  if (!validAreaCodes.includes(areaCode)) {
    return false;
  }

  // For mobile numbers (11 digits), the 3rd digit must be 9
  if (cleanPhone.length === 11 && cleanPhone[2] !== '9') {
    return false;
  }

  return true;
}

/**
 * Format phone to (XX) XXXXX-XXXX or (XX) XXXX-XXXX
 */
export function formatPhone(phone: string): string {
  const cleanPhone = phone.replace(/[^\d]/g, '');

  if (cleanPhone.length === 11) {
    return cleanPhone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  } else if (cleanPhone.length === 10) {
    return cleanPhone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }

  return phone;
}

/**
 * Phone input mask
 */
export function phoneMask(value: string): string {
  const cleanValue = value.replace(/[^\d]/g, '');
  
  if (cleanValue.length <= 2) {
    return cleanValue.length > 0 ? `(${cleanValue}` : '';
  } else if (cleanValue.length <= 6) {
    return `(${cleanValue.slice(0, 2)}) ${cleanValue.slice(2)}`;
  } else if (cleanValue.length <= 10) {
    return `(${cleanValue.slice(0, 2)}) ${cleanValue.slice(2, 6)}-${cleanValue.slice(6)}`;
  } else {
    return `(${cleanValue.slice(0, 2)}) ${cleanValue.slice(2, 7)}-${cleanValue.slice(7, 11)}`;
  }
}