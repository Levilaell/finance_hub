/**
 * Meta Pixel tracking utilities
 * Use these functions to track custom events throughout your application
 */

import { PIXEL_ID } from '@/components/PixelTracker';

export { PIXEL_ID };

// Standard Meta Pixel events
export const META_EVENTS = {
  PAGE_VIEW: 'PageView',
  LEAD: 'Lead',
  COMPLETE_REGISTRATION: 'CompleteRegistration',
  CONTACT: 'Contact',
  SUBMIT_APPLICATION: 'SubmitApplication',
  SCHEDULE: 'Schedule',
  START_TRIAL: 'StartTrial',
  SUBSCRIBE: 'Subscribe',
  ADD_PAYMENT_INFO: 'AddPaymentInfo',
  ADD_TO_CART: 'AddToCart',
  PURCHASE: 'Purchase',
  VIEW_CONTENT: 'ViewContent',
} as const;

interface MetaPixelEventParams {
  content_name?: string;
  content_category?: string;
  value?: number;
  currency?: string;
  status?: string;
  [key: string]: any;
}

/**
 * Track a standard Meta Pixel event
 * @param eventName - The name of the event (use META_EVENTS constants)
 * @param params - Optional event parameters
 */
export const trackEvent = (eventName: string, params?: MetaPixelEventParams) => {
  if (typeof window !== 'undefined' && window.fbq) {
    if (params) {
      window.fbq('track', eventName, params);
    } else {
      window.fbq('track', eventName);
    }
  } else {
    console.warn('Meta Pixel not loaded yet');
  }
};

/**
 * Track a custom Meta Pixel event
 * @param eventName - The name of your custom event
 * @param params - Optional event parameters
 */
export const trackCustomEvent = (eventName: string, params?: MetaPixelEventParams) => {
  if (typeof window !== 'undefined' && window.fbq) {
    // @ts-ignore - trackCustom is a valid fbq action
    window.fbq('trackCustom', eventName, params);
  } else {
    console.warn('Meta Pixel not loaded yet');
  }
};

/**
 * Track PageView (already handled automatically by PixelTracker)
 */
export const trackPageView = () => {
  trackEvent(META_EVENTS.PAGE_VIEW);
};

/**
 * Track user registration/sign up
 */
export const trackRegistration = (params?: { status?: string }) => {
  trackEvent(META_EVENTS.COMPLETE_REGISTRATION, params);
};

/**
 * Track lead generation (form submission, contact, etc.)
 */
export const trackLead = (params?: { content_name?: string; value?: number; currency?: string }) => {
  trackEvent(META_EVENTS.LEAD, params);
};

/**
 * Track contact form submission
 */
export const trackContact = (params?: { content_name?: string }) => {
  trackEvent(META_EVENTS.CONTACT, params);
};

/**
 * Track subscription/plan selection
 */
export const trackSubscribe = (params?: { value?: number; currency?: string; predicted_ltv?: number }) => {
  trackEvent(META_EVENTS.SUBSCRIBE, params);
};

/**
 * Track payment info added
 */
export const trackAddPaymentInfo = (params?: { content_category?: string; value?: number; currency?: string }) => {
  trackEvent(META_EVENTS.ADD_PAYMENT_INFO, params);
};

/**
 * Track purchase/transaction
 */
export const trackPurchase = (params: { value: number; currency: string; content_name?: string }) => {
  trackEvent(META_EVENTS.PURCHASE, params);
};

/**
 * Track content view
 */
export const trackViewContent = (params?: { content_name?: string; content_category?: string }) => {
  trackEvent(META_EVENTS.VIEW_CONTENT, params);
};
