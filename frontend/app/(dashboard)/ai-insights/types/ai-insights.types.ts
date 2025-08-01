export interface AICredit {
  id: string;
  balance: number;
  monthly_allowance: number;
  bonus_credits: number;
  last_reset: string;
  total_purchased: number;
  created_at: string;
  updated_at: string;
}

export interface AICreditTransaction {
  id: string;
  type: 'monthly_reset' | 'purchase' | 'bonus' | 'usage' | 'refund' | 'adjustment';
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string;
  metadata: Record<string, any>;
  user?: string;
  conversation?: string;
  message?: string;
  payment_id?: string;
  created_at: string;
}

export interface AIConversation {
  id: string;
  title: string;
  status: 'active' | 'archived' | 'deleted';
  financial_context?: Record<string, any>;
  settings?: Record<string, any>;
  message_count: number;
  total_credits_used: number;
  insights_generated?: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

export interface AIMessage {
  id: string;
  conversation?: string;
  role: 'user' | 'assistant' | 'system';
  type?: 'text' | 'analysis' | 'report' | 'chart' | 'alert';
  content: string;
  credits_used?: number;
  tokens_used?: number;
  model_used?: string;
  structured_data?: any;
  insights?: AIInsightPreview[];
  helpful?: boolean;
  user_feedback?: string;
  created_at: string;
  viewed_at?: string;
}

export interface AIInsight {
  id: string;
  type: 'cost_saving' | 'cash_flow' | 'anomaly' | 'opportunity' | 'risk' | 'trend' | 'benchmark' | 'tax' | 'growth';
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'new' | 'viewed' | 'in_progress' | 'completed' | 'dismissed';
  title: string;
  description: string;
  action_items?: string[];
  data_context?: Record<string, any>;
  potential_impact?: number;
  impact_percentage?: number;
  is_automated?: boolean;
  conversation?: string;
  message?: string;
  action_taken?: boolean;
  action_taken_at?: string;
  actual_impact?: number;
  user_feedback?: string;
  created_at: string;
  viewed_at?: string;
  expires_at?: string;
}

export interface AIInsightPreview {
  type: string;
  title: string;
  description: string;
  potential_impact?: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  action_items?: string[];
}

export interface CreditPackage {
  id: string;
  credits: number;
  price: number;
  price_per_credit: number;
  savings?: string;
  best_value?: boolean;
  enterprise?: boolean;
}

// Request/Response types
export interface SendMessageRequest {
  content: string;
  request_type?: 'general' | 'analysis' | 'report' | 'recommendation';
}

export interface SendMessageResponse {
  message_id: string;
  content: string;
  credits_used: number;
  credits_remaining: number;
  structured_data?: any;
  insights?: AIInsightPreview[];
  created_at: string;
}

export interface PurchaseCreditsRequest {
  amount: number;
  payment_method_id: string;
}

export interface PurchaseCreditsResponse {
  payment_intent_id: string;
  credits_added: number;
  new_balance: number;
  transaction_id: string;
}

export interface InsightActionRequest {
  action_taken: boolean;
  actual_impact?: number;
  user_feedback?: string;
}

// WebSocket message types
export interface WSMessage {
  type: string;
  [key: string]: any;
}

export interface WSChatMessage extends WSMessage {
  type: 'message';
  message: string;
}

export interface WSAIResponse extends WSMessage {
  type: 'ai_response';
  success: boolean;
  data: {
    message: string;
    message_id: string;
    credits_used: number;
    credits_remaining: number;
    structured_data?: any;
    insights?: AIInsightPreview[];
    created_at: string;
    is_fallback?: boolean;
  };
  timestamp: string;
}

export interface WSTypingIndicator extends WSMessage {
  type: 'assistant_typing' | 'user_typing';
  typing: boolean;
  user_id?: string;
}

export interface WSError extends WSMessage {
  type: 'error';
  error?: string;
  error_code?: string;
  message: string;
  credits_remaining?: number;
}