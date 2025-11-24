'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { billsService } from '@/services/bills.service';
import { bankingService } from '@/services/banking.service';
import { Bill, BillRequest, Category } from '@/types/banking';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import {
  PlusIcon,
  FunnelIcon,
  ArrowPathIcon,
  XMarkIcon,
  CheckIcon,
  BanknotesIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

export default function BillsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [bills, setBills] = useState<Bill[]>([]);
  const [filteredBills, setFilteredBills] = useState<Bill[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Form states
  const [formData, setFormData] = useState<BillRequest>({
    type: 'payable',
    description: '',
    amount: 0,
    due_date: '',
    recurrence: 'once',
    customer_supplier: '',
    notes: ''
  });
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [paymentNotes, setPaymentNotes] = useState<string>('');

  // Filter states
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showOverdue, setShowOverdue] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    fetchData();
  }, [isAuthenticated, router]);

  useEffect(() => {
    applyFilters();
  }, [bills, filterType, filterStatus, filterCategory, searchTerm, showOverdue]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [billsData, categoriesData] = await Promise.all([
        billsService.getBills(),
        bankingService.getCategories()
      ]);
      setBills(billsData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('Error fetching bills:', error);
      toast.error('Erro ao carregar contas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchData();
    setIsRefreshing(false);
  };

  const applyFilters = () => {
    let filtered = [...bills];

    if (filterType !== 'all') {
      filtered = filtered.filter(b => b.type === filterType);
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter(b => b.status === filterStatus);
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter(b => b.category === filterCategory);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(b =>
        b.description.toLowerCase().includes(term) ||
        b.customer_supplier?.toLowerCase().includes(term)
      );
    }

    if (showOverdue) {
      filtered = filtered.filter(b => b.is_overdue);
    }

    setFilteredBills(filtered);
  };

  const clearFilters = () => {
    setFilterType('all');
    setFilterStatus('all');
    setFilterCategory('all');
    setSearchTerm('');
    setShowOverdue(false);
  };

  const handleCreateBill = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await billsService.createBill(formData);
      toast.success('Conta criada com sucesso!');
      setShowCreateDialog(false);
      resetForm();
      await fetchData();
    } catch (error) {
      console.error('Error creating bill:', error);
      toast.error('Erro ao criar conta');
    }
  };

  const handleRegisterPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBill) return;

    try {
      await billsService.registerPayment(selectedBill.id, {
        amount: paymentAmount,
        notes: paymentNotes
      });
      toast.success('Pagamento registrado com sucesso!');
      setShowPaymentDialog(false);
      setSelectedBill(null);
      setPaymentAmount(0);
      setPaymentNotes('');
      await fetchData();
    } catch (error: any) {
      console.error('Error registering payment:', error);
      toast.error(error?.response?.data?.error || 'Erro ao registrar pagamento');
    }
  };

  const handleDeleteBill = async (billId: string) => {
    if (!confirm('Tem certeza que deseja excluir esta conta?')) return;

    try {
      await billsService.deleteBill(billId);
      toast.success('Conta excluída com sucesso!');
      await fetchData();
    } catch (error) {
      console.error('Error deleting bill:', error);
      toast.error('Erro ao excluir conta');
    }
  };

  const openPaymentDialog = (bill: Bill) => {
    setSelectedBill(bill);
    setPaymentAmount(bill.amount_remaining);
    setPaymentNotes('');
    setShowPaymentDialog(true);
  };

  const resetForm = () => {
    setFormData({
      type: 'payable',
      description: '',
      amount: 0,
      due_date: '',
      recurrence: 'once',
      customer_supplier: '',
      notes: ''
    });
  };

  if (!isAuthenticated || !user || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const stats = {
    total: filteredBills.length,
    pending: filteredBills.filter(b => b.status === 'pending').length,
    partially_paid: filteredBills.filter(b => b.status === 'partially_paid').length,
    overdue: filteredBills.filter(b => b.is_overdue).length,
    totalPayable: filteredBills
      .filter(b => b.type === 'payable')
      .reduce((sum, b) => {
        const amount = typeof b.amount_remaining === 'string'
          ? parseFloat(b.amount_remaining)
          : b.amount_remaining;
        return sum + (isNaN(amount) ? 0 : amount);
      }, 0),
    totalReceivable: filteredBills
      .filter(b => b.type === 'receivable')
      .reduce((sum, b) => {
        const amount = typeof b.amount_remaining === 'string'
          ? parseFloat(b.amount_remaining)
          : b.amount_remaining;
        return sum + (isNaN(amount) ? 0 : amount);
      }, 0)
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-white">Contas a Pagar/Receber</h1>
          <p className="text-white/70 mt-1">
            Gerencie suas contas pendentes
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filtros
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowPathIcon className="h-4 w-4" />
            )}
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                Nova Conta
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Criar Nova Conta</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateBill} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Tipo</Label>
                    <Select
                      value={formData.type}
                      onValueChange={(value: any) => setFormData({ ...formData, type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="payable">A Pagar</SelectItem>
                        <SelectItem value="receivable">A Receber</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Recorrência</Label>
                    <Select
                      value={formData.recurrence}
                      onValueChange={(value: any) => setFormData({ ...formData, recurrence: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="once">Uma vez</SelectItem>
                        <SelectItem value="monthly">Mensal</SelectItem>
                        <SelectItem value="weekly">Semanal</SelectItem>
                        <SelectItem value="yearly">Anual</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Descrição</Label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Ex: Aluguel da loja"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Valor</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.amount || ''}
                      onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <div>
                    <Label>Data de Vencimento</Label>
                    <Input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label>Cliente/Fornecedor</Label>
                  <Input
                    value={formData.customer_supplier}
                    onChange={(e) => setFormData({ ...formData, customer_supplier: e.target.value })}
                    placeholder="Nome do cliente ou fornecedor"
                  />
                </div>

                <div>
                  <Label>Categoria (Opcional)</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione uma categoria" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories
                        .filter(c =>
                          formData.type === 'receivable' ? c.type === 'income' : c.type === 'expense'
                        )
                        .map(cat => (
                          <SelectItem key={cat.id} value={cat.id}>
                            <div className="flex items-center gap-2">
                              <div
                                className="w-4 h-4 rounded"
                                style={{ backgroundColor: cat.color }}
                              />
                              {cat.name}
                            </div>
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Observações</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Observações adicionais"
                    rows={3}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit">Criar Conta</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <BanknotesIcon className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pendentes</p>
                <p className="text-2xl font-bold text-orange-500">{stats.pending}</p>
              </div>
              <ClockIcon className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Atrasadas</p>
                <p className="text-2xl font-bold text-red-500">{stats.overdue}</p>
              </div>
              <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">A Pagar</p>
                <p className="text-xl font-bold text-red-600">{formatCurrency(stats.totalPayable)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">A Receber</p>
                <p className="text-xl font-bold text-green-600">{formatCurrency(stats.totalReceivable)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Filtros</CardTitle>
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <XMarkIcon className="h-4 w-4 mr-2" />
              Limpar
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label>Pesquisar</Label>
                <Input
                  placeholder="Descrição ou cliente..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div>
                <Label>Tipo</Label>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="payable">A Pagar</SelectItem>
                    <SelectItem value="receivable">A Receber</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Status</Label>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="partially_paid">Parcialmente Pago</SelectItem>
                    <SelectItem value="paid">Pago</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <Button
                  variant={showOverdue ? 'default' : 'outline'}
                  onClick={() => setShowOverdue(!showOverdue)}
                  className="w-full"
                >
                  Somente Atrasadas
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bills List */}
      <Card>
        <CardHeader>
          <CardTitle>
            {filteredBills.length} Conta{filteredBills.length !== 1 ? 's' : ''}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredBills.length > 0 ? (
            <div className="space-y-4">
              {filteredBills.map((bill) => (
                <div
                  key={bill.id}
                  className="flex items-center justify-between p-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{bill.description}</h3>
                      <Badge className={billsService.getStatusBadgeClass(bill.status)}>
                        {billsService.getStatusLabel(bill.status)}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={bill.type === 'receivable' ? 'text-green-500' : 'text-red-500'}
                      >
                        {billsService.getTypeLabel(bill.type)}
                      </Badge>
                      {bill.is_overdue && (
                        <Badge className="bg-red-100 text-red-800">
                          Atrasada
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span>
                        Vencimento: {format(new Date(bill.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                      </span>
                      {bill.customer_supplier && (
                        <span>• {bill.customer_supplier}</span>
                      )}
                      {bill.recurrence !== 'once' && (
                        <span>• {billsService.getRecurrenceLabel(bill.recurrence)}</span>
                      )}
                    </div>
                    {bill.status === 'partially_paid' && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                          <span>Progresso do pagamento</span>
                          <span>{bill.payment_percentage.toFixed(0)}%</span>
                        </div>
                        <Progress value={bill.payment_percentage} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatCurrency(bill.amount_paid)} de {formatCurrency(bill.amount)} pago
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-2xl font-bold">
                        {formatCurrency(bill.amount_remaining)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {billsService.getDueDateLabel(bill.due_date)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {bill.status !== 'paid' && bill.status !== 'cancelled' && (
                        <Button
                          size="sm"
                          onClick={() => openPaymentDialog(bill)}
                        >
                          <CheckIcon className="h-4 w-4 mr-1" />
                          Registrar
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteBill(bill.id)}
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-white/60">Nenhuma conta encontrada</p>
              <Button
                variant="ghost"
                onClick={clearFilters}
                className="mt-4"
              >
                Limpar filtros
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar Pagamento</DialogTitle>
          </DialogHeader>
          {selectedBill && (
            <form onSubmit={handleRegisterPayment} className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Conta</p>
                <p className="font-semibold">{selectedBill.description}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Valor restante</p>
                <p className="text-2xl font-bold">{formatCurrency(selectedBill.amount_remaining)}</p>
              </div>
              <div>
                <Label>Valor do Pagamento</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={paymentAmount || ''}
                  onChange={(e) => setPaymentAmount(parseFloat(e.target.value))}
                  max={selectedBill.amount_remaining}
                  required
                />
              </div>
              <div>
                <Label>Observações (Opcional)</Label>
                <Textarea
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="Observações sobre o pagamento"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowPaymentDialog(false)}>
                  Cancelar
                </Button>
                <Button type="submit">Confirmar Pagamento</Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
