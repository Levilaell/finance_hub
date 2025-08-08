/**
 * API-related constants
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/auth/login/',
  LOGOUT: '/api/auth/logout/',
  REGISTER: '/api/auth/register/',
  REFRESH_TOKEN: '/api/auth/refresh/',
  USER_PROFILE: '/api/auth/profile/',
  
  // Banking
  ACCOUNTS: '/api/banking/accounts/',
  TRANSACTIONS: '/api/banking/transactions/',
  CONNECTORS: '/api/banking/connectors/',
  ITEMS: '/api/banking/items/',
  CONNECT_TOKEN: '/api/banking/connect-token/',
  CATEGORIES: '/api/banking/categories/',
  
  // Companies
  COMPANIES: '/api/companies/',
  COMPANY_USERS: '/api/companies/users/',
  SUBSCRIPTION: '/api/companies/subscription/',
  
  // Reports
  REPORTS: '/api/reports/',
  AI_ANALYSIS: '/api/reports/ai-analysis/',
} as const;

export const API_TIMEOUT = 30000; // 30 seconds

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
} as const;