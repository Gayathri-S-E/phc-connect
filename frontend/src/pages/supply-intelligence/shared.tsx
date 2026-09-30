import React from 'react';
import { AlertOctagon, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { Badge } from '../../components/ui/badge';
import type { ApiError } from '../../services/types';

export const TIER_ORDER: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

export const cardStyle: React.CSSProperties = {
  background: 'var(--bg-card, #fff)',
  border: '1px solid var(--border-color, #e2e8f0)',
  borderRadius: 12,
  padding: '1rem',
};
export const mutedStyle: React.CSSProperties = { color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' };
export const advisoryStyle: React.CSSProperties = {
  border: '1px solid #d97706',
  background: 'rgba(245,158,11,0.12)',
  borderRadius: 10,
  padding: '0.75rem 1rem',
  fontSize: '0.9rem',
};

/** Tier badge: colour + icon + text (never colour alone). */
export const TierBadge: React.FC<{ tier: string }> = ({ tier }) => {
  const { t } = useLanguage();
  const upper = (tier || 'LOW').toUpperCase();

  if (upper === 'CRITICAL') {
    return (
      <Badge variant="destructive" className="gap-1 font-bold">
        <AlertOctagon className="w-3 h-3" aria-hidden="true" />
        {t(`supplyIntel.tier.${tier.toLowerCase()}`, tier)}
      </Badge>
    );
  }
  if (upper === 'HIGH') {
    return (
      <Badge variant="warning" className="gap-1 font-bold">
        <AlertTriangle className="w-3 h-3 text-amber-600" aria-hidden="true" />
        {t(`supplyIntel.tier.${tier.toLowerCase()}`, tier)}
      </Badge>
    );
  }
  if (upper === 'MEDIUM') {
    return (
      <Badge variant="info" className="gap-1 font-bold">
        <AlertCircle className="w-3 h-3 text-sky-600" aria-hidden="true" />
        {t(`supplyIntel.tier.${tier.toLowerCase()}`, tier)}
      </Badge>
    );
  }
  return (
    <Badge variant="success" className="gap-1 font-bold">
      <CheckCircle className="w-3 h-3 text-emerald-600" aria-hidden="true" />
      {t(`supplyIntel.tier.${tier.toLowerCase()}`, tier)}
    </Badge>
  );
};

export const stateViewTypeFor = (e: ApiError | null): 'error' | '403' | 'offline' =>
  e?.status === 403 ? '403' : e?.status === 0 ? 'offline' : 'error';

/** Renders an object as a compact key/value list. */
export const KeyValues: React.FC<{ data: Record<string, unknown> }> = ({ data }) => (
  <dl className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs m-0">
    {Object.entries(data).map(([k, v]) => (
      <div key={k} className="p-2 bg-muted/40 rounded border border-border">
        <dt className="text-[11px] font-semibold text-muted-foreground uppercase">{k.replace(/_/g, ' ')}</dt>
        <dd className="m-0 text-foreground font-medium mt-0.5 break-words">
          {v !== null && typeof v === 'object' ? <code className="font-mono text-[10px]">{JSON.stringify(v)}</code> : String(v ?? '—')}
        </dd>
      </div>
    ))}
  </dl>
);

export const fmtDate = (iso?: string | null, lang?: string) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString(lang || undefined);
};
