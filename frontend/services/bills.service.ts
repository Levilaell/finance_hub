/**
 * Bills Service - API integration for accounts payable/receivable
 */

import apiClient from "@/lib/api-client";
import {
  Bill,
  BillRequest,
  BillFilter,
  BillsSummary,
  RegisterPaymentRequest,
  CashFlowProjection,
  PaginatedResponse,
  TransactionSuggestion,
  LinkTransactionRequest,
  // BillPayment types (pagamentos parciais)
  BillPayment,
  BillPaymentCreateRequest,
  PartialPaymentSuggestionsResponse
} from "@/types/banking";

class BillsService {
  // Bills CRUD
  async getBills(filters?: BillFilter): Promise<Bill[]> {
    const allBills: Bill[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await apiClient.get<PaginatedResponse<Bill>>(
        "/api/banking/bills/",
        { ...filters, page }
      );

      allBills.push(...response.results);
      hasMore = response.next !== null && response.next !== undefined;
      page++;

      // Safety limit
      if (page > 100) {
        console.warn('⚠️ Limite de 100 páginas atingido');
        break;
      }
    }

    return allBills;
  }

  async getBill(id: string): Promise<Bill> {
    return apiClient.get<Bill>(`/api/banking/bills/${id}/`);
  }

  async createBill(data: BillRequest): Promise<Bill> {
    return apiClient.post<Bill>("/api/banking/bills/", data);
  }

  async updateBill(id: string, data: Partial<BillRequest>): Promise<Bill> {
    return apiClient.patch<Bill>(`/api/banking/bills/${id}/`, data);
  }

  async deleteBill(id: string): Promise<void> {
    return apiClient.delete(`/api/banking/bills/${id}/`);
  }

  // Register Payment
  async registerPayment(id: string, data: RegisterPaymentRequest): Promise<Bill> {
    return apiClient.post<Bill>(
      `/api/banking/bills/${id}/register_payment/`,
      data
    );
  }

  // Summary
  async getSummary(): Promise<BillsSummary> {
    return apiClient.get<BillsSummary>("/api/banking/bills/summary/");
  }

  // Cash Flow Projection
  async getCashFlowProjection(): Promise<CashFlowProjection[]> {
    return apiClient.get<CashFlowProjection[]>(
      "/api/banking/bills/cash_flow_projection/"
    );
  }

  // Actual Cash Flow (what was paid/received)
  async getActualCashFlow(): Promise<CashFlowProjection[]> {
    return apiClient.get<CashFlowProjection[]>(
      "/api/banking/bills/actual_cash_flow/"
    );
  }

  // Utility methods
  getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      pending: 'text-yellow-500',
      partially_paid: 'text-blue-500',
      paid: 'text-green-500',
      cancelled: 'text-gray-500',
    };
    return colors[status] || 'text-gray-500';
  }

  getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
      pending: 'bg-orange-600 text-white',
      partially_paid: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'Pendente',
      partially_paid: 'Parcialmente Pago',
      paid: 'Pago',
      cancelled: 'Cancelado',
    };
    return labels[status] || status;
  }

  getTypeLabel(type: string): string {
    return type === 'receivable' ? 'A Receber' : 'A Pagar';
  }

  getTypeColor(type: string): string {
    return type === 'receivable' ? 'text-green-500' : 'text-red-500';
  }

  getRecurrenceLabel(recurrence: string): string {
    const labels: Record<string, string> = {
      once: 'Uma vez',
      monthly: 'Mensal',
      weekly: 'Semanal',
      yearly: 'Anual',
    };
    return labels[recurrence] || recurrence;
  }

  isOverdue(bill: Bill): boolean {
    if (bill.status === 'paid' || bill.status === 'cancelled') {
      return false;
    }
    const today = new Date();
    const dueDate = new Date(bill.due_date);
    return dueDate < today;
  }

  getDaysUntilDue(dueDate: string): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    const diffTime = due.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  getDueDateLabel(dueDate: string): string {
    const days = this.getDaysUntilDue(dueDate);

    if (days < 0) {
      return `${Math.abs(days)} dia${Math.abs(days) !== 1 ? 's' : ''} atrasado`;
    } else if (days === 0) {
      return 'Vence hoje';
    } else if (days === 1) {
      return 'Vence amanhã';
    } else if (days <= 7) {
      return `Vence em ${days} dias`;
    }

    return new Date(dueDate).toLocaleDateString('pt-BR');
  }

  // ============================================================
  // Transaction Linking Methods
  // ============================================================

  /**
   * Get suggested transactions for linking to a bill
   */
  async getSuggestedTransactions(billId: string): Promise<TransactionSuggestion[]> {
    return apiClient.get<TransactionSuggestion[]>(
      `/api/banking/bills/${billId}/suggested_transactions/`
    );
  }

  /**
   * Link a transaction to a bill
   */
  async linkTransaction(billId: string, transactionId: string): Promise<Bill> {
    return apiClient.post<Bill>(
      `/api/banking/bills/${billId}/link_transaction/`,
      { transaction_id: transactionId }
    );
  }

  /**
   * Unlink transaction from a bill
   */
  async unlinkTransaction(billId: string): Promise<Bill> {
    return apiClient.post<Bill>(
      `/api/banking/bills/${billId}/unlink_transaction/`,
      {}
    );
  }

  // ============================================================
  // Partial Payment Methods (Pagamentos Parciais)
  // ============================================================

  /**
   * Get all payments for a bill
   */
  async getPayments(billId: string): Promise<BillPayment[]> {
    return apiClient.get<BillPayment[]>(
      `/api/banking/bills/${billId}/payments/`
    );
  }

  /**
   * Add a payment to a bill (with optional transaction link)
   */
  async addPayment(billId: string, data: BillPaymentCreateRequest): Promise<Bill> {
    return apiClient.post<Bill>(
      `/api/banking/bills/${billId}/add_payment/`,
      data
    );
  }

  /**
   * Remove a payment from a bill
   */
  async removePayment(billId: string, paymentId: string): Promise<Bill> {
    return apiClient.delete<Bill>(
      `/api/banking/bills/${billId}/payments/${paymentId}/`
    );
  }

  /**
   * Get suggested transactions for partial payment
   */
  async getSuggestedTransactionsPartial(billId: string): Promise<PartialPaymentSuggestionsResponse> {
    return apiClient.get<PartialPaymentSuggestionsResponse>(
      `/api/banking/bills/${billId}/suggested_transactions_partial/`
    );
  }

  // ============================================================
  // OCR Upload Methods
  // ============================================================

  /**
   * Upload a boleto file (PDF or image) and extract data using OCR
   */
  async uploadBoleto(file: File): Promise<OCRResult> {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.postFormData<OCRResult>(
      '/api/banking/bills/upload_boleto/',
      formData
    );
  }

  /**
   * Create a bill from OCR results after user review
   */
  async createFromOCR(data: BillRequest & {
    barcode?: string;
    ocr_confidence?: number;
    ocr_raw_data?: Record<string, any>;
  }): Promise<Bill> {
    return apiClient.post<Bill>(
      '/api/banking/bills/create_from_ocr/',
      data
    );
  }
}

// OCR Result type
export interface OCRResult {
  success: boolean;
  barcode: string;
  amount: string | null;
  due_date: string | null;
  beneficiary: string;
  confidence: number;
  needs_review: boolean;
  extracted_fields?: Record<string, any>;
  error: string;
}

export const billsService = new BillsService();

// Re-export types for convenience
export type { BillRequest } from '@/types/banking';
