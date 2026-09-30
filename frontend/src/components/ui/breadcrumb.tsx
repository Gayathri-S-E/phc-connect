import React from 'react';
import { Slot } from 'radix-ui';
import { ChevronRight, Ellipsis } from 'lucide-react';
import { cn } from '@/lib/utils';

export const Breadcrumb = React.forwardRef<HTMLElement, React.ComponentPropsWithoutRef<'nav'>>(
  ({ 'aria-label': label = 'Breadcrumb', ...props }, ref) => <nav ref={ref} aria-label={label} {...props} />
);
Breadcrumb.displayName = 'Breadcrumb';

export const BreadcrumbList = React.forwardRef<HTMLOListElement, React.ComponentPropsWithoutRef<'ol'>>(
  ({ className, ...props }, ref) => (
    <ol ref={ref} className={cn('flex flex-wrap items-center gap-1.5 text-small text-muted-foreground', className)} {...props} />
  )
);
BreadcrumbList.displayName = 'BreadcrumbList';

export const BreadcrumbItem = React.forwardRef<HTMLLIElement, React.ComponentPropsWithoutRef<'li'>>(
  ({ className, ...props }, ref) => <li ref={ref} className={cn('inline-flex items-center gap-1.5', className)} {...props} />
);
BreadcrumbItem.displayName = 'BreadcrumbItem';

export const BreadcrumbLink = React.forwardRef<HTMLAnchorElement, React.ComponentPropsWithoutRef<'a'> & { asChild?: boolean }>(
  ({ asChild, className, ...props }, ref) => {
    const Comp = asChild ? Slot.Root : 'a';
    return <Comp ref={ref} className={cn('rounded-sm transition-colors hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring', className)} {...props} />;
  }
);
BreadcrumbLink.displayName = 'BreadcrumbLink';

export const BreadcrumbPage = React.forwardRef<HTMLSpanElement, React.ComponentPropsWithoutRef<'span'>>(
  ({ className, ...props }, ref) => (
    <span ref={ref} role="link" aria-disabled="true" aria-current="page" className={cn('font-medium text-foreground', className)} {...props} />
  )
);
BreadcrumbPage.displayName = 'BreadcrumbPage';

export const BreadcrumbSeparator = ({ children, className, ...props }: React.ComponentPropsWithoutRef<'li'>) => (
  <li role="presentation" aria-hidden="true" className={cn('[&>svg]:size-3.5', className)} {...props}>
    {children ?? <ChevronRight />}
  </li>
);

export const BreadcrumbEllipsis = ({ className, ...props }: React.ComponentPropsWithoutRef<'span'>) => (
  <span role="presentation" aria-hidden="true" className={cn('flex size-6 items-center justify-center', className)} {...props}>
    <Ellipsis className="size-4" />
    <span className="sr-only">More</span>
  </span>
);
