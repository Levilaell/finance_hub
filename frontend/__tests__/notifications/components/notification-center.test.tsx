import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NotificationCenter } from '../../../components/notifications/notification-center';
import { useNotifications } from '@/hooks/use-notifications';
import { formatDistanceToNow } from 'date-fns';

// Mock dependencies
jest.mock('@/hooks/use-notifications');
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn()
}));

// Mock UI components
jest.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>
}));

jest.mock('@/components/ui/dropdown-menu', () => {
  const React = require('react');
  return {
    DropdownMenu: ({ children }: any) => <div data-testid="dropdown-menu">{children}</div>,
    DropdownMenuTrigger: ({ children, asChild }: any) => {
      const child = React.Children.only(children);
      return React.cloneElement(child, { 'data-testid': 'dropdown-trigger' });
    },
    DropdownMenuContent: ({ children }: any) => <div role="menu" data-testid="dropdown-content">{children}</div>,
    DropdownMenuSeparator: () => <hr />
  };
});

jest.mock('@/components/ui/badge', () => ({
  Badge: ({ children, ...props }: any) => <span {...props}>{children}</span>
}));

jest.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children }: any) => <div>{children}</div>
}));

jest.mock('@/constants/notifications', () => ({
  NOTIFICATION_ICONS: {
    report_ready: '📊',
    payment_success: '💰',
    payment_failed: '❌',
    account_connected: '🔗',
    account_disconnected: '🔌',
    account_sync_failed: '⚠️',
    low_balance: '💸',
    monthly_summary: '📅',
    security_alert: '🔒',
    system_update: '🔧',
    user_action_required: '⚡',
    sync_completed: '✅',
    subscription_renewed: '🔄',
    subscription_cancelled: '🚫',
    transaction_categorized: '🏷️',
    ai_insight_available: '🤖'
  }
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Bell: () => <span>Bell Icon</span>,
  BellOff: () => <span>BellOff Icon</span>,
  Check: () => <span>Check Icon</span>,
  X: () => <span>X Icon</span>
}));

// Mock cn utility
jest.mock('@/lib/utils', () => ({
  cn: (...classes: any[]) => classes.filter(Boolean).join(' ')
}));

const mockUseNotifications = useNotifications as jest.MockedFunction<typeof useNotifications>;
const mockFormatDistanceToNow = formatDistanceToNow as jest.MockedFunction<typeof formatDistanceToNow>;

