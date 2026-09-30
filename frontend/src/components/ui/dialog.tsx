import React from 'react';
import { Dialog as DialogPrimitive } from 'radix-ui';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

/**
 * Radix Dialog (focus trap, Escape, scroll lock, aria-modal) with the legacy Med2Us composition API:
 *   <Dialog open onOpenChange maxWidth> <DialogHeader><DialogTitle/><DialogDescription/></DialogHeader>
 *   <DialogContent>body</DialogContent> <DialogFooter/> </Dialog>
 * Always render a <DialogTitle> inside (Radix uses it as the accessible name).
 */
interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
  maxWidth?: string;
}

export function Dialog({ open, onOpenChange, children, className, maxWidth = 'max-w-lg' }: DialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-overlay data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className={cn(
            'fixed left-1/2 top-1/2 z-50 flex max-h-[90vh] w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
            maxWidth,
            className
          )}
        >
          {children}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}

export const DialogTrigger = DialogPrimitive.Trigger;

export const DialogHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center justify-between border-b border-border bg-muted/60 px-6 py-4', className)} {...props}>
    <div className="space-y-1">{children}</div>
  </div>
);

export const DialogTitle = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title ref={ref} className={cn('text-section-title text-foreground', className)} {...props} />
));
DialogTitle.displayName = 'DialogTitle';

export const DialogDescription = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description ref={ref} className={cn('text-small text-muted-foreground', className)} {...props} />
));
DialogDescription.displayName = 'DialogDescription';

/** Scrollable body of the dialog. */
export const DialogContent = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex-1 space-y-4 overflow-y-auto p-6', className)} {...props}>
    {children}
  </div>
);

export const DialogFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center justify-end gap-2 border-t border-border bg-muted/60 px-6 py-3.5', className)} {...props}>
    {children}
  </div>
);

export const DialogClose = ({ onClose, className }: { onClose: () => void; className?: string }) => (
  <Button
    type="button"
    variant="ghost"
    size="icon-sm"
    onClick={onClose}
    aria-label="Close dialog"
    className={cn('text-muted-foreground hover:text-foreground', className)}
  >
    <X className="size-4" />
  </Button>
);
