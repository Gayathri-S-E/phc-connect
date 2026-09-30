import React from 'react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  /** What is empty, e.g. "No appointments today". */
  title: React.ReactNode;
  /** Why it matters / what this area is for. */
  why?: React.ReactNode;
  /** Optional leading icon (decorative). */
  icon?: React.ReactNode;
  /** Next action (real actions only): a Button, link, or group. */
  action?: React.ReactNode;
}

/** Empty state pattern: what is empty + why it matters + next action. Left-aligned, bordered, no illustration. */
export function EmptyState({ title, why, icon, action, className, ...props }: EmptyStateProps) {
  return (
    <div
      className={cn('flex flex-col items-start gap-3 rounded-lg border border-dashed border-input bg-card p-6 sm:flex-row sm:items-center', className)}
      {...props}
    >
      {icon ? (
        <div aria-hidden="true" className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary-text [&_svg]:size-5">
          {icon}
        </div>
      ) : null}
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-small font-semibold text-foreground">{title}</p>
        {why ? <p className="max-w-prose text-small text-muted-foreground">{why}</p> : null}
      </div>
      {action ? <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div> : null}
    </div>
  );
}
