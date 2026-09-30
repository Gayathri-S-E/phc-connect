import React from 'react';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogContent,
  DialogFooter,
  DialogClose,
} from '../ui/dialog';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  maxWidth = 'max-w-xl',
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()} maxWidth={maxWidth}>
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>{children}</DialogContent>
      {footer && <DialogFooter>{footer}</DialogFooter>}
    </Dialog>
  );
};