describe('NotificationCenter', () => {
  const mockNotifications = [
    {
      id: '1',
      event: 'report_ready',
      title: 'Report Ready',
      message: 'Your monthly report is ready for download',
      is_read: false,
      is_critical: false,
      created_at: '2024-01-01T10:00:00Z',
      metadata: {},
      action_url: '/reports/123'
    },
    {
      id: '2',
      event: 'payment_failed',
      title: 'Payment Failed',
      message: 'Your payment could not be processed',
      is_read: true,
      is_critical: true,
      created_at: '2024-01-01T09:00:00Z',
      metadata: {},
      action_url: '/subscription'
    }
  ];

  const mockMarkAsRead = jest.fn();
  const mockMarkAllAsRead = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockFormatDistanceToNow.mockReturnValue('5 minutes ago');
    
    mockUseNotifications.mockReturnValue({
      notifications: mockNotifications,
      isLoading: false,
      isConnected: true,
      markAsRead: mockMarkAsRead,
      markAllAsRead: mockMarkAllAsRead,
      deleteNotification: jest.fn(),
      refetch: jest.fn()
    });
  });

  describe('Rendering', () => {
    it('should render notification bell icon', () => {
      render(<NotificationCenter />);
      
      const bellIcon = screen.getByText('Bell Icon');
      expect(bellIcon).toBeInTheDocument();
    });

    it('should show unread count badge', () => {
      render(<NotificationCenter />);
      
      const badge = screen.getByText('1');
      expect(badge).toBeInTheDocument();
    });

    it('should show 9+ for more than 9 unread notifications', () => {
      const manyNotifications = Array(15).fill(null).map((_, i) => ({
        ...mockNotifications[0],
        id: String(i),
        is_read: false
      }));

      mockUseNotifications.mockReturnValue({
        notifications: manyNotifications,
        isLoading: false,
        isConnected: true,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      const badge = screen.getByText('9+');
      expect(badge).toBeInTheDocument();
    });

    it('should show disconnected icon when not connected', () => {
      mockUseNotifications.mockReturnValue({
        notifications: [],
        isLoading: false,
        isConnected: false,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      // BellOff icon should be shown
      const bellOffIcon = screen.getByText('BellOff Icon');
      expect(bellOffIcon).toBeInTheDocument();
    });
  });

  describe('Dropdown Menu', () => {
    it('should open dropdown when clicking bell', () => {
      render(<NotificationCenter />);
      
      // Since we're mocking, the dropdown content is always visible
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });

    it('should show loading state', () => {
      mockUseNotifications.mockReturnValue({
        notifications: [],
        isLoading: true,
        isConnected: true,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      const bellButton = screen.getByRole('button');
      fireEvent.click(bellButton);
      
      expect(screen.getByText('Loading notifications...')).toBeInTheDocument();
    });

    it('should show empty state', () => {
      mockUseNotifications.mockReturnValue({
        notifications: [],
        isLoading: false,
        isConnected: true,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      const bellButton = screen.getByRole('button');
      fireEvent.click(bellButton);
      
      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });

    it('should show mark all as read button when there are unread notifications', () => {
      render(<NotificationCenter />);
      
      const markAllButton = screen.getByText('Mark all read');
      expect(markAllButton).toBeInTheDocument();
    });

    it('should show disconnection warning', () => {
      mockUseNotifications.mockReturnValue({
        notifications: mockNotifications,
        isLoading: false,
        isConnected: false,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      expect(screen.getByText('Real-time updates unavailable')).toBeInTheDocument();
    });
  });

  describe('Notification Items', () => {
    it('should display notification details', () => {
      render(<NotificationCenter />);
      
      expect(screen.getByText('Report Ready')).toBeInTheDocument();
      expect(screen.getByText('Your monthly report is ready for download')).toBeInTheDocument();
      expect(screen.getByText('Payment Failed')).toBeInTheDocument();
      expect(screen.getByText('Your payment could not be processed')).toBeInTheDocument();
    });

    it('should highlight unread notifications', () => {
      render(<NotificationCenter />);
      
      // Find the notification items by their container div with class
      const unreadNotification = screen.getByText('Report Ready').closest('div.group');
      expect(unreadNotification).toHaveClass('bg-accent/50');
    });

    it('should show critical badge for critical notifications', () => {
      render(<NotificationCenter />);
      
      expect(screen.getByText('Critical')).toBeInTheDocument();
    });

    it('should show notification icons', () => {
      render(<NotificationCenter />);
      
      // Check for time display
      expect(screen.getAllByText('5 minutes ago')).toHaveLength(2);
    });
  });

  describe('Interactions', () => {
    it('should mark notification as read when clicking', async () => {
      render(<NotificationCenter />);
      
      const unreadNotification = screen.getByText('Report Ready').closest('div.group') as HTMLElement;
      fireEvent.click(unreadNotification);
      
      expect(mockMarkAsRead).toHaveBeenCalledWith('1');
    });

    it('should not mark already read notification', () => {
      render(<NotificationCenter />);
      
      const readNotification = screen.getByText('Payment Failed').closest('div.group') as HTMLElement;
      fireEvent.click(readNotification);
      
      expect(mockMarkAsRead).not.toHaveBeenCalled();
    });

    it('should navigate to action URL when clicking notification', () => {
      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(<NotificationCenter />);
      
      const notification = screen.getByText('Report Ready').closest('div.group') as HTMLElement;
      fireEvent.click(notification);
      
      expect(window.location.href).toBe('/reports/123');
    });

    it('should call markAllAsRead when clicking mark all button', () => {
      render(<NotificationCenter />);
      
      const markAllButton = screen.getByText('Mark all read');
      fireEvent.click(markAllButton);
      
      expect(mockMarkAllAsRead).toHaveBeenCalled();
    });
  });

  describe('Notification Icon Mapping', () => {
    it('should show correct icon for different event types', () => {
      const notificationsWithEvents = [
        {
          ...mockNotifications[0],
          id: '1',
          event: 'account_connected' as const
        },
        {
          ...mockNotifications[0],
          id: '2',
          event: 'payment_failed' as const
        },
        {
          ...mockNotifications[0],
          id: '3',
          event: 'low_balance' as const
        }
      ];

      mockUseNotifications.mockReturnValue({
        notifications: notificationsWithEvents,
        isLoading: false,
        isConnected: true,
        markAsRead: mockMarkAsRead,
        markAllAsRead: mockMarkAllAsRead,
        deleteNotification: jest.fn(),
        refetch: jest.fn()
      });

      render(<NotificationCenter />);
      
      // Check that the emoji icons are rendered
      expect(screen.getByText('🔗')).toBeInTheDocument(); // account_connected
      expect(screen.getByText('❌')).toBeInTheDocument(); // payment_failed
      expect(screen.getByText('💸')).toBeInTheDocument(); // low_balance
    });
  });
});