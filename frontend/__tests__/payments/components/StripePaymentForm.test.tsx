/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { StripePaymentForm } from '../../../components/payment/StripePaymentForm';

jest.mock('@stripe/stripe-js', () => ({
  loadStripe: jest.fn(() => Promise.resolve({
    elements: jest.fn(),
    createToken: jest.fn(),
    createPaymentMethod: jest.fn(),
    confirmCardPayment: jest.fn(),
    retrievePaymentIntent: jest.fn(),
  })),
}));

jest.mock('@stripe/react-stripe-js', () => ({
  Elements: ({ children, ...props }: any) => <div data-testid="stripe-elements" {...props}>{children}</div>,
  CardElement: (props: any) => (
    <div data-testid="card-element" {...props}>
      <input 
        data-testid="card-input" 
        onChange={(e) => props.onChange && props.onChange({
          complete: e.target.value.length > 0,
          error: null,
          brand: 'visa'
        })}
      />
    </div>
  ),
  useStripe: () => mockStripe,
  useElements: () => ({
    getElement: jest.fn(() => ({
      focus: jest.fn(),
      blur: jest.fn(),
      clear: jest.fn(),
    })),
  }),
}));

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/payment',
    query: {},
  }),
}));

// Mock toast notifications
jest.mock('../../../lib/utils', () => ({
  cn: jest.fn((...classes) => classes.filter(Boolean).join(' ')),
}));

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock Stripe instance for test use
const mockStripe = {
  elements: jest.fn(),
  createToken: jest.fn(),
  createPaymentMethod: jest.fn(),
  confirmCardPayment: jest.fn(),
  retrievePaymentIntent: jest.fn(),
};

describe('StripePaymentForm', () => {
  const defaultProps = {
    clientSecret: 'pi_test_1234567890',
    amount: 2999, // $29.99
    onSuccess: jest.fn(),
    onError: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockStripe.confirmCardPayment.mockResolvedValue({
      paymentIntent: {
        status: 'succeeded',
        id: 'pi_test_1234567890',
      },
    });
  });

  it('renders payment form correctly', () => {
    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} />
      </Elements>
    );

    expect(screen.getByTestId('stripe-elements')).toBeInTheDocument();
    expect(screen.getByTestId('card-element')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /pay/i })).toBeInTheDocument();
  });

  it('displays correct amount', () => {
    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} />
      </Elements>
    );

    // Amount should be displayed formatted as currency
    expect(screen.getByText(/\$29\.99/)).toBeInTheDocument();
  });

  it('handles successful payment', async () => {
    const onSuccess = jest.fn();
    
    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} onSuccess={onSuccess} />
      </Elements>
    );

    // Fill in card details
    const cardInput = screen.getByTestId('card-input');
    fireEvent.change(cardInput, { target: { value: '4242424242424242' } });

    // Submit payment
    const submitButton = screen.getByRole('button', { name: /pay/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockStripe.confirmCardPayment).toHaveBeenCalledWith(
        defaultProps.clientSecret,
        expect.any(Object)
      );
      expect(onSuccess).toHaveBeenCalledWith({
        paymentIntent: {
          status: 'succeeded',
          id: 'pi_test_1234567890',
        },
      });
    });
  });

  it('handles payment failure', async () => {
    const onError = jest.fn();
    mockStripe.confirmCardPayment.mockResolvedValue({
      error: {
        type: 'card_error',
        code: 'card_declined',
        message: 'Your card was declined.',
      },
    });

    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} onError={onError} />
      </Elements>
    );

    // Fill in card details
    const cardInput = screen.getByTestId('card-input');
    fireEvent.change(cardInput, { target: { value: '4000000000000002' } });

    // Submit payment
    const submitButton = screen.getByRole('button', { name: /pay/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith({
        type: 'card_error',
        code: 'card_declined',
        message: 'Your card was declined.',
      });
    });
  });

  it('disables submit button when card is incomplete', () => {
    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} />
      </Elements>
    );

    const submitButton = screen.getByRole('button', { name: /pay/i });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when card is complete', async () => {
    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} />
      </Elements>
    );

    // Fill in card details
    const cardInput = screen.getByTestId('card-input');
    fireEvent.change(cardInput, { target: { value: '4242424242424242' } });

    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /pay/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('shows loading state during payment processing', async () => {
    // Mock a slow payment confirmation
    mockStripe.confirmCardPayment.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        paymentIntent: { status: 'succeeded', id: 'pi_test_1234567890' }
      }), 1000))
    );

    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} />
      </Elements>
    );

    // Fill in card details
    const cardInput = screen.getByTestId('card-input');
    fireEvent.change(cardInput, { target: { value: '4242424242424242' } });

    // Submit payment
    const submitButton = screen.getByRole('button', { name: /pay/i });
    fireEvent.click(submitButton);

    // Check for loading state
    expect(screen.getByText(/processing/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('handles network errors gracefully', async () => {
    const onError = jest.fn();
    mockStripe.confirmCardPayment.mockRejectedValue(new Error('Network error'));

    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} onError={onError} />
      </Elements>
    );

    // Fill in card details
    const cardInput = screen.getByTestId('card-input');
    fireEvent.change(cardInput, { target: { value: '4242424242424242' } });

    // Submit payment
    const submitButton = screen.getByRole('button', { name: /pay/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(new Error('Network error'));
    });
  });

  it('validates required client secret', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <Elements stripe={mockStripe}>
        <StripePaymentForm {...defaultProps} clientSecret="" />
      </Elements>
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Client secret is required')
    );

    consoleSpy.mockRestore();
  });
});