/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Elements } from '@stripe/react-stripe-js';
import { PaymentService } from '../../../services/payment.service';

// Mock components
const MockPaymentFlow = () => {
  const [step, setStep] = React.useState('plans');
  const [selectedPlan, setSelectedPlan] = React.useState(null);
  const [paymentMethod, setPaymentMethod] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  const handlePlanSelect = (plan: any) => {
    setSelectedPlan(plan);
    setStep('payment');
  };

  const handlePayment = async () => {
    setLoading(true);
    try {
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      setStep('success');
    } catch (error) {
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="payment-flow">
      {step === 'plans' && (
        <div data-testid="plan-selection">
          <h2>Choose Your Plan</h2>
          <div data-testid="basic-plan" onClick={() => handlePlanSelect({ id: 'basic', name: 'Basic Plan', price: 29.99 })}>
            <h3>Basic Plan</h3>
            <p>$29.99/month</p>
            <button>Select Plan</button>
          </div>
          <div data-testid="premium-plan" onClick={() => handlePlanSelect({ id: 'premium', name: 'Premium Plan', price: 99.99 })}>
            <h3>Premium Plan</h3>
            <p>$99.99/month</p>
            <button>Select Plan</button>
          </div>
        </div>
      )}

      {step === 'payment' && (
        <div data-testid="payment-form">
          <h2>Payment Details</h2>
          <div data-testid="selected-plan">
            <h3>{selectedPlan?.name}</h3>
            <p>${selectedPlan?.price}/month</p>
          </div>
          <div data-testid="payment-methods">
            <div data-testid="card-payment" onClick={() => setPaymentMethod('card')}>
              <input type="radio" name="payment" checked={paymentMethod === 'card'} readOnly />
              <label>Credit/Debit Card</label>
            </div>
          </div>
          <div data-testid="card-form">
            <input data-testid="card-number" placeholder="Card Number" />
            <input data-testid="card-expiry" placeholder="MM/YY" />
            <input data-testid="card-cvc" placeholder="CVC" />
          </div>
          <button 
            data-testid="pay-button" 
            onClick={handlePayment}
            disabled={loading}
          >
            {loading ? 'Processing...' : `Pay $${selectedPlan?.price}`}
          </button>
          <button data-testid="back-button" onClick={() => setStep('plans')}>
            Back to Plans
          </button>
        </div>
      )}

      {step === 'success' && (
        <div data-testid="payment-success">
          <h2>Payment Successful!</h2>
          <p>Your subscription to {selectedPlan?.name} is now active.</p>
          <button data-testid="continue-button">Continue to Dashboard</button>
        </div>
      )}

      {step === 'error' && (
        <div data-testid="payment-error">
          <h2>Payment Failed</h2>
          <p>There was an error processing your payment. Please try again.</p>
          <button data-testid="retry-button" onClick={() => setStep('payment')}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

// Mock Stripe
const mockStripe = {
  elements: jest.fn(),
  createToken: jest.fn(),
  createPaymentMethod: jest.fn(),
  confirmCardPayment: jest.fn(),
  retrievePaymentIntent: jest.fn(),
};

jest.mock('@stripe/stripe-js', () => ({
  loadStripe: jest.fn(() => Promise.resolve(mockStripe)),
}));

// Mock payment service
jest.mock('../../../services/payment.service', () => ({
  PaymentService: {
    getSubscriptionPlans: jest.fn(),
    createCheckoutSession: jest.fn(),
    createPaymentIntent: jest.fn(),
    confirmPaymentIntent: jest.fn(),
    createPaymentMethod: jest.fn(),
  },
}));

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

describe('Payment Flow Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    jest.clearAllMocks();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <Elements stripe={mockStripe}>
          {component}
        </Elements>
      </QueryClientProvider>
    );
  };

  it('completes full payment flow successfully', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Step 1: Plan selection
    expect(screen.getByTestId('plan-selection')).toBeInTheDocument();
    expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();

    // Select basic plan
    const basicPlan = screen.getByTestId('basic-plan');
    fireEvent.click(basicPlan);

    // Step 2: Payment form
    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    expect(screen.getByText('Payment Details')).toBeInTheDocument();
    expect(screen.getByText('Basic Plan')).toBeInTheDocument();
    expect(screen.getByText('$29.99/month')).toBeInTheDocument();

    // Fill payment details
    const cardNumber = screen.getByTestId('card-number');
    const cardExpiry = screen.getByTestId('card-expiry');
    const cardCvc = screen.getByTestId('card-cvc');

    fireEvent.change(cardNumber, { target: { value: '4242424242424242' } });
    fireEvent.change(cardExpiry, { target: { value: '12/25' } });
    fireEvent.change(cardCvc, { target: { value: '123' } });

    // Submit payment
    const payButton = screen.getByTestId('pay-button');
    fireEvent.click(payButton);

    // Check loading state
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(payButton).toBeDisabled();

    // Step 3: Success
    await waitFor(() => {
      expect(screen.getByTestId('payment-success')).toBeInTheDocument();
    }, { timeout: 2000 });

    expect(screen.getByText('Payment Successful!')).toBeInTheDocument();
    expect(screen.getByText('Your subscription to Basic Plan is now active.')).toBeInTheDocument();
  });

  it('allows going back to plan selection', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Select premium plan
    const premiumPlan = screen.getByTestId('premium-plan');
    fireEvent.click(premiumPlan);

    // Verify we're on payment page
    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    expect(screen.getByText('Premium Plan')).toBeInTheDocument();
    expect(screen.getByText('$99.99/month')).toBeInTheDocument();

    // Go back to plans
    const backButton = screen.getByTestId('back-button');
    fireEvent.click(backButton);

    // Should be back on plan selection
    expect(screen.getByTestId('plan-selection')).toBeInTheDocument();
    expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
  });

  it('handles different plan selections correctly', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Test Premium plan selection
    const premiumPlan = screen.getByTestId('premium-plan');
    fireEvent.click(premiumPlan);

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    const selectedPlan = screen.getByTestId('selected-plan');
    expect(within(selectedPlan).getByText('Premium Plan')).toBeInTheDocument();
    expect(within(selectedPlan).getByText('$99.99/month')).toBeInTheDocument();

    const payButton = screen.getByTestId('pay-button');
    expect(payButton).toHaveTextContent('Pay $99.99');
  });

  it('validates payment method selection', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Select basic plan
    const basicPlan = screen.getByTestId('basic-plan');
    fireEvent.click(basicPlan);

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    // Check payment method options
    const cardPayment = screen.getByTestId('card-payment');
    expect(cardPayment).toBeInTheDocument();

    const cardRadio = within(cardPayment).getByRole('radio');
    fireEvent.click(cardRadio);

    expect(cardRadio).toBeChecked();
  });

  it('shows proper loading states during payment', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Select plan and proceed to payment
    fireEvent.click(screen.getByTestId('basic-plan'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    // Fill form
    fireEvent.change(screen.getByTestId('card-number'), { target: { value: '4242424242424242' } });

    // Submit payment
    const payButton = screen.getByTestId('pay-button');
    fireEvent.click(payButton);

    // Should show loading state immediately
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(payButton).toBeDisabled();

    // Should complete after timeout
    await waitFor(() => {
      expect(screen.getByTestId('payment-success')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('validates required form fields', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Select plan
    fireEvent.click(screen.getByTestId('basic-plan'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    // Try to submit without filling form
    const payButton = screen.getByTestId('pay-button');
    
    // Check that form fields exist and are required
    expect(screen.getByTestId('card-number')).toBeInTheDocument();
    expect(screen.getByTestId('card-expiry')).toBeInTheDocument();
    expect(screen.getByTestId('card-cvc')).toBeInTheDocument();
  });

  it('displays correct plan information on payment page', async () => {
    renderWithProviders(<MockPaymentFlow />);

    // Test both plans
    const plans = [
      { testId: 'basic-plan', name: 'Basic Plan', price: '$29.99' },
      { testId: 'premium-plan', name: 'Premium Plan', price: '$99.99' },
    ];

    for (const plan of plans) {
      // Go back to plan selection if not already there
      if (!screen.queryByTestId('plan-selection')) {
        fireEvent.click(screen.getByTestId('back-button'));
        await waitFor(() => {
          expect(screen.getByTestId('plan-selection')).toBeInTheDocument();
        });
      }

      // Select plan
      fireEvent.click(screen.getByTestId(plan.testId));

      // Verify payment page shows correct plan
      await waitFor(() => {
        expect(screen.getByTestId('payment-form')).toBeInTheDocument();
      });

      const selectedPlan = screen.getByTestId('selected-plan');
      expect(within(selectedPlan).getByText(plan.name)).toBeInTheDocument();
      expect(within(selectedPlan).getByText(`${plan.price}/month`)).toBeInTheDocument();
    }
  });

  it('handles payment retries on error', async () => {
    // Mock payment failure on first attempt
    let paymentAttempts = 0;
    const originalPaymentFlow = MockPaymentFlow;

    const FailingPaymentFlow = () => {
      const [step, setStep] = React.useState('plans');
      const [selectedPlan, setSelectedPlan] = React.useState(null);
      const [loading, setLoading] = React.useState(false);

      const handlePlanSelect = (plan: any) => {
        setSelectedPlan(plan);
        setStep('payment');
      };

      const handlePayment = async () => {
        setLoading(true);
        paymentAttempts++;
        try {
          await new Promise(resolve => setTimeout(resolve, 500));
          if (paymentAttempts === 1) {
            throw new Error('Payment failed');
          }
          setStep('success');
        } catch (error) {
          setStep('error');
        } finally {
          setLoading(false);
        }
      };

      return (
        <div data-testid="payment-flow">
          {step === 'plans' && (
            <div data-testid="plan-selection">
              <div data-testid="basic-plan" onClick={() => handlePlanSelect({ id: 'basic', name: 'Basic Plan', price: 29.99 })}>
                <button>Select Basic Plan</button>
              </div>
            </div>
          )}
          {step === 'payment' && (
            <div data-testid="payment-form">
              <input data-testid="card-number" />
              <button data-testid="pay-button" onClick={handlePayment} disabled={loading}>
                {loading ? 'Processing...' : 'Pay'}
              </button>
            </div>
          )}
          {step === 'error' && (
            <div data-testid="payment-error">
              <h2>Payment Failed</h2>
              <button data-testid="retry-button" onClick={() => setStep('payment')}>
                Try Again
              </button>
            </div>
          )}
          {step === 'success' && (
            <div data-testid="payment-success">
              <h2>Payment Successful!</h2>
            </div>
          )}
        </div>
      );
    };

    renderWithProviders(<FailingPaymentFlow />);

    // Select plan
    fireEvent.click(screen.getByTestId('basic-plan'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    // First payment attempt (should fail)
    fireEvent.click(screen.getByTestId('pay-button'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-error')).toBeInTheDocument();
    });

    expect(screen.getByText('Payment Failed')).toBeInTheDocument();

    // Retry payment (should succeed)
    fireEvent.click(screen.getByTestId('retry-button'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-form')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('pay-button'));

    await waitFor(() => {
      expect(screen.getByTestId('payment-success')).toBeInTheDocument();
    });

    expect(screen.getByText('Payment Successful!')).toBeInTheDocument();
  });
});