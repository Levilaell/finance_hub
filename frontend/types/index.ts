// User and Authentication - Actively Used Types
export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_active: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  avatar?: string;
  date_of_birth?: string;
  last_login_ip?: string;
  preferred_language: 'pt-br' | 'en';
  timezone: string;
  is_two_factor_enabled: boolean;
  two_factor_secret?: string;
  backup_codes: string[];
  payment_gateway?: 'stripe';
  created_at: string;
  updated_at: string;

  // Company relationship
  company?: any; // Simplified reference

  // Computed properties
  full_name?: string;
  initials?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password2: string;
  first_name: string;
  last_name: string;
  company_name: string;
  company_cnpj: string;
  company_type: string;
  business_sector: string;
  phone: string;
  selected_plan?: string;
}

export interface LoginResponse {
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
  requires_2fa?: boolean;
}

// Re-export banking types
export * from './banking';












