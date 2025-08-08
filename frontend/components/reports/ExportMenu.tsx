import React from 'react';
import { Download, FileText, FileSpreadsheet, FileJson } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { reportsService } from '@/services/reports.service';

interface ExportMenuProps {
  data: any;
  filename: string;
  disabled?: boolean;
}

export function ExportMenu({ data, filename, disabled = false }: ExportMenuProps) {
  const handleExport = (format: 'csv' | 'json' | 'pdf' | 'xlsx') => {
    try {
      if (format === 'csv' || format === 'json') {
        // Client-side export for CSV and JSON
        const exportData = reportsService.formatReportData(data, format);
        const blob = new Blob([exportData as string], {
          type: format === 'csv' ? 'text/csv' : 'application/json',
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        toast.success(`Dados exportados como ${format.toUpperCase()}`);
      } else {
        // For PDF and XLSX, we need server-side generation
        toast.info('Por favor, use o gerador de relatórios para PDF e Excel');
      }
    } catch (error) {
      toast.error('Erro ao exportar dados');
      console.error('Export error:', error);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled || !data}>
          <Download className="h-4 w-4 mr-2" />
          Exportar
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => handleExport('csv')}>
          <FileText className="h-4 w-4 mr-2" />
          Exportar como CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('json')}>
          <FileJson className="h-4 w-4 mr-2" />
          Exportar como JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('pdf')} disabled>
          <FileText className="h-4 w-4 mr-2" />
          Exportar como PDF (usar gerador)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('xlsx')} disabled>
          <FileSpreadsheet className="h-4 w-4 mr-2" />
          Exportar como Excel (usar gerador)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}