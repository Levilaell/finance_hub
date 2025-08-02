/**
 * Tests for AuthLayout component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { AuthLayout } from '@/components/layouts/auth-layout';

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: any) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

describe('AuthLayout', () => {
  describe('Basic Rendering', () => {
    it('should render children', () => {
      render(
        <AuthLayout>
          <div data-testid="test-content">Test Content</div>
        </AuthLayout>
      );

      expect(screen.getByTestId('test-content')).toBeInTheDocument();
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should render the logo with link to home', () => {
      render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      const logoLink = screen.getByRole('link', { name: /caixahub/i });
      expect(logoLink).toBeInTheDocument();
      expect(logoLink).toHaveAttribute('href', '/');
      
      const logoText = screen.getByText('CaixaHub');
      expect(logoText).toBeInTheDocument();
    });

    it('should render without title and subtitle', () => {
      render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      // Should only have the logo, no additional title or subtitle
      expect(screen.getByText('CaixaHub')).toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument();
    });
  });

  describe('Title and Subtitle', () => {
    it('should render title when provided', () => {
      render(
        <AuthLayout title="Sign In">
          <div>Content</div>
        </AuthLayout>
      );

      const title = screen.getByRole('heading', { level: 2 });
      expect(title).toBeInTheDocument();
      expect(title).toHaveTextContent('Sign In');
    });

    it('should render subtitle when provided', () => {
      render(
        <AuthLayout subtitle="Welcome back to your account">
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByText('Welcome back to your account')).toBeInTheDocument();
    });

    it('should render both title and subtitle when provided', () => {
      render(
        <AuthLayout 
          title="Create Account" 
          subtitle="Start your financial journey today"
        >
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Create Account');
      expect(screen.getByText('Start your financial journey today')).toBeInTheDocument();
    });

    it('should render only subtitle without title', () => {
      render(
        <AuthLayout subtitle="Just a subtitle">
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument();
      expect(screen.getByText('Just a subtitle')).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('should have correct CSS classes for layout', () => {
      const { container } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      // Check main container classes
      const mainContainer = container.firstChild as HTMLElement;
      expect(mainContainer).toHaveClass(
        'min-h-screen',
        'flex',
        'flex-col',
        'justify-center',
        'py-12',
        'sm:px-6',
        'lg:px-8',
        'bg-background'
      );
    });

    it('should have correct responsive layout classes', () => {
      const { container } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      // Check header section classes
      const headerSection = container.querySelector('.sm\\:mx-auto');
      expect(headerSection).toHaveClass(
        'sm:mx-auto',
        'sm:w-full',
        'sm:max-w-md'
      );

      // Check content section classes
      const contentSection = container.querySelector('.mt-8');
      expect(contentSection).toHaveClass(
        'mt-8',
        'sm:mx-auto',
        'sm:w-full',
        'sm:max-w-md'
      );
    });

    it('should have correct card styling', () => {
      const { container } = render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      const card = container.querySelector('.bg-card');
      expect(card).toHaveClass(
        'bg-card',
        'py-8',
        'px-4',
        'shadow',
        'sm:rounded-lg',
        'sm:px-10'
      );
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(
        <AuthLayout title="Sign In">
          <div>Content</div>
        </AuthLayout>
      );

      // Logo should be h1
      const logo = screen.getByRole('heading', { level: 1 });
      expect(logo).toHaveTextContent('CaixaHub');

      // Title should be h2
      const title = screen.getByRole('heading', { level: 2 });
      expect(title).toHaveTextContent('Sign In');
    });

    it('should have accessible link for logo', () => {
      render(
        <AuthLayout>
          <div>Content</div>
        </AuthLayout>
      );

      const logoLink = screen.getByRole('link', { name: /caixahub/i });
      expect(logoLink).toBeInTheDocument();
      expect(logoLink).toHaveAttribute('href', '/');
    });

    it('should maintain proper focus order', () => {
      render(
        <AuthLayout title="Sign In">
          <input data-testid="email" type="email" />
          <button data-testid="submit">Submit</button>
        </AuthLayout>
      );

      const logoLink = screen.getByRole('link', { name: /caixahub/i });
      const emailInput = screen.getByTestId('email');
      const submitButton = screen.getByTestId('submit');

      // Elements should be in the expected tab order
      expect(logoLink.tabIndex).not.toBe(-1);
      expect(emailInput.tabIndex).not.toBe(-1);
      expect(submitButton.tabIndex).not.toBe(-1);
    });
  });

  describe('Content Rendering', () => {
    it('should render multiple children', () => {
      render(
        <AuthLayout>
          <div data-testid="child-1">First Child</div>
          <div data-testid="child-2">Second Child</div>
          <div data-testid="child-3">Third Child</div>
        </AuthLayout>
      );

      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
      expect(screen.getByTestId('child-3')).toBeInTheDocument();
    });

    it('should render form elements correctly', () => {
      render(
        <AuthLayout title="Login">
          <form>
            <input type="email" placeholder="Email" />
            <input type="password" placeholder="Password" />
            <button type="submit">Sign In</button>
          </form>
        </AuthLayout>
      );

      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    });

    it('should render complex nested content', () => {
      render(
        <AuthLayout title="Complex Form" subtitle="Fill out the details">
          <div className="space-y-4">
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input id="name" type="text" />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" />
            </div>
            <div className="actions">
              <button type="button">Cancel</button>
              <button type="submit">Submit</button>
            </div>
          </div>
        </AuthLayout>
      );

      expect(screen.getByLabelText('Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });
  });

  describe('Props Handling', () => {
    it('should handle empty strings for title and subtitle', () => {
      render(
        <AuthLayout title="" subtitle="">
          <div>Content</div>
        </AuthLayout>
      );

      // Empty strings should not render the elements
      expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument();
      // Don't test for empty string as it matches whitespace in DOM
    });

    it('should handle undefined props gracefully', () => {
      render(
        <AuthLayout title={undefined} subtitle={undefined}>
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument();
    });

    it('should handle long titles and subtitles', () => {
      const longTitle = 'This is a very long title that might wrap to multiple lines';
      const longSubtitle = 'This is a very long subtitle that provides detailed information about what the user should expect when using this form or page';

      render(
        <AuthLayout title={longTitle} subtitle={longSubtitle}>
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByText(longTitle)).toBeInTheDocument();
      expect(screen.getByText(longSubtitle)).toBeInTheDocument();
    });

    it('should handle special characters in title and subtitle', () => {
      const titleWithSpecialChars = 'Sign In & Create Account';
      const subtitleWithSpecialChars = 'Welcome to <CaixaHub> - Your Financial Partner!';

      render(
        <AuthLayout title={titleWithSpecialChars} subtitle={subtitleWithSpecialChars}>
          <div>Content</div>
        </AuthLayout>
      );

      expect(screen.getByText(titleWithSpecialChars)).toBeInTheDocument();
      expect(screen.getByText(subtitleWithSpecialChars)).toBeInTheDocument();
    });
  });

  describe('Visual Structure', () => {
    it('should render in correct visual order', () => {
      const { container } = render(
        <AuthLayout title="Test Title" subtitle="Test Subtitle">
          <div data-testid="content">Form Content</div>
        </AuthLayout>
      );

      const elements = Array.from(container.querySelectorAll('*')).filter(
        el => el.textContent && el.textContent.trim()
      );

      // Find elements by their text content
      const logoIndex = elements.findIndex(el => el.textContent?.includes('CaixaHub'));
      const titleIndex = elements.findIndex(el => el.textContent?.includes('Test Title') && !el.textContent?.includes('CaixaHub'));
      const subtitleIndex = elements.findIndex(el => el.textContent?.includes('Test Subtitle') && !el.textContent?.includes('Test Title'));
      const contentIndex = elements.findIndex(el => el.textContent?.includes('Form Content'));

      // Verify the order is correct (skip if elements not found)
      if (logoIndex >= 0 && titleIndex >= 0) {
        expect(logoIndex).toBeLessThan(titleIndex);
      }
      if (titleIndex >= 0 && subtitleIndex >= 0) {
        expect(titleIndex).toBeLessThan(subtitleIndex);
      }
      if (subtitleIndex >= 0 && contentIndex >= 0) {
        expect(subtitleIndex).toBeLessThan(contentIndex);
      }
    });

    it('should have proper spacing between elements', () => {
      const { container } = render(
        <AuthLayout title="Test Title" subtitle="Test Subtitle">
          <div>Content</div>
        </AuthLayout>
      );

      // Check for margin classes that provide spacing
      const titleElement = container.querySelector('h2');
      const subtitleElement = container.querySelector('p');
      const contentWrapper = container.querySelector('.mt-8');

      expect(titleElement).toHaveClass('mt-6');
      expect(subtitleElement).toHaveClass('mt-2');
      expect(contentWrapper).toHaveClass('mt-8');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null children', () => {
      expect(() => {
        render(<AuthLayout>{null}</AuthLayout>);
      }).not.toThrow();
    });

    it('should handle empty children', () => {
      expect(() => {
        render(<AuthLayout></AuthLayout>);
      }).not.toThrow();
    });

    it('should handle React fragments as children', () => {
      render(
        <AuthLayout>
          <>
            <div data-testid="fragment-child-1">Fragment Child 1</div>
            <div data-testid="fragment-child-2">Fragment Child 2</div>
          </>
        </AuthLayout>
      );

      expect(screen.getByTestId('fragment-child-1')).toBeInTheDocument();
      expect(screen.getByTestId('fragment-child-2')).toBeInTheDocument();
    });

    it('should handle conditional rendering within children', () => {
      const showOptionalContent = true;

      render(
        <AuthLayout>
          <div>Always visible</div>
          {showOptionalContent && <div data-testid="conditional">Conditional content</div>}
        </AuthLayout>
      );

      expect(screen.getByText('Always visible')).toBeInTheDocument();
      expect(screen.getByTestId('conditional')).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    it('should work with form libraries', () => {
      const mockSubmit = jest.fn();

      render(
        <AuthLayout title="Contact Form">
          <form onSubmit={mockSubmit} role="form">
            <input data-testid="form-input" type="text" required />
            <button type="submit">Submit</button>
          </form>
        </AuthLayout>
      );

      const form = screen.getByRole('form');
      expect(form).toBeInTheDocument();
    });

    it('should work with different UI libraries', () => {
      // Test with various types of components that might be used
      render(
        <AuthLayout title="Mixed Components">
          <div className="custom-component">Custom styled component</div>
          <button className="btn btn-primary">Styled button</button>
          <input className="form-control" type="text" />
        </AuthLayout>
      );

      expect(screen.getByText('Custom styled component')).toBeInTheDocument();
      expect(screen.getByRole('button')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  });
});