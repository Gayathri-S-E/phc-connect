import React from 'react';
import { 
  CheckCircle, AlertTriangle, AlertCircle, Clock, 
  Truck, Info, XCircle, ShieldCheck
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { Badge as UiBadge } from '../ui/badge';
import { cn } from '../../lib/utils';

export interface CommonBadgeProps {
  status: string;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

export const Badge: React.FC<CommonBadgeProps> = ({ status, label, size = 'md', className }) => {
  const { t } = useLanguage();
  const s = (status || '').toUpperCase();
  const fallbackLabel = label || status.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
  
  const statusKey = `status.${s.toLowerCase()}`;
  const translatedStatus = t(statusKey);
  const displayLabel = label || (translatedStatus !== statusKey ? translatedStatus : fallbackLabel);

  let variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info' | 'purple' = 'secondary';
  let icon = <Info className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;

  if (['COMPLETED', 'DISPENSED', 'RESOLVED', 'ACTIVE', 'APPROVED', 'RECEIVED', 'PRESENT', 'NORMAL'].includes(s)) {
    variant = 'success';
    icon = <CheckCircle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
  } else if (['SCHEDULED', 'PENDING', 'PENDING_REVIEW', 'PENDING_COLLECTION', 'PENDING_DISPENSING', 'ALLOCATED', 'SAMPLE_COLLECTED'].includes(s)) {
    variant = 'info';
    icon = <Clock className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
  } else if (['IN_TRANSIT', 'IN_CONSULTATION', 'IN_PROGRESS', 'CHECKED_IN', 'UNDER_INVESTIGATION'].includes(s)) {
    variant = 'purple';
    icon = <Truck className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
  } else if (['URGENT', 'HIGH', 'MAJOR', 'NEEDS_ATTENTION', 'LOW_STOCK', 'LATE', 'PRIORITY', 'SEMI_URGENT'].includes(s)) {
    variant = 'warning';
    icon = <AlertTriangle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
  } else if (['CRITICAL', 'EMERGENCY', 'IMMEDIATE', 'CANCELLED', 'REJECTED', 'EXPIRED', 'DISRUPTED', 'ABSENT', 'OUT_OF_RANGE', 'STOCKOUT'].includes(s)) {
    variant = 'destructive';
    icon = <AlertCircle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />;
  }

  return (
    <UiBadge
      variant={variant}
      className={cn(
        'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider',
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        className
      )}
    >
      {icon}
      <span>{displayLabel}</span>
    </UiBadge>
  );
};
