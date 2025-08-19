import React, { memo, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Sector,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface CategoryData {
  category: {
    name: string;
    icon?: string;
  };
  amount: number;
  percentage: number;
}

interface CategoryPieChartProps {
  data: CategoryData[] | null;
  isLoading?: boolean;
  height?: number;
  showLegend?: boolean;
}

const COLORS = [
  'hsl(0 0% 9%)',   // Near black
  'hsl(0 0% 18%)',  // Dark gray
  'hsl(0 0% 35%)',  // Medium gray
  'hsl(0 0% 50%)',  // True neutral
  'hsl(0 0% 65%)',  // Light gray
  'hsl(0 0% 82%)',  // Very light gray
  'hsl(120 60% 40%)', // Success green (semantic only)
  'hsl(0 60% 45%)',   // Error red (semantic only)
  'hsl(45 90% 40%)',  // Warning amber (semantic only)
  'hsl(220 60% 45%)', // Info blue (semantic only)
];

const renderActiveShape = (props: any) => {
  const RADIAN = Math.PI / 180;
  const {
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
    value,
  } = props;
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? 'start' : 'end';

  return (
    <g>
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill}>
        {payload.category.name}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
      <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
      <text
        x={ex + (cos >= 0 ? 1 : -1) * 12}
        y={ey}
        textAnchor={textAnchor}
        className="fill-foreground"
        fontSize={14}
      >
        {formatCurrency(value)}
      </text>
      <text
        x={ex + (cos >= 0 ? 1 : -1) * 12}
        y={ey}
        dy={18}
        textAnchor={textAnchor}
        className="fill-muted-foreground"
        fontSize={12}
      >
        {`(${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

const CategoryPieChart = memo(({ 
  data, 
  isLoading = false, 
  height = 320,
  showLegend = true 
}: CategoryPieChartProps) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  if (isLoading) {
    return (
      <div className="w-full" style={{ height }}>
        <Skeleton className="w-full h-full rounded-full mx-auto" style={{ maxWidth: height }} />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <p className="text-muted-foreground">Sem dados disponíveis</p>
      </div>
    );
  }

  // Prepare data for the chart - limit to top 8 for better visualization
  const chartData = data.slice(0, 8).map((item) => ({
    ...item,
    name: item.category.name,
  }));

  // Calculate chart and legend heights
  const chartHeight = showLegend ? height - 80 : height;
  
  return (
    <div style={{ height, position: 'relative' }}>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <PieChart>
          <Pie
            activeIndex={activeIndex}
            activeShape={renderActiveShape}
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={showLegend ? 70 : 80}
            fill="#8884d8"
            dataKey="amount"
            onMouseEnter={onPieEnter}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value: number) => formatCurrency(value)}
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      
      {showLegend && (
        <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 px-2 mt-2" style={{ maxHeight: '70px', overflow: 'hidden' }}>
          {chartData.map((entry, index) => (
            <div key={`legend-${index}`} className="flex items-center gap-1 text-xs">
              <div 
                className="w-2 h-2 rounded-full flex-shrink-0" 
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <span className="text-muted-foreground truncate" style={{ maxWidth: '100px' }}>
                {entry.name.length > 12 ? entry.name.substring(0, 10) + '...' : entry.name}
              </span>
              <span className="text-muted-foreground">
                ({entry.percentage || 0}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

CategoryPieChart.displayName = 'CategoryPieChart';

export { CategoryPieChart };