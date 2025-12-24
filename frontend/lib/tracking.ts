// frontend/lib/tracking.ts
// Tracking via dataLayer para GTM → Server-Side → Meta CAPI

// Tipo para dados do usuário (Meta CAPI Enhanced Match)
export type UserData = {
  email?: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
};

// Tipo para user_data formatado para Meta CAPI
type FormattedUserData = {
  em?: string;
  ph?: string;
  fn?: string;
  ln?: string;
};

// Função helper para formatar user_data para Meta CAPI
const formatUserData = (userData?: UserData): FormattedUserData | undefined => {
  if (!userData) return undefined;
  return {
    em: userData.email?.toLowerCase().trim(),
    ph: userData.phone?.replace(/\D/g, ''),
    fn: userData.firstName?.toLowerCase().trim(),
    ln: userData.lastName?.toLowerCase().trim(),
  };
};

export const pushEvent = (eventName: string, params?: Record<string, any>) => {
  if (typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: eventName,
      ...params,
    });
  }
};

// Armazena dados do usuário no dataLayer para Enhanced Match
export const setUserData = (userData: UserData) => {
  if (typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: 'set_user_data',
      user_data: {
        email: userData.email?.toLowerCase().trim(),
        phone_number: userData.phone?.replace(/\D/g, ''),
        address: {
          first_name: userData.firstName?.toLowerCase().trim(),
          last_name: userData.lastName?.toLowerCase().trim(),
        }
      }
    });
  }
};

export const trackPageView = (pageName: string, category?: string) => {
  pushEvent('page_view', {
    page_name: pageName,
    page_category: category,
  });
};

export const trackLead = (params?: {
  content_name?: string;
  value?: number;
  currency?: string;
  user_data?: UserData;
}) => {
  pushEvent('lead', {
    content_name: params?.content_name,
    value: params?.value || 0,
    currency: params?.currency || 'BRL',
    user_data: formatUserData(params?.user_data),
  });
};

export const trackCompleteRegistration = (params?: {
  status?: string;
  user_data?: UserData;
}) => {
  pushEvent('complete_registration', {
    status: params?.status,
    user_data: formatUserData(params?.user_data),
  });
};

export const trackStartTrial = (params?: {
  value?: number;
  currency?: string;
  content_name?: string;
  user_data?: UserData;
}) => {
  pushEvent('start_trial', {
    value: params?.value || 197,
    currency: params?.currency || 'BRL',
    content_name: params?.content_name || 'CaixaHub Trial 7 dias',
    user_data: formatUserData(params?.user_data),
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
