import React from 'react';
import { cn } from '@/lib/utils';

export interface MetricProps extends React.HTMLAttributes<HTMLDivElement> {
  label: React.ReactNode;
  value: React.ReactNode;
  /** Small supporting line: unit, period, source, freshness. */
  hint?: React.ReactNode;
  icon?: React.ReactNode;
}

/** Label / value / hint. Uses a description list so assistive tech reads label then value. */
export function Metric({ label, value, hint, icon, className, ...props }: MetricProps) {
  return (
    <div className={cn('rounded-lg border border-border bg-card p-3', className)} {...props}>
      <dl className="space-y-1">
        <dt className="flex items-center gap-1.5 text-caption font-medium text-muted-foreground [&_svg]:size-3.5">
          {icon ? <span aria-hidden="true">{icon}</span> : null}
          <span className="truncate">{label}</span>
        </dt>
        <dd className="text-xl font-semibold leading-tight tabular-nums text-foreground">{value}</dd>
        {hint ? <dd className="text-caption text-muted-foreground">{hint}</dd> : null}
      </dl>
    </div>
  );
}

/** Responsive strip of metrics. */
export function MetricGrid({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4', className)} {...props} />;
}
