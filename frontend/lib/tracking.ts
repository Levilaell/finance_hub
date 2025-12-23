// frontend/lib/tracking.ts
// Tracking via dataLayer para GTM → Server-Side → Meta CAPI

declare global {
  interface Window {
    dataLayer: any[];
  }
}

export const pushEvent = (eventName: string, params?: Record<string, any>) => {
  if (typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: eventName,
      ...params,
    });
  }
};

export const trackPageView = (pageName: string, category?: string) => {
  pushEvent('page_view', {
    page_name: pageName,
    page_category: category,
  });
};

export const trackLead = (params?: { content_name?: string; value?: number; currency?: string }) => {
  pushEvent('lead', {
    content_name: params?.content_name,
    value: params?.value || 0,
    currency: params?.currency || 'BRL',
  });
};

export const trackCompleteRegistration = (params?: { status?: string }) => {
  pushEvent('complete_registration', {
    status: params?.status,
  });
};

export const trackStartTrial = (params?: { value?: number; currency?: string; content_name?: string }) => {
  pushEvent('start_trial', {
    value: params?.value || 197,
    currency: params?.currency || 'BRL',
    content_name: params?.content_name || 'CaixaHub Trial 7 dias',
  });
};

export const trackPurchase = (params: { value: number; currency?: string; transaction_id?: string }) => {
  pushEvent('purchase', {
    value: params.value,
    currency: params.currency || 'BRL',
    transaction_id: params.transaction_id,
  });
};

export const trackViewContent = (params?: { content_name?: string; content_category?: string }) => {
  pushEvent('view_content', {
    content_name: params?.content_name,
    content_category: params?.content_category,
  });
};
