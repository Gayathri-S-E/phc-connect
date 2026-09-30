import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { CircleAlert, CircleCheck, Info, Sparkles, TriangleAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

export const alertVariants = cva(
  'relative flex w-full items-start gap-3 rounded-lg border p-4 text-small [&>svg]:mt-0.5 [&>svg]:size-4 [&>svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'border-border bg-card text-foreground',
        info: 'border-info-border bg-info-soft text-info-text',
        warning: 'border-warning-border bg-warning-soft text-warning-text',
        destructive: 'border-danger-border bg-danger-soft text-danger-text',
        success: 'border-success-border bg-success-soft text-success-text',
        ai: 'border-ai-border bg-ai-soft text-ai-text',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

const icons = {
  info: Info,
  warning: TriangleAlert,
  destructive: CircleAlert,
  success: CircleCheck,
  ai: Sparkles,
} as const;

export const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, children, ...props }, ref) => {
  const Icon = variant && variant !== 'default' ? icons[variant] : null;
  return (
    <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props}>
      {Icon ? <Icon aria-hidden="true" /> : null}
      <div className="flex-1 space-y-0.5">{children}</div>
    </div>
  );
});
Alert.displayName = 'Alert';

export const AlertTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn('font-semibold leading-snug text-foreground', className)} {...props} />
  )
);
AlertTitle.displayName = 'AlertTitle';

export const AlertDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('text-small leading-relaxed text-foreground/85 [&_p]:leading-relaxed', className)} {...props} />
  )
);
AlertDescription.displayName = 'AlertDescription';
