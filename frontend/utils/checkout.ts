import { subscriptionService } from '@/services/subscription.service';
import { toast } from 'sonner';

/**
 * Inicia o checkout do Stripe e redireciona o usuário
 * @param onError - Callback opcional para tratamento de erro customizado
 */
export async function startStripeCheckout(onError?: (error: any) => void) {
  try {
    const result = await subscriptionService.createCheckoutSession();

    if (result.checkout_url) {
      // Redireciona para Stripe Checkout hospedado
      window.location.href = result.checkout_url;
    } else {
      throw new Error('URL de checkout não recebida');
    }
  } catch (error: any) {
    console.error('Erro ao criar sessão de checkout:', error);

    const errorMessage = error.response?.data?.error || error.message || 'Erro ao iniciar checkout';

    toast.error('Erro ao iniciar checkout', {
      description: errorMessage,
    });

    // Chama callback customizado se fornecido
    if (onError) {
      onError(error);
    }
  }
}
