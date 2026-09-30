import React from 'react';
import { AlertOctagon, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
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

const TIER_STYLE: Record<string, { bg: string; fg: string; Icon: React.ElementType }> = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', fg: '#b91c1c', Icon: AlertOctagon },
  HIGH: { bg: 'rgba(245,158,11,0.18)', fg: '#b45309', Icon: AlertTriangle },
  MEDIUM: { bg: 'rgba(59,130,246,0.15)', fg: '#1d4ed8', Icon: AlertCircle },
  LOW: { bg: 'rgba(16,185,129,0.15)', fg: '#047857', Icon: CheckCircle },
};

/** Tier badge: colour + icon + text (never colour alone). */
export const TierBadge: React.FC<{ tier: string }> = ({ tier }) => {
  const { t } = useLanguage();
  const s = TIER_STYLE[tier] || TIER_STYLE.LOW;
  const Icon = s.Icon;
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 10px', borderRadius: 999,
        background: s.bg, color: s.fg, fontWeight: 700, fontSize: '0.78rem', whiteSpace: 'nowrap',
      }}
    >
      <Icon size={13} aria-hidden="true" />
      {t(`supplyIntel.tier.${tier.toLowerCase()}`, tier)}
    </span>
  );
};

export const stateViewTypeFor = (e: ApiError | null): 'error' | '403' | 'offline' =>
  e?.status === 403 ? '403' : e?.status === 0 ? 'offline' : 'error';

/** Renders an object as a compact key/value list. */
export const KeyValues: React.FC<{ data: Record<string, unknown> }> = ({ data }) => (
  <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '0.4rem 1rem', margin: 0, fontSize: '0.85rem' }}>
    {Object.entries(data).map(([k, v]) => (
      <div key={k} style={{ wordBreak: 'break-word' }}>
        <dt style={{ ...mutedStyle, fontSize: '0.75rem' }}>{k.replace(/_/g, ' ')}</dt>
        <dd style={{ margin: 0 }}>
          {v !== null && typeof v === 'object' ? <code>{JSON.stringify(v)}</code> : String(v ?? '—')}
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
