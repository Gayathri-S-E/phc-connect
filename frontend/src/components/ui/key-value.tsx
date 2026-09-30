import React from 'react';
import { cn } from '@/lib/utils';

export interface KeyValueItem {
  label: React.ReactNode;
  value: React.ReactNode;
}

export interface KeyValueListProps extends React.HTMLAttributes<HTMLDListElement> {
  items: KeyValueItem[];
  /** stacked = label above value; inline = label left, value right (aligned columns). */
  layout?: 'stacked' | 'inline';
}

/** Semantic description list for record details (patient, facility, batch ...). */
export function KeyValueList({ items, layout = 'inline', className, ...props }: KeyValueListProps) {
  return (
    <dl className={cn('divide-y divide-border text-small', className)} {...props}>
      {items.map((item, i) => (
        <div
          key={i}
          className={cn('py-2', layout === 'inline' ? 'grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3' : 'space-y-0.5')}
        >
          <dt className="text-muted-foreground">{item.label}</dt>
          <dd className="min-w-0 break-words font-medium text-foreground">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
