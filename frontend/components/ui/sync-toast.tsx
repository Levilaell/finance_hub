/**
 * Custom toast component for sync status messages
 * Provides rich feedback with actions for error scenarios
 */

import { ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface SyncToastProps {
  message: string;
  errorMessage?: string;
  type: 'error' | 'warning' | 'info';
}

export function SyncToast({ message, errorMessage, type }: SyncToastProps) {
  const icons = {
    error: ExclamationTriangleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  };

  const colors = {
    error: 'text-red-400',
    warning: 'text-amber-400',
    info: 'text-blue-400',
  };

  const Icon = icons[type];
  const iconColor = colors[type];

  return (
    <div className="flex flex-col gap-2 max-w-md">
      <div className="flex items-start gap-3">
        <Icon className={`h-5 w-5 mt-0.5 flex-shrink-0 ${iconColor}`} />
        <div className="flex-1">
          <p className="text-sm font-medium text-white">{message}</p>
          {errorMessage && (
            <p className="text-xs text-gray-300 mt-1">{errorMessage}</p>
          )}
        </div>
      </div>
    </div>
  );
}
