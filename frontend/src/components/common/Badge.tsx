import React from 'react';
import { CircleAlert, CircleCheck, CircleDot, Clock, Info, Loader, TriangleAlert } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { StatusBadge, type StatusTone } from '../ui/status-badge';
import { cn } from '../../lib/utils';

export interface CommonBadgeProps {
  status: string;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
}

const SUCCESS = ['COMPLETED', 'DISPENSED', 'RESOLVED', 'ACTIVE', 'APPROVED', 'RECEIVED', 'PRESENT', 'NORMAL', 'EXECUTED'];
const PENDING = ['SCHEDULED', 'PENDING', 'PENDING_REVIEW', 'PENDING_COLLECTION', 'PENDING_DISPENSING', 'ALLOCATED', 'SAMPLE_COLLECTED'];
const IN_PROGRESS = ['IN_TRANSIT', 'IN_CONSULTATION', 'IN_PROGRESS', 'CHECKED_IN', 'UNDER_INVESTIGATION'];
const ATTENTION = ['URGENT', 'HIGH', 'MAJOR', 'NEEDS_ATTENTION', 'LOW_STOCK', 'LATE', 'PRIORITY', 'SEMI_URGENT'];
const CRITICAL = ['CRITICAL', 'EMERGENCY', 'IMMEDIATE', 'CANCELLED', 'REJECTED', 'EXPIRED', 'DISRUPTED', 'ABSENT', 'OUT_OF_RANGE', 'STOCKOUT', 'FAILED'];

/**
 * Status chip for record states (appointment, order, transfer, stock ...). Thin wrapper over the design-system
 * StatusBadge: always icon + label + colour. For new code you can use StatusBadge directly with an explicit tone.
 */
export const Badge: React.FC<CommonBadgeProps> = ({ status, label, size = 'md', className }) => {
  const { t } = useLanguage();
  const s = (status || '').toUpperCase();
  const fallbackLabel = (status || '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
  const statusKey = `status.${s.toLowerCase()}`;
  const translated = t(statusKey);
  const displayLabel = label || (translated !== statusKey ? translated : fallbackLabel);
  const iconClass = size === 'sm' ? 'size-3' : 'size-3.5';

  let tone: StatusTone = 'neutral';
  let icon: React.ReactNode = <CircleDot className={iconClass} aria-hidden="true" />;

  if (SUCCESS.includes(s)) {
    tone = 'success';
    icon = <CircleCheck className={iconClass} aria-hidden="true" />;
  } else if (PENDING.includes(s)) {
    tone = 'info';
    icon = <Clock className={iconClass} aria-hidden="true" />;
  } else if (IN_PROGRESS.includes(s)) {
    tone = 'info';
    icon = <Loader className={iconClass} aria-hidden="true" />;
  } else if (ATTENTION.includes(s)) {
    tone = 'warning';
    icon = <TriangleAlert className={iconClass} aria-hidden="true" />;
  } else if (CRITICAL.includes(s)) {
    tone = 'danger';
    icon = <CircleAlert className={iconClass} aria-hidden="true" />;
  } else {
    icon = <Info className={iconClass} aria-hidden="true" />;
  }

  return <StatusBadge status={tone} label={displayLabel} icon={icon} className={cn(size === 'sm' && 'px-1.5 text-caption', className)} />;
};
