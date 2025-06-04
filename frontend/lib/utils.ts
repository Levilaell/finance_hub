import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string = "BRL"): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: currency,
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  // Ensure consistent date parsing by treating string dates as UTC
  const d = typeof date === 'string' 
    ? new Date(date + (date.includes('T') ? '' : 'T00:00:00.000Z'))
    : new Date(date);
    
  if (isNaN(d.getTime())) {
    return "Data inválida";
  }
  
  return new Intl.DateTimeFormat("pt-BR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC" // Force UTC to ensure consistency between server and client
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