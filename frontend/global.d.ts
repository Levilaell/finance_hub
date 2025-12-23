// Global type declarations for the application

declare global {
  interface Window {
    dataLayer: Record<string, any>[];
  }
}

export {};
