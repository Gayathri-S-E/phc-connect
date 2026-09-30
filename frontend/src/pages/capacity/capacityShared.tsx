import React from 'react';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export const WARD_TYPES = ['GENERAL', 'MATERNITY', 'PAEDIATRIC', 'ISOLATION', 'ICU'] as const;

export const wardLabelKey = (w: string) => `capacity.ward.${w.toLowerCase()}`;
export const wardFallback = (w: string) => w.charAt(0) + w.slice(1).toLowerCase();

export function formatDateTime(v?: string | null): string | null {
  if (!v) return null;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleString();
}

export const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);

/** Freshness badge: FRESH / STALE / NO_DATA. Colour is never the only signal (icon + text). */
export const FreshnessBadge: React.FC<{ status?: string | null }> = ({ status }) => {
  const { t } = useLanguage();
  const s = (status || 'NO_DATA').toUpperCase();
  let bg = 'rgba(100, 116, 139, 0.15)';
  let color = '#475569';
  let icon = <AlertCircle size={13} aria-hidden="true" />;
  let label = t('capacity.status.no_data', 'No data');
  if (s === 'FRESH') {
    bg = 'rgba(16, 185, 129, 0.15)';
    color = '#059669';
    icon = <CheckCircle size={13} aria-hidden="true" />;
    label = t('capacity.status.fresh', 'Up to date');
  } else if (s === 'STALE') {
    bg = 'rgba(245, 158, 11, 0.15)';
    color = '#b45309';
    icon = <AlertTriangle size={13} aria-hidden="true" />;
    label = t('capacity.status.stale', 'Stale (over 24h)');
  }
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.2rem 0.6rem',
        borderRadius: '9999px', fontSize: '0.775rem', fontWeight: 600, backgroundColor: bg, color, whiteSpace: 'nowrap',
      }}
    >
      {icon}
      {label}
    </span>
  );
};

/** Accessible horizontal occupancy bar. Renders "Not reported" when values are missing. */
export const OccupancyBar: React.FC<{ occupied: number | null | undefined; total: number | null | undefined; label: string }> = ({
  occupied, total, label,
}) => {
  const { t } = useLanguage();
  if (!isNum(occupied) || !isNum(total)) {
    return <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t('capacity.not_reported', 'Not reported')}</span>;
  }
  const pct = total > 0 ? Math.min(100, Math.round((occupied / total) * 100)) : 0;
  const color = pct >= 90 ? '#dc2626' : pct >= 75 ? '#d97706' : '#059669';
  const text = t('capacity.bar_text', '{occupied} of {total} beds occupied ({pct}%)', { occupied, total, pct });
  return (
    <div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-valuetext={text}
        style={{ height: '10px', borderRadius: '9999px', backgroundColor: 'rgba(100,116,139,0.2)', overflow: 'hidden' }}
      >
        <div style={{ width: `${pct}%`, height: '100%', backgroundColor: color }} />
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{text}</div>
    </div>
  );
};
