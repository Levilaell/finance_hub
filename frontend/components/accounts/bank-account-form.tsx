'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { useBankingStore } from '@/store/banking-store';
import { toast } from 'sonner';

const bankAccountSchema = z.object({
  bank_provider: z.number({ required_error: 'Selecione um banco' }),
  account_type: z.enum(['checking', 'savings', 'business', 'digital'], {
    required_error: 'Selecione o tipo de conta',
  }),
  agency: z.string().min(1, 'Agência é obrigatória').max(10, 'Agência deve ter no máximo 10 caracteres'),
  account_number: z.string().min(1, 'Número da conta é obrigatório').max(20, 'Número da conta deve ter no máximo 20 caracteres'),
  account_digit: z.string().optional(),
  nickname: z.string().optional(),
  is_primary: z.boolean().default(false),
});

type BankAccountFormData = z.infer<typeof bankAccountSchema>;

interface BankAccountFormProps {
  isOpen: boolean;
  onClose: () => void;
  account?: any; // For editing
}

export function BankAccountForm({ isOpen, onClose, account }: BankAccountFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { providers, fetchAccounts } = useBankingStore();

  const form = useForm<BankAccountFormData>({
    resolver: zodResolver(bankAccountSchema),
    defaultValues: {
      bank_provider: account?.bank_provider?.id || undefined,
      account_type: account?.account_type || 'checking',
      agency: account?.agency || '',
      account_number: account?.account_number || '',
      account_digit: account?.account_digit || '',
      nickname: account?.nickname || '',
      is_primary: account?.is_primary || false,
    },
  });

  const onSubmit = async (data: BankAccountFormData) => {
    setIsSubmitting(true);
    try {
      const url = account 
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/accounts/${account.id}/`
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/banking/accounts/`;
      
      const method = account ? 'PATCH' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${typeof window !== 'undefined' ? localStorage.getItem('access_token') : ''}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao salvar conta');
      }

      toast.success(account ? 'Conta atualizada com sucesso' : 'Conta criada com sucesso');
      await fetchAccounts();
      onClose();
    } catch (error: any) {
      toast.error(error.message || 'Erro ao salvar conta');
    } finally {
      setIsSubmitting(false);
    }
  };

  const accountTypes = [
    { value: 'checking', label: 'Conta Corrente' },
    { value: 'savings', label: 'Poupança' },
    { value: 'business', label: 'Conta Empresarial' },
    { value: 'digital', label: 'Conta Digital' },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {account ? 'Editar Conta Bancária' : 'Adicionar Conta Bancária'}
          </DialogTitle>
          <DialogDescription>
            {account 
              ? 'Edite as informações da sua conta bancária'
              : 'Adicione uma nova conta bancária manualmente'
            }
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="bank_provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Banco</FormLabel>
                  <Select onValueChange={(value) => field.onChange(Number(value))} value={field.value?.toString()}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o banco" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {providers.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id.toString()}>
                          {provider.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="account_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo de Conta</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione o tipo" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {accountTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="agency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Agência</FormLabel>
                    <FormControl>
                      <Input placeholder="1234" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="account_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Número da Conta</FormLabel>
                    <FormControl>
                      <Input placeholder="12345678" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="account_digit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Dígito Verificador (opcional)</FormLabel>
                  <FormControl>
                    <Input placeholder="9" maxLength={2} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="nickname"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Apelido (opcional)</FormLabel>
                  <FormControl>
                    <Input placeholder="Conta Principal" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end space-x-3">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <LoadingSpinner className="mr-2 h-4 w-4" />}
                {account ? 'Atualizar' : 'Criar'} Conta
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}