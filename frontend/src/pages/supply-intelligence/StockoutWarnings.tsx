import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, Sparkles, ChevronDown, ChevronRight } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { TierBadge, TIER_ORDER, cardStyle, mutedStyle, advisoryStyle, KeyValues, stateViewTypeFor, fmtDate } from './shared';

interface SurgeItem {
  facility_id: string; facility_name: string; state?: string; district?: string;
  medication_id: string; medication_name: string;
  days_of_supply_baseline: number | null; days_of_supply_surge: number | null;
  risk_tier: string; baseline_risk_tier: string; escalated_by_emergency: boolean;
  predicted_stockout_date: string | null; confidence: number;
  evidence: Record<string, any>; explanation: string;
}
interface SurgeResponse {
  generated_at: string; count: number; items: SurgeItem[];
  methodology?: Record<string, any>; advisory_notice?: string;
  explanation?: string; ai_explanation?: string | null; ai_explanation_reason?: string | null;
}

export interface StockoutWarningsProps {
  facilityId?: string;
  medicationId?: string;
  horizonDays?: number;
  minTier?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

const StockoutWarnings: React.FC<StockoutWarningsProps> = ({ facilityId, medicationId, horizonDays = 30, minTier = 'MEDIUM' }) => {
  const { t, language } = useLanguage();
  const [data, setData] = useState<SurgeResponse | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  const load = useCallback(async (explain: boolean) => {
    const q = new URLSearchParams({ horizon_days: String(horizonDays), min_tier: minTier });
    if (facilityId) q.set('facility_id', facilityId);
    if (medicationId) q.set('medication_id', medicationId);
    if (explain) { q.set('explain', 'true'); q.set('lang', language); }
    if (explain) setExplaining(true); else setLoading(true);
    setExplainError(null);
    const res = await api.get<any>(`/analytics/surge-risk?${q}`);
    if (explain) setExplaining(false); else setLoading(false);
    if (res.error) {
      if (explain) setExplainError(res.error.detail); else { setError(res.error); setData(null); }
      return;
    }
    const body: any = res.data;
    setError(null);
    setData((body && body.data) || body);
  }, [facilityId, medicationId, horizonDays, minTier, language]);

  useEffect(() => { void load(false); }, [load]);

  const items = useMemo(
    () => [...(data?.items || [])].sort((a, b) =>
      (TIER_ORDER[a.risk_tier] ?? 9) - (TIER_ORDER[b.risk_tier] ?? 9) ||
      (a.days_of_supply_surge ?? -1) - (b.days_of_supply_surge ?? -1)),
    [data]);

  const title = t('supplyIntel.stockout.title', 'Emergency-surge stock-out warnings');

  if (loading) return <StateView state="loading" message={t('supplyIntel.loading', 'Loading…')} />;
  if (error) {
    return (
      <StateView
        state={stateViewTypeFor(error)}
        title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : title}
        message={error.detail}
        onRetry={() => void load(false)}
      />
    );
  }

  const explainRequested = !!data?.ai_explanation || (!!data?.ai_explanation_reason && data.ai_explanation_reason !== 'NOT_REQUESTED');

  return (
    <section aria-labelledby="stockout-h" style={{ display: 'grid', gap: '1rem' }}>
      <header style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 id="stockout-h" style={{ margin: 0 }}>{title}</h2>
          <p style={{ ...mutedStyle, margin: 0 }}>
            {t('supplyIntel.generatedAt', 'Generated')}: {fmtDate(data?.generated_at, language)} · {items.length} {t('supplyIntel.warnings', 'warnings')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="btn-secondary" onClick={() => void load(false)} style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
            <RefreshCw size={14} aria-hidden="true" /> {t('supplyIntel.refresh', 'Refresh')}
          </button>
          <button className="btn-primary" onClick={() => void load(true)} disabled={explaining || items.length === 0}
            aria-busy={explaining} style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
            <Sparkles size={14} aria-hidden="true" />
            {explaining ? t('supplyIntel.explaining', 'Explaining…') : t('supplyIntel.explainAi', 'Explain with AI')}
          </button>
        </div>
      </header>

      <div role="note" style={advisoryStyle}>
        <strong>{t('supplyIntel.advisory', 'ADVISORY')}</strong>{' '}
        {data?.advisory_notice || t('supplyIntel.advisoryText', 'Advisory only. Nothing is ordered or transferred automatically.')}
      </div>

      <div aria-live="polite">
        {explainError && (
          <div role="alert" style={{ ...cardStyle, borderColor: '#dc2626' }}>
            {t('supplyIntel.aiUnavailable', 'AI explanation unavailable')}: {explainError}
          </div>
        )}
        {!explainError && data && explainRequested && (
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 0.4rem', fontSize: '1rem' }}>
              <Sparkles size={14} aria-hidden="true" /> {t('supplyIntel.aiExplanation', 'AI explanation')}
            </h3>
            {data.ai_explanation ? (
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{data.ai_explanation}</p>
            ) : (
              <p style={{ margin: 0 }}>
                {t('supplyIntel.aiUnavailable', 'AI explanation unavailable')}: {data.ai_explanation_reason || t('supplyIntel.unknownReason', 'unknown reason')}
              </p>
            )}
            {data.explanation && <p style={{ ...mutedStyle, marginBottom: 0 }}>{t('supplyIntel.deterministic', 'Rule-based summary')}: {data.explanation}</p>}
          </div>
        )}
      </div>

      {items.length === 0 ? (
        <StateView state="empty" message={t('supplyIntel.stockout.empty', 'No stock-out risks at or above the selected tier in your scope.')} />
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.75rem' }}>
          {items.map((it) => {
            const key = `${it.facility_id}:${it.medication_id}`;
            const isOpen = !!open[key];
            return (
              <li key={key} style={cardStyle}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 1rem', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ minWidth: 0 }}>
                    <strong>{it.medication_name}</strong>
                    <div style={mutedStyle}>{it.facility_name}{it.district ? ` · ${it.district}` : ''}{it.state ? `, ${it.state}` : ''}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                    <TierBadge tier={it.risk_tier} />
                    {it.escalated_by_emergency && (
                      <span style={{ ...mutedStyle, fontWeight: 600 }}>
                        {t('supplyIntel.escalated', 'raised by emergency')} ({t('supplyIntel.was', 'was')} {it.baseline_risk_tier})
                      </span>
                    )}
                  </div>
                </div>
                <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', margin: '0.75rem 0' }}>
                  <div><dt style={mutedStyle}>{t('supplyIntel.daysSurge', 'Days of supply (surge)')}</dt><dd style={{ margin: 0, fontWeight: 700 }}>{it.days_of_supply_surge ?? '—'}</dd></div>
                  <div><dt style={mutedStyle}>{t('supplyIntel.daysBase', 'Days of supply (baseline)')}</dt><dd style={{ margin: 0 }}>{it.days_of_supply_baseline ?? '—'}</dd></div>
                  <div><dt style={mutedStyle}>{t('supplyIntel.stockoutDate', 'Predicted stock-out')}</dt><dd style={{ margin: 0 }}>{fmtDate(it.predicted_stockout_date, language)}</dd></div>
                  <div><dt style={mutedStyle}>{t('supplyIntel.multiplier', 'Surge multiplier')}</dt><dd style={{ margin: 0 }}>×{it.evidence?.surge_multiplier ?? 1}</dd></div>
                  <div><dt style={mutedStyle}>{t('supplyIntel.confidence', 'Confidence')}</dt><dd style={{ margin: 0 }}>{Math.round((it.confidence || 0) * 100)}%</dd></div>
                </dl>
                <p style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>{it.explanation}</p>
                <button
                  className="btn-reset"
                  aria-expanded={isOpen}
                  aria-controls={`ev-${key}`}
                  onClick={() => setOpen((o) => ({ ...o, [key]: !o[key] }))}
                  style={{ display: 'inline-flex', gap: 4, alignItems: 'center', cursor: 'pointer', color: 'var(--primary, #2563eb)', fontWeight: 600 }}
                >
                  {isOpen ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
                  {t('supplyIntel.evidence', 'Evidence and formula')}
                </button>
                {isOpen && (
                  <div id={`ev-${key}`} style={{ marginTop: '0.5rem', display: 'grid', gap: '0.5rem' }}>
                    {it.evidence?.incident?.formula && (
                      <p style={{ margin: 0 }}><strong>{t('supplyIntel.formula', 'Multiplier formula')}:</strong> <code>{it.evidence.incident.formula}</code></p>
                    )}
                    <KeyValues data={it.evidence || {}} />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {data?.methodology && (
        <details style={cardStyle}>
          <summary style={{ cursor: 'pointer', fontWeight: 600 }}>{t('supplyIntel.methodology', 'Methodology and multiplier configuration')}</summary>
          <div style={{ marginTop: '0.5rem' }}><KeyValues data={data.methodology} /></div>
        </details>
      )}
    </section>
  );
};

export default StockoutWarnings;
