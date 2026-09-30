import React from 'react';
import { CheckCircle, AlertTriangle, AlertCircle } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { Badge } from '../../components/ui/badge';

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

  if (s === 'FRESH') {
    return (
      <Badge variant="success" className="gap-1 font-medium">
        <CheckCircle className="w-3 h-3 text-emerald-600" aria-hidden="true" />
        {t('capacity.status.fresh', 'Up to date')}
      </Badge>
    );
  } else if (s === 'STALE') {
    return (
      <Badge variant="warning" className="gap-1 font-medium">
        <AlertTriangle className="w-3 h-3 text-amber-600" aria-hidden="true" />
        {t('capacity.status.stale', 'Stale (over 24h)')}
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="gap-1 text-muted-foreground font-medium">
      <AlertCircle className="w-3 h-3 text-slate-400" aria-hidden="true" />
      {t('capacity.status.no_data', 'No data')}
    </Badge>
  );
};

/** Accessible horizontal occupancy bar with semantic threshold coloring. */
export const OccupancyBar: React.FC<{ occupied: number | null | undefined; total: number | null | undefined; label: string }> = ({
  occupied, total, label,
}) => {
  const { t } = useLanguage();
  if (!isNum(occupied) || !isNum(total)) {
    return <span className="text-xs text-muted-foreground">{t('capacity.not_reported', 'Not reported')}</span>;
  }
  const pct = total > 0 ? Math.min(100, Math.round((occupied / total) * 100)) : 0;
  const barColor = pct >= 90 ? 'bg-rose-500' : pct >= 75 ? 'bg-amber-500' : 'bg-emerald-500';
  const text = t('capacity.bar_text', '{occupied} of {total} beds occupied ({pct}%)', { occupied, total, pct });
  return (
    <div className="w-full">
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-valuetext={text}
        className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden"
      >
        <div 
          className={`h-full transition-all duration-300 ${barColor}`} 
          style={{ width: `${pct}%` }} 
        />
      </div>
      <div className="text-[11px] text-muted-foreground mt-1 flex justify-between font-medium">
        <span>{text}</span>
        <span className={pct >= 90 ? 'text-rose-600 font-bold' : pct >= 75 ? 'text-amber-600' : 'text-emerald-700'}>
          {pct}%
        </span>
      </div>
    </div>
  );
};
