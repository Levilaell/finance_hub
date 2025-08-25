/**
 * Responsive Banner System - Mobile-First Design
 * Solves: altura vertical excessiva + botões saindo para os lados
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

// Banner Container with Mobile-First Responsive Variants
interface ResponsiveBannerContainerProps {
  children: React.ReactNode;
  variant?: 'info' | 'warning' | 'critical' | 'success' | 'neutral';
  className?: string;
}

export function ResponsiveBannerContainer({ 
  children, 
  variant = 'info', 
  className 
}: ResponsiveBannerContainerProps) {
  const variantStyles = {
    info: 'border-blue-200 bg-blue-50 dark:bg-blue-950/10',
    warning: 'border-orange-200 bg-orange-50 dark:bg-orange-950/10', 
    critical: 'border-red-200 bg-red-50 dark:bg-red-950/10',
    success: 'border-green-200 bg-green-50 dark:bg-green-950/10',
    neutral: 'border-muted bg-muted/50'
  };

  return (
    <Card className={cn(
      'mb-4 sm:mb-6 relative', // Reduced mobile margin: 16px → 24px desktop
      variantStyles[variant],
      className
    )}>
      {children}
    </Card>
  );
}

// Banner Content with Responsive Layout
interface ResponsiveBannerContentProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actions?: React.ReactNode;
  dismissButton?: React.ReactNode;
  className?: string;
}

export function ResponsiveBannerContent({
  icon,
  title,
  description,
  actions,
  dismissButton,
  className
}: ResponsiveBannerContentProps) {
  return (
    <CardContent className={cn(
      // Mobile-first responsive padding: 12px → 16px desktop (25% reduction)
      'p-3 sm:p-4',
      // Mobile: Vertical stacking, Desktop: Horizontal layout
      'flex flex-col space-y-3',
      'sm:flex-row sm:space-y-0 sm:items-start sm:justify-between',
      className
    )}>
      {/* Dismiss Button - Absolute positioning to save space */}
      {dismissButton && (
        <div className="absolute top-2 right-2 sm:top-3 sm:right-3">
          {dismissButton}
        </div>
      )}

      {/* Main Content Section */}
      <div className={cn(
        'flex items-start space-x-2 sm:space-x-3',
        'flex-1 min-w-0', // Ensure text can shrink
        dismissButton && 'pr-8' // Space for dismiss button
      )}>
        {/* Icon Container - Responsive sizing */}
        {icon && (
          <div className={cn(
            // Mobile: 32px, Desktop: 40px (20% reduction)
            'h-8 w-8 sm:h-10 sm:w-10',
            'rounded-full flex items-center justify-center flex-shrink-0',
            'bg-primary/10'
          )}>
            {icon}
          </div>
        )}

        {/* Text Content */}
        <div className="flex-1 min-w-0 space-y-1">
          <h4 className={cn(
            // Mobile: smaller text to reduce height
            'text-sm sm:text-base font-medium text-foreground',
            'leading-5' // Tight line-height for mobile
          )}>
            {title}
          </h4>
          <p className={cn(
            // Mobile: smaller text + line clamp to prevent height bloat
            'text-xs sm:text-sm text-muted-foreground',
            'leading-4 sm:leading-5',
            'line-clamp-2 sm:line-clamp-3' // Truncate long text on mobile
          )}>
            {description}
          </p>
        </div>
      </div>

      {/* Actions Section - Mobile: Full width, Desktop: Auto width */}
      {actions && (
        <div className={cn(
          'w-full sm:w-auto sm:ml-4 flex-shrink-0',
          'mt-2 sm:mt-0' // Mobile spacing
        )}>
          {actions}
        </div>
      )}
    </CardContent>
  );
}

// Responsive Button Group - Solves overflow issues
interface ResponsiveButtonGroupProps {
  primary?: {
    label: string;
    onClick: () => void;
    loading?: boolean;
    variant?: 'default' | 'destructive' | 'outline' | 'ghost';
    disabled?: boolean;
  };
  secondary?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'destructive' | 'outline' | 'ghost';
    disabled?: boolean;
  };
  className?: string;
}

export function ResponsiveButtonGroup({ 
  primary, 
  secondary, 
  className 
}: ResponsiveButtonGroupProps) {
  return (
    <div className={cn(
      // Mobile: Vertical stacking (solves overflow), Desktop: Horizontal
      'flex flex-col space-y-2',
      'sm:flex-row sm:space-y-0 sm:space-x-2',
      className
    )}>
      {primary && (
        <Button
          size="sm"
          variant={primary.variant || 'default'}
          onClick={primary.onClick}
          disabled={primary.disabled || primary.loading}
          className={cn(
            // Mobile: Full width (prevents overflow), Desktop: Auto width
            'w-full sm:w-auto',
            // Minimum touch target for accessibility
            'min-h-[44px] sm:min-h-[36px]',
            // Text truncation for very long labels
            'truncate max-w-[200px] sm:max-w-none'
          )}
        >
          {primary.loading ? 'Carregando...' : primary.label}
        </Button>
      )}

      {secondary && (
        <Button
          size="sm"
          variant={secondary.variant || 'ghost'}
          onClick={secondary.onClick}
          disabled={secondary.disabled}
          className={cn(
            'w-full sm:w-auto',
            'min-h-[44px] sm:min-h-[36px]',
            'truncate max-w-[200px] sm:max-w-none'
          )}
        >
          {secondary.label}
        </Button>
      )}
    </div>
  );
}

// Quick Dismiss Button Component
interface ResponsiveDismissButtonProps {
  onClick: () => void;
  className?: string;
}

export function ResponsiveDismissButton({ onClick, className }: ResponsiveDismissButtonProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      className={cn(
        // Mobile: Larger touch target, Desktop: Smaller
        'h-8 w-8 sm:h-6 sm:w-6',
        'text-muted-foreground hover:text-foreground',
        'p-0',
        className
      )}
      aria-label="Fechar banner"
    >
      <X className="h-4 w-4" />
    </Button>
  );
}

// Banner Hook for easy integration
export function useResponsiveBanner() {
  const [dismissed, setDismissed] = React.useState(false);

  const dismiss = React.useCallback(() => {
    setDismissed(true);
  }, []);

  const reset = React.useCallback(() => {
    setDismissed(false);
  }, []);

  return {
    dismissed,
    dismiss,
    reset
  };
}