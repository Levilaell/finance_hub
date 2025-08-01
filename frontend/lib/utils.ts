import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency?: string): string;
export function formatCurrency(amount: number, format: 'compact'): string;
export function formatCurrency(amount: number, currencyOrFormat: string = "BRL"): string {
  if (currencyOrFormat === 'compact') {
    const absAmount = Math.abs(amount);
    const isNegative = amount < 0;
    
    let compactValue: string;
    if (absAmount >= 1_000_000) {
      compactValue = `R$ ${(absAmount / 1_000_000).toFixed(1)}M`;
    } else if (absAmount >= 1_000) {
      compactValue = `R$ ${(absAmount / 1_000).toFixed(1)}k`;
    } else {
      compactValue = `R$ ${absAmount.toFixed(0)}`;
    }
    
    return isNegative ? `-${compactValue}` : compactValue;
  }
  
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currencyOrFormat,
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  // Handle null/undefined
  if (!date) {
    return "Nunca";
  }
  
  let d: Date;
  
  if (typeof date === 'string') {
    // Check if it's in Brazilian format: dd/mm/yyyy hh:mm:ss
    const brazilianFormat = /^(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2}):(\d{2})$/;
    const match = date.match(brazilianFormat);
    
    if (match) {
      // Parse Brazilian format: dd/mm/yyyy hh:mm:ss
      const [, day, month, year, hours, minutes, seconds] = match;
      d = new Date(
        parseInt(year),
        parseInt(month) - 1, // Month is 0-indexed
        parseInt(day),
        parseInt(hours),
        parseInt(minutes),
        parseInt(seconds)
      );
    } else {
      // Try ISO format or other standard formats
      d = new Date(date);
    }
  } else {
    d = date;
  }
    
  if (isNaN(d.getTime())) {
    console.error('formatDate: Invalid date', { date, d });
    return "Data inválida";
  }
  
  // Format relative time
  const now = new Date();
  const diffInMs = now.getTime() - d.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  
  if (diffInMinutes < 1) {
    return "Agora mesmo";
  } else if (diffInMinutes < 60) {
    return `Há ${diffInMinutes} minuto${diffInMinutes !== 1 ? 's' : ''}`;
  } else if (diffInHours < 24) {
    return `Há ${diffInHours} hora${diffInHours !== 1 ? 's' : ''}`;
  } else if (diffInDays < 7) {
    return `Há ${diffInDays} dia${diffInDays !== 1 ? 's' : ''}`;
  }
  
  // For older dates, use absolute format
  return new Intl.DateTimeFormat("pt-BR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(d);
}

export function formatDateTime(date: string | Date): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) {
    return "Data inválida";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), wait);
  };
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