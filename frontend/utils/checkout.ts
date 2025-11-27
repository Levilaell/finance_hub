import { subscriptionService } from '@/services/subscription.service';
import { toast } from 'sonner';

interface CheckoutOptions {
  priceId?: string;
  onError?: (error: any) => void;
}

/**
 * Inicia o checkout do Stripe e redireciona o usuário
 * @param options - Opções do checkout (priceId para teste A/B, onError callback)
 */
export async function startStripeCheckout(options?: CheckoutOptions | ((error: any) => void)) {
  // Suporta tanto o formato antigo (só callback) quanto o novo (objeto de opções)
  const opts: CheckoutOptions = typeof options === 'function' ? { onError: options } : (options || {});

  try {
    const result = await subscriptionService.createCheckoutSession(
      undefined,
      undefined,
      opts.priceId
    );

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
    if (opts.onError) {
      opts.onError(error);
    }
  }
}

/**
 * Obtém o price_id da URL se existir
 */
export function getPriceIdFromUrl(): string | null {
  if (typeof window === 'undefined') return null;
  const params = new URLSearchParams(window.location.search);
  return params.get('price_id');
}
