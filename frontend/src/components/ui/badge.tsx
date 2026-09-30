import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

export const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 select-none',
  {
    variants: {
      variant: {
        default: 'border-[#7fc8f8]/60 bg-[#f0f7fe] text-[#257bb5] border',
        secondary: 'border-slate-200 bg-slate-100 text-slate-700 border',
        destructive: 'border-[#ff6392]/40 bg-[#fff0f5] text-[#d93b6e] font-bold border',
        outline: 'border-slate-300 text-slate-700 bg-white border',
        success: 'border-[#7fc8f8]/60 bg-[#f0f9ff] text-[#257bb5] font-bold border',
        warning: 'border-[#ffe45e]/80 bg-[#fffde6] text-[#967b00] font-bold border',
        info: 'border-[#7fc8f8]/60 bg-[#f0f7fe] text-[#257bb5] border',
        purple: 'border-[#5aa9e6]/60 bg-[#f0f7fe] text-[#257bb5] border',
        indigo: 'border-[#5aa9e6]/60 bg-[#f0f7fe] text-[#257bb5] border',
        teal: 'border-[#7fc8f8]/60 bg-[#f0f9ff] text-[#257bb5] border',
        slate: 'border-slate-200 bg-slate-100 text-slate-700 border',
        sky: 'border-[#7fc8f8]/60 bg-[#f0f7fe] text-[#257bb5] border',
        gold: 'border-[#ffe45e]/80 bg-[#fffde6] text-[#967b00] font-bold border',
        rose: 'border-[#ff6392]/40 bg-[#fff0f5] text-[#d93b6e] font-bold border',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}
