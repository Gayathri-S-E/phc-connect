import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { CircleAlert, CircleCheck, CircleDot, Info, Sparkles, TriangleAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

export type StatusTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'ai';

export const statusBadgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-semibold whitespace-nowrap select-none [&_svg]:size-3.5 [&_svg]:shrink-0',
  {
    variants: {
      status: {
        success: 'border-success-border bg-success-soft text-success-text',
        warning: 'border-warning-border bg-warning-soft text-warning-text',
        danger: 'border-danger-border bg-danger-soft text-danger-text',
        info: 'border-info-border bg-info-soft text-info-text',
        neutral: 'border-neutral-border bg-neutral-soft text-neutral-text',
        ai: 'border-ai-border bg-ai-soft text-ai-text',
      },
    },
    defaultVariants: { status: 'neutral' },
  }
);

const defaultIcons: Record<StatusTone, React.ReactNode> = {
  success: <CircleCheck aria-hidden="true" />,
  warning: <TriangleAlert aria-hidden="true" />,
  danger: <CircleAlert aria-hidden="true" />,
  info: <Info aria-hidden="true" />,
  neutral: <CircleDot aria-hidden="true" />,
  ai: <Sparkles aria-hidden="true" />,
};

export interface StatusBadgeProps
  extends Omit<React.HTMLAttributes<HTMLSpanElement>, 'children'>,
    VariantProps<typeof statusBadgeVariants> {
  /** Visible text label. Required: status is never conveyed by colour alone. */
  label: React.ReactNode;
  /** Override the default icon for the tone. */
  icon?: React.ReactNode;
}

/** State chip: icon + label + colour. Variants: success / warning / danger / info / neutral / ai. */
export function StatusBadge({ status = 'neutral', label, icon, className, ...props }: StatusBadgeProps) {
  const tone = (status ?? 'neutral') as StatusTone;
  return (
    <span className={cn(statusBadgeVariants({ status: tone }), className)} {...props}>
      {icon ?? defaultIcons[tone]}
      <span>{label}</span>
    </span>
  );
}
