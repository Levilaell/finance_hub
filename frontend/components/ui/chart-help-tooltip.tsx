'use client';

import { useState } from 'react';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ChartHelpTooltipProps {
  content: string;
}

export function ChartHelpTooltip({ content }: ChartHelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Para mobile, usar click; para desktop, usar hover
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip open={isOpen} onOpenChange={setIsOpen}>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={handleClick}
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={() => setIsOpen(false)}
            className="inline-flex items-center justify-center ml-2 text-white/50 hover:text-white/80 transition-colors focus:outline-none"
            aria-label="Ajuda sobre este gráfico"
          >
            <QuestionMarkCircleIcon className="h-5 w-5" />
          </button>
        </TooltipTrigger>
        <TooltipContent
          side="bottom"
          align="start"
          className="max-w-sm p-3 bg-slate-800 text-white border-slate-600 text-sm z-50"
          sideOffset={5}
        >
          <p className="leading-relaxed">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
