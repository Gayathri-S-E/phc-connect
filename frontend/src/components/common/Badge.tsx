import React from 'react';
import { 
  CheckCircle, AlertTriangle, AlertCircle, Clock, 
  Truck, Check, XCircle, Info 
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

interface BadgeProps {
  status: string;
  label?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ status, label, size = 'md' }) => {
  const { t } = useLanguage();
  const s = (status || '').toUpperCase();
  const fallbackLabel = label || status.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
  
  // Look up translated status
  const statusKey = `status.${s.toLowerCase()}`;
  const translatedStatus = t(statusKey);
  const displayLabel = label || (translatedStatus !== statusKey ? translatedStatus : fallbackLabel);

  let bg = 'rgba(100, 116, 139, 0.15)';
  let color = '#475569';
  let icon = <Info size={size === 'sm' ? 12 : 14} />;

  if (['COMPLETED', 'DISPENSED', 'RESOLVED', 'ACTIVE', 'APPROVED', 'RECEIVED', 'PRESENT'].includes(s)) {
    bg = 'rgba(16, 185, 129, 0.15)';
    color = '#059669';
    icon = <CheckCircle size={size === 'sm' ? 12 : 14} />;
  } else if (['SCHEDULED', 'PENDING', 'PENDING_REVIEW', 'PENDING_COLLECTION', 'PENDING_DISPENSING', 'ALLOCATED', 'SAMPLE_COLLECTED'].includes(s)) {
    bg = 'rgba(59, 130, 246, 0.15)';
    color = '#2563eb';
    icon = <Clock size={size === 'sm' ? 12 : 14} />;
  } else if (['IN_TRANSIT', 'IN_CONSULTATION', 'IN_PROGRESS', 'CHECKED_IN', 'UNDER_INVESTIGATION'].includes(s)) {
    bg = 'rgba(139, 92, 246, 0.15)';
    color = '#7c3aed';
    icon = <Truck size={size === 'sm' ? 12 : 14} />;
  } else if (['URGENT', 'HIGH', 'MAJOR', 'NEEDS_ATTENTION', 'LOW_STOCK', 'LATE', 'PRIORITY'].includes(s)) {
    bg = 'rgba(245, 158, 11, 0.15)';
    color = '#d97706';
    icon = <AlertTriangle size={size === 'sm' ? 12 : 14} />;
  } else if (['CRITICAL', 'EMERGENCY', 'CANCELLED', 'REJECTED', 'EXPIRED', 'DISRUPTED', 'ABSENT', 'OUT_OF_RANGE'].includes(s)) {
    bg = 'rgba(239, 68, 68, 0.15)';
    color = '#dc2626';
    icon = <AlertCircle size={size === 'sm' ? 12 : 14} />;
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: size === 'sm' ? '0.15rem 0.5rem' : '0.25rem 0.65rem',
        borderRadius: '9999px',
        fontSize: size === 'sm' ? '0.75rem' : '0.825rem',
        fontWeight: 600,
        backgroundColor: bg,
        color: color,
        textTransform: 'capitalize',
        whiteSpace: 'nowrap',
      }}
    >
      {icon}
      {displayLabel}
    </span>
  );
};
