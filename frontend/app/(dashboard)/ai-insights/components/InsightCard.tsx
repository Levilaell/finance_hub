'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Lightbulb } from 'lucide-react';
import { InsightItem } from '@/services/ai-insights.service';
import { aiInsightsService } from '@/services/ai-insights.service';

interface InsightCardProps {
  title: string;
  items: InsightItem[];
  type: 'alert' | 'opportunity';
  icon?: React.ReactNode;
}

export function InsightCard({ title, items, type, icon }: InsightCardProps) {
  if (items.length === 0) {
    return null;
  }

  const Icon = type === 'alert' ? AlertCircle : Lightbulb;
  const headerColor = type === 'alert' ? 'text-red-600' : 'text-yellow-500';

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className={`text-lg flex items-center gap-2 ${headerColor}`}>
          <Icon className="h-5 w-5" />
          {title} ({items.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {items.map((item, index) => (
            <div
              key={index}
              className="border-l-4 pl-4 py-2"
              style={{
                borderColor: item.severity === 'high' ? '#ef4444' : item.severity === 'medium' ? '#f59e0b' : '#10b981'
              }}
            >
              <div className="flex items-start gap-2 mb-2">
                <span className="text-lg">
                  {aiInsightsService.getSeverityIcon(item.severity)}
                </span>
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">{item.title}</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    {item.description}
                  </p>
                  <div className="bg-muted/50 rounded-lg p-3 mt-2">
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      💡 Recomendação:
                    </p>
                    <p className="text-sm">{item.recommendation}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
