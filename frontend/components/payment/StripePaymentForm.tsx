'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Lock, AlertCircle } from 'lucide-react';
// Type definition for payment method request
interface CreatePaymentMethodRequest {
  token: string;
  cardholderName: string;
  isDefault: boolean;
}
import { useTheme } from 'next-themes';

// Initialize Stripe - this should come from environment variable
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

const formSchema = z.object({
  cardholderName: z.string().min(2, 'Name is required'),
  isDefault: z.boolean().default(false),
});

type FormData = z.infer<typeof formSchema>;

interface StripePaymentFormProps {
  onSubmit: (data: CreatePaymentMethodRequest) => void;
  loading?: boolean;
}

// Inner component that uses Stripe hooks
function PaymentFormContent({ onSubmit, loading }: StripePaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const { theme } = useTheme();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [cardComplete, setCardComplete] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      isDefault: false,
    },
  });

  // Stripe Element styling
  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: theme === 'dark' ? '#ffffff' : '#000000',
        '::placeholder': {
          color: theme === 'dark' ? '#6b7280' : '#9ca3af',
        },
        iconColor: theme === 'dark' ? '#9ca3af' : '#6b7280',
      },
      invalid: {
        color: '#ef4444',
        iconColor: '#ef4444',
      },
    },
    hidePostalCode: true,
  };

  const handleCardChange = (event: any) => {
    setCardComplete(event.complete);
    if (event.error) {
      setError(event.error.message);
    } else {
      setError(null);
    }
  };

  const onFormSubmit = async (data: FormData) => {
    if (!stripe || !elements) {
      setError('Stripe has not loaded yet. Please try again.');
      return;
    }

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setError('Card element not found');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      // Create payment method with Stripe
      const { error, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
          name: data.cardholderName,
        },
      });

      if (error) {
        setError(error.message || 'An error occurred');
        setProcessing(false);
        return;
      }

      if (!paymentMethod) {
        setError('Failed to create payment method');
        setProcessing(false);
        return;
      }

      // Submit the payment method to our backend
      onSubmit({
        type: 'card',
        token: paymentMethod.id, // This is the Stripe payment method ID
        is_default: data.isDefault,
        brand: paymentMethod.card?.brand || '',
        last4: paymentMethod.card?.last4 || '',
        exp_month: paymentMethod.card?.exp_month,
        exp_year: paymentMethod.card?.exp_year,
      });
    } catch (err) {
      setError('An unexpected error occurred');
      console.error('Payment method creation error:', err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cardholderName">Cardholder Name</Label>
              <input
                id="cardholderName"
                placeholder="John Doe"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                {...register('cardholderName')}
              />
              {errors.cardholderName && (
                <p className="text-sm text-red-500">{errors.cardholderName.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="card-element">Card Details</Label>
              <div className="p-3 border rounded-md">
                <CardElement 
                  id="card-element"
                  options={cardElementOptions}
                  onChange={handleCardChange}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Enter your card number, expiry date, and CVC
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="isDefault"
                {...register('isDefault')}
              />
              <Label
                htmlFor="isDefault"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Set as default payment method
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Button 
        type="submit" 
        className="w-full" 
        disabled={!stripe || processing || loading || !cardComplete}
      >
        {processing || loading ? 'Processing...' : 'Add Payment Method'}
      </Button>

      <p className="text-xs text-muted-foreground text-center">
        <Lock className="inline-block h-3 w-3 mr-1" />
        Your payment information is encrypted and secure. We never store your card details.
      </p>
    </form>
  );
}

// Wrapper component that provides Stripe Elements
export function StripePaymentForm(props: StripePaymentFormProps) {
  const { theme } = useTheme();
  
  return (
    <Elements 
      stripe={stripePromise}
      options={{
        appearance: {
          theme: theme === 'dark' ? 'night' : 'stripe',
          variables: {
            colorPrimary: '#3b82f6',
          },
        },
      }}
    >
      <PaymentFormContent {...props} />
    </Elements>
  );
}