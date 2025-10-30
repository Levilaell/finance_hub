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
  PaginatedResponse
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
      pending: 'bg-yellow-100 text-yellow-800',
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
}

export const billsService = new BillsService();
