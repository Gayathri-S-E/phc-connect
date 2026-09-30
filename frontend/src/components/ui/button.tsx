import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-[#5aa9e6] text-white hover:bg-[#4396d4] shadow-xs active:scale-[0.98]',
        primary: 'bg-[#5aa9e6] text-white hover:bg-[#4396d4] shadow-xs active:scale-[0.98]',
        secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 shadow-2xs active:scale-[0.98]',
        destructive: 'bg-[#ff6392] text-white hover:bg-[#e04f7b] shadow-xs active:scale-[0.98]',
        outline: 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50 hover:border-slate-400 shadow-2xs active:scale-[0.98]',
        ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
        link: 'text-[#5aa9e6] underline-offset-4 hover:underline p-0 h-auto font-medium',
        emerald: 'bg-[#5aa9e6] text-white hover:bg-[#4396d4] shadow-xs active:scale-[0.98]',
        teal: 'bg-[#7fc8f8] text-slate-950 font-bold hover:bg-[#68b8ec] shadow-xs active:scale-[0.98]',
        amber: 'bg-[#ffe45e] text-slate-950 font-bold hover:bg-[#ebd048] shadow-xs active:scale-[0.98]',
        sky: 'bg-[#5aa9e6] text-white hover:bg-[#4396d4] shadow-xs active:scale-[0.98]',
        gold: 'bg-[#ffe45e] text-slate-950 font-bold hover:bg-[#ebd048] shadow-xs active:scale-[0.98]',
        rose: 'bg-[#ff6392] text-white hover:bg-[#e04f7b] shadow-xs active:scale-[0.98]',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs gap-1.5',
        md: 'h-9 px-4 py-2',
        lg: 'h-11 rounded-xl px-6 text-base gap-2.5',
        icon: 'h-9 w-9 p-0 shrink-0',
        'icon-sm': 'h-7 w-7 p-0 shrink-0 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, children, ...props }, ref) => {
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<any>, {
        className: cn(buttonVariants({ variant, size, className }), (children.props as any).className),
        ...props,
      });
    }

    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
