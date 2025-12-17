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
  ExclamationTriangleIcon,
  LinkIcon,
  ArrowTopRightOnSquareIcon,
  ListBulletIcon,
  PlusCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { toast } from 'sonner';
import { LinkTransactionDialog, LinkPartialPaymentDialog, BillPaymentsList } from '@/components/banking';

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
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [showPartialPaymentDialog, setShowPartialPaymentDialog] = useState(false);
  const [showPaymentsListDialog, setShowPaymentsListDialog] = useState(false);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [isUnlinking, setIsUnlinking] = useState<string | null>(null);

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

  // Função para achatar categorias com subcategorias
  const flattenCategories = (cats: Category[], type: 'income' | 'expense') => {
    return cats
      .filter(c => c.type === type)
      .flatMap(cat => {
        const items: Array<Category & { displayName?: string; isSubcategory?: boolean }> = [
          { ...cat, displayName: cat.name, isSubcategory: false }
        ];
        if (cat.subcategories && cat.subcategories.length > 0) {
          items.push(...cat.subcategories.map(sub => ({
            ...sub,
            displayName: `  └ ${sub.name}`,
            isSubcategory: true
          })));
        }
        return items;
      });
  };

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

  const openLinkDialog = (bill: Bill) => {
    setSelectedBill(bill);
    setShowLinkDialog(true);
  };

  const openPartialPaymentDialog = (bill: Bill) => {
    setSelectedBill(bill);
    setShowPartialPaymentDialog(true);
  };

  const openPaymentsListDialog = (bill: Bill) => {
    setSelectedBill(bill);
    setShowPaymentsListDialog(true);
  };

  const handleUnlinkTransaction = async (billId: string) => {
    if (!confirm('Deseja desvincular esta transação? A conta voltará ao status pendente.')) return;

    setIsUnlinking(billId);
    try {
      await billsService.unlinkTransaction(billId);
      toast.success('Transação desvinculada. Conta retornada para pendente.');
      await fetchData();
    } catch (error: any) {
      console.error('Error unlinking transaction:', error);
      toast.error(error?.response?.data?.error || 'Erro ao desvincular transação');
    } finally {
      setIsUnlinking(null);
    }
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
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-3 sm:gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Contas a Pagar/Receber</h1>
            <TooltipProvider>
              <Tooltip delayDuration={0}>
                <TooltipTrigger asChild>
                  <button className="text-white/50 hover:text-white/80 transition-colors">
                    <QuestionMarkCircleIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="bottom" align="start" className="max-w-sm p-4 bg-zinc-900 border-white/10">
                  <div className="space-y-3 text-sm">
                    <p className="font-semibold text-white">Como funciona:</p>
                    <ul className="space-y-2 text-white/80">
                      <li><strong className="text-orange-400">1.</strong> Crie uma conta (a pagar ou receber)</li>
                      <li><strong className="text-orange-400">2.</strong> Vincule a transações do extrato quando pagar</li>
                      <li><strong className="text-orange-400">3.</strong> Ou registre pagamentos manuais (dinheiro)</li>
                    </ul>
                    <div className="pt-2 border-t border-white/10">
                      <p className="text-white/60 text-xs">
                        <strong className="text-blue-400">Dica:</strong> Pagamentos parciais são suportados. Vincule várias transações até quitar a conta.
                      </p>
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <p className="text-sm sm:text-base text-white/70 mt-1">
            Gerencie suas contas pendentes
          </p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="text-white border-white/20 hover:bg-white/10 flex-1 sm:flex-none"
          >
            <FunnelIcon className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Filtros</span>
          </Button>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-white border-white/20 hover:bg-white/10"
          >
            {isRefreshing ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowPathIcon className="h-4 w-4" />
            )}
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button className="flex-1 sm:flex-none">
                <PlusIcon className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Nova Conta</span>
                <span className="sm:hidden">Nova</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Criar Nova Conta</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateBill} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                      {flattenCategories(
                        categories,
                        formData.type === 'receivable' ? 'income' : 'expense'
                      ).map(cat => (
                        <SelectItem key={cat.id} value={cat.id}>
                          <div className="flex items-center gap-2">
                            <div
                              className="w-4 h-4 rounded"
                              style={{ backgroundColor: cat.color }}
                            />
                            <span className={cat.isSubcategory ? 'text-muted-foreground' : ''}>
                              {cat.displayName || cat.name}
                            </span>
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
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Total</p>
                <p className="text-xl sm:text-2xl font-bold">{stats.total}</p>
              </div>
              <BanknotesIcon className="h-6 w-6 sm:h-8 sm:w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Pendentes</p>
                <p className="text-xl sm:text-2xl font-bold text-orange-500">{stats.pending}</p>
              </div>
              <ClockIcon className="h-6 w-6 sm:h-8 sm:w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Atrasadas</p>
                <p className="text-xl sm:text-2xl font-bold text-red-500">{stats.overdue}</p>
              </div>
              <ExclamationTriangleIcon className="h-6 w-6 sm:h-8 sm:w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">A Pagar</p>
                <p className="text-base sm:text-xl font-bold text-red-600">{formatCurrency(stats.totalPayable)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-2 sm:col-span-1">
          <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">A Receber</p>
                <p className="text-base sm:text-xl font-bold text-green-600">{formatCurrency(stats.totalReceivable)}</p>
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <div>
                <Label className="text-xs sm:text-sm">Pesquisar</Label>
                <Input
                  placeholder="Descrição ou cliente..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="h-9 sm:h-10"
                />
              </div>
              <div>
                <Label className="text-xs sm:text-sm">Tipo</Label>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="h-9 sm:h-10">
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
                <Label className="text-xs sm:text-sm">Status</Label>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="h-9 sm:h-10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="partially_paid">Parc. Pago</SelectItem>
                    <SelectItem value="paid">Pago</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <Button
                  variant={showOverdue ? 'default' : 'outline'}
                  onClick={() => setShowOverdue(!showOverdue)}
                  className="w-full h-9 sm:h-10 text-xs sm:text-sm"
                >
                  <span className="sm:hidden">Atrasadas</span>
                  <span className="hidden sm:inline">Somente Atrasadas</span>
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
            <div className="space-y-3 sm:space-y-4">
              {filteredBills.map((bill) => (
                <div
                  key={bill.id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 sm:p-4 border border-white/10 rounded-lg hover:bg-white/5 transition-colors gap-3 sm:gap-4"
                >
                  {/* Conteúdo principal */}
                  <div className="flex-1 min-w-0">
                    {/* Título e badges */}
                    <div className="flex flex-wrap items-start sm:items-center gap-2">
                      <h3 className="font-semibold text-base sm:text-lg break-words">{bill.description}</h3>
                      <div className="flex flex-wrap gap-1.5">
                        <Badge className={`text-xs ${billsService.getStatusBadgeClass(bill.status)}`}>
                          {billsService.getStatusLabel(bill.status)}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`text-xs ${bill.type === 'receivable' ? 'text-green-500' : 'text-red-500'}`}
                        >
                          {billsService.getTypeLabel(bill.type)}
                        </Badge>
                        {bill.is_overdue && (
                          <Badge className="text-xs bg-red-100 text-red-800">
                            Atrasada
                          </Badge>
                        )}
                        {bill.has_linked_transaction && bill.linked_transaction_details && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Badge className="text-xs bg-blue-100 text-blue-800 flex items-center gap-1">
                                  <LinkIcon className="h-3 w-3" />
                                  <span className="hidden sm:inline">Vinculada</span>
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p className="font-medium">{bill.linked_transaction_details.description}</p>
                                <p className="text-xs">
                                  {format(new Date(bill.linked_transaction_details.date), 'dd/MM/yyyy', { locale: ptBR })}
                                  {' • '}
                                  {formatCurrency(parseFloat(bill.linked_transaction_details.amount))}
                                </p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        {bill.payments_count && bill.payments_count > 0 && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger>
                                <Badge
                                  className="text-xs bg-purple-100 text-purple-800 flex items-center gap-1 cursor-pointer hover:bg-purple-200"
                                  onClick={() => openPaymentsListDialog(bill)}
                                >
                                  <ListBulletIcon className="h-3 w-3" />
                                  {bill.payments_count} pagamento{bill.payments_count > 1 ? 's' : ''}
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Clique para ver os pagamentos</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </div>
                    {/* Informações secundárias */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs sm:text-sm text-muted-foreground">
                      <span>
                        Venc: {format(new Date(bill.due_date), 'dd/MM/yyyy', { locale: ptBR })}
                      </span>
                      {bill.customer_supplier && (
                        <span className="truncate max-w-[150px] sm:max-w-none">• {bill.customer_supplier}</span>
                      )}
                      {bill.recurrence !== 'once' && (
                        <span>• {billsService.getRecurrenceLabel(bill.recurrence)}</span>
                      )}
                    </div>
                    {/* Barra de progresso */}
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
                  {/* Valor e ações */}
                  <div className="flex items-center justify-between sm:justify-end gap-3 sm:gap-4 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/10">
                    <div className="text-left sm:text-right">
                      <p className="text-xl sm:text-2xl font-bold">
                        {formatCurrency(bill.amount_remaining)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {billsService.getDueDateLabel(bill.due_date)}
                      </p>
                    </div>
                    <div className="flex gap-1.5 sm:gap-2">
                      {/* Legacy Link/Unlink button (for backward compatibility) */}
                      {bill.has_linked_transaction && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-8 w-8 sm:h-9 sm:w-9 p-0"
                                onClick={() => handleUnlinkTransaction(bill.id)}
                                disabled={isUnlinking === bill.id}
                              >
                                {isUnlinking === bill.id ? (
                                  <LoadingSpinner className="h-4 w-4" />
                                ) : (
                                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                                )}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Desvincular transação</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      {/* Add payment button (new partial payment system) */}
                      {bill.can_add_payment && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                size="sm"
                                className="h-8 sm:h-9 px-2 sm:px-3"
                                onClick={() => openPartialPaymentDialog(bill)}
                              >
                                <PlusCircleIcon className="h-4 w-4 sm:mr-1" />
                                <span className="hidden sm:inline">
                                  {bill.payments_count && bill.payments_count > 0 ? 'Add Pagamento' : 'Registrar'}
                                </span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              {bill.payments_count && bill.payments_count > 0
                                ? 'Adicionar mais um pagamento'
                                : 'Registrar pagamento'}
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-8 sm:h-9 sm:w-9 p-0"
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
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Registrar Pagamento</DialogTitle>
          </DialogHeader>
          {selectedBill && (
            <form onSubmit={handleRegisterPayment} className="space-y-4">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Conta</p>
                <p className="font-semibold text-sm sm:text-base break-words">{selectedBill.description}</p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Valor restante</p>
                <p className="text-xl sm:text-2xl font-bold">{formatCurrency(selectedBill.amount_remaining)}</p>
              </div>
              <div>
                <Label className="text-xs sm:text-sm">Valor do Pagamento</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={paymentAmount || ''}
                  onChange={(e) => setPaymentAmount(parseFloat(e.target.value))}
                  max={selectedBill.amount_remaining}
                  required
                  className="h-9 sm:h-10"
                />
              </div>
              <div>
                <Label className="text-xs sm:text-sm">Observações (Opcional)</Label>
                <Textarea
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  placeholder="Observações sobre o pagamento"
                  rows={3}
                />
              </div>
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowPaymentDialog(false)}>
                  Cancelar
                </Button>
                <Button type="submit">Confirmar</Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Link Transaction Dialog (Legacy) */}
      <LinkTransactionDialog
        bill={selectedBill}
        open={showLinkDialog}
        onOpenChange={setShowLinkDialog}
        onLinked={fetchData}
      />

      {/* Partial Payment Dialog (New System) */}
      <LinkPartialPaymentDialog
        bill={selectedBill}
        open={showPartialPaymentDialog}
        onOpenChange={setShowPartialPaymentDialog}
        onPaymentAdded={fetchData}
      />

      {/* Payments List Dialog */}
      <Dialog open={showPaymentsListDialog} onOpenChange={setShowPaymentsListDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ListBulletIcon className="h-5 w-5" />
              Pagamentos - {selectedBill?.description}
            </DialogTitle>
          </DialogHeader>
          {selectedBill && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="bg-muted/50 rounded-lg p-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Valor Total</p>
                    <p className="font-semibold">{formatCurrency(selectedBill.amount)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Já Pago</p>
                    <p className="font-semibold text-green-600">{formatCurrency(selectedBill.amount_paid)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Restante</p>
                    <p className="font-semibold text-orange-600">{formatCurrency(selectedBill.amount_remaining)}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                    <span>Progresso</span>
                    <span>{selectedBill.payment_percentage?.toFixed(0) || 0}%</span>
                  </div>
                  <Progress value={selectedBill.payment_percentage || 0} className="h-2" />
                </div>
              </div>

              {/* Payments List */}
              <BillPaymentsList
                bill={selectedBill}
                onPaymentRemoved={() => {
                  fetchData();
                  // Close dialog if all payments removed
                  if (selectedBill.payments_count === 1) {
                    setShowPaymentsListDialog(false);
                  }
                }}
              />

              {/* Add more payments button */}
              {selectedBill.can_add_payment && (
                <div className="flex justify-center pt-2 border-t">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowPaymentsListDialog(false);
                      openPartialPaymentDialog(selectedBill);
                    }}
                  >
                    <PlusCircleIcon className="h-4 w-4 mr-2" />
                    Adicionar Pagamento
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
