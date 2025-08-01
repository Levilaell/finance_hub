/**
 * Test setup and configuration
 */

import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

// Polyfill for TextEncoder/TextDecoder (needed for JWT decoding)
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';

// Mock fetch globally
global.fetch = jest.fn();

// Mock window.location
const mockLocation = {
  href: 'http://localhost:3000',
  pathname: '/',
  search: '',
  hash: '',
  replace: jest.fn(),
  assign: jest.fn(),
  reload: jest.fn(),
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

// Mock document.cookie
Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});

// Mock CustomEvent
global.CustomEvent = class CustomEvent extends Event {
  public detail: any;
  
  constructor(type: string, options?: { detail?: any }) {
    super(type);
    this.detail = options?.detail;
  }
} as any;

// Mock timers for async operations
jest.useFakeTimers();

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
  localStorage.clear();
  sessionStorage.clear();
  
  // Reset location mock
  mockLocation.href = 'http://localhost:3000';
  mockLocation.pathname = '/';
  mockLocation.search = '';
  mockLocation.hash = '';
  
  // Reset document.cookie
  document.cookie = '';
  
  // Clear fetch mock
  (fetch as jest.Mock).mockClear();
});

// Setup default fetch mock responses
beforeEach(() => {
  (fetch as jest.Mock).mockImplementation(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
      headers: new Headers(),
    })
  );
});

export default {};