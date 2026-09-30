import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { cardStyle, mutedStyle, TierBadge, KeyValues, stateViewTypeFor } from './shared';

interface Prior { medication_id: string; medication_name: string; round_no: number; n_states: number; n_samples: number; mean_daily_rate: number; variance: number }
interface FcItem {
  medication_id: string; medication_name: string; local_daily_rate: number; sparse_data: boolean;
  national_prior_weight: number; national_prior_rate: number | null;
  forecast_daily_rate: number; days_of_supply: number | null; risk_tier: string; confidence: number;
}

export interface FederatedModelPanelProps {
  /** Facility to forecast; defaults to the signed-in user's facility. */
  facilityId?: string;
  medicationId?: string;
  horizonDays?: number;
}

const unwrap = (d: any) => (d && d.data !== undefined ? d.data : d);
const cell: React.CSSProperties = { padding: '6px 8px', borderBottom: '1px solid var(--border-color, #e2e8f0)' };

const FederatedModelPanel: React.FC<FederatedModelPanelProps> = ({ facilityId, medicationId, horizonDays = 30 }) => {
  const { t } = useLanguage();
  const { user, scope } = useAuth();
  const canFederate = scope === 'STATE' || scope === 'GLOBAL';
  const canAggregate = scope === 'GLOBAL';
  const facility = facilityId || user?.facility_id || undefined;

  const [priors, setPriors] = useState<Prior[]>([]);
  const [items, setItems] = useState<FcItem[]>([]);
  const [error, setError] = useState<ApiError | null>(null);
  const [forecastError, setForecastError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [stateName, setStateName] = useState(user?.state || '');
  const [action, setAction] = useState<{ busy: boolean; result?: any; error?: string; which?: string }>({ busy: false });

  const load = useCallback(async () => {
    setLoading(true);
    const pq = new URLSearchParams(); if (medicationId) pq.set('medication_id', medicationId);
    const fq = new URLSearchParams({ horizon_days: String(horizonDays) });
    if (facility) fq.set('facility_id', facility);
    if (medicationId) fq.set('medication_id', medicationId);
    const [p, f] = await Promise.all([
      api.get<any>(`/analytics/federation/prior?${pq}`),
      api.get<any>(`/analytics/federation/forecast?${fq}`),
    ]);
    setLoading(false);
    if (p.error) { setError(p.error); return; }
    setError(null);
    setPriors(unwrap(p.data) || []);
    if (f.error) { setForecastError(f.error); setItems([]); }
    else { setForecastError(null); setItems(unwrap(f.data)?.items || []); }
  }, [facility, medicationId, horizonDays]);

  useEffect(() => { void load(); }, [load]);

  const run = async (which: 'local' | 'aggregate') => {
    setAction({ busy: true, which });
    const url = which === 'local'
      ? `/analytics/federation/local-update${stateName ? `?state=${encodeURIComponent(stateName)}` : ''}`
      : '/analytics/federation/aggregate';
    const res = await api.post<any>(url);
    if (res.error) { setAction({ busy: false, which, error: `${res.error.status}: ${res.error.detail}` }); return; }
    setAction({ busy: false, which, result: unwrap(res.data) });
    void load();
  };

  if (loading) return <StateView state="loading" message={t('supplyIntel.loading', 'Loading…')} />;
  if (error) {
    return <StateView state={stateViewTypeFor(error)} title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : t('supplyIntel.fed.title', 'Federated model')}
      message={error.detail} onRetry={() => void load()} />;
  }
  const priorFor = (id: string) => priors.find((p) => p.medication_id === id);
  const cols: [string, string][] = [
    ['medication', 'Medication'], ['nationalPrior', 'National prior'], ['localRate', 'Local rate'], ['priorWeight', 'Prior weight'],
    ['forecastRate', 'Blended forecast'], ['daysSupply', 'Days of supply'], ['risk', 'Risk'], ['confidence', 'Confidence'],
  ];

  return (
    <section aria-labelledby="fed-h" style={{ display: 'grid', gap: '1rem' }}>
      <header style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center' }}>
        <h2 id="fed-h" style={{ margin: 0 }}>{t('supplyIntel.fed.title', 'Federated demand model')}</h2>
        <button className="btn-secondary" onClick={() => void load()} style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
          <RefreshCw size={14} aria-hidden="true" /> {t('supplyIntel.refresh', 'Refresh')}
        </button>
      </header>

      <div role="note" style={{ ...cardStyle, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <ShieldCheck size={20} aria-hidden="true" style={{ flexShrink: 0 }} />
        <p style={{ margin: 0, fontSize: '0.9rem' }}>
          {t('supplyIntel.fed.privacy', 'Only aggregate parameters (average daily rate, variance, seasonality and sample counts) are shared between states and the national level. Patient records and individual transactions never leave their facility or state.')}
        </p>
      </div>

      <div>
        <h3>{t('supplyIntel.fed.priorVsForecast', 'National prior versus facility forecast')}</h3>
        {forecastError && (
          <div role="alert" style={{ ...cardStyle, borderColor: '#dc2626', marginBottom: 8 }}>
            {t('supplyIntel.fed.forecastError', 'Facility forecast unavailable')}: {forecastError.detail}
          </div>
        )}
        {items.length === 0 && !forecastError ? (
          <StateView state="empty" message={t('supplyIntel.fed.empty', 'No forecast items for this facility.')} />
        ) : items.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <caption style={{ ...mutedStyle, textAlign: 'left', paddingBottom: 6 }}>{t('supplyIntel.fed.caption', 'Rates are units per day.')}</caption>
              <thead>
                <tr>
                  {cols.map(([k, fb]) => (
                    <th key={k} scope="col" style={{ textAlign: 'left', padding: '6px 8px', borderBottom: '2px solid var(--border-color, #e2e8f0)' }}>
                      {t(`supplyIntel.fed.col.${k}`, fb)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((it) => {
                  const p = priorFor(it.medication_id);
                  return (
                    <tr key={it.medication_id}>
                      <th scope="row" style={{ ...cell, textAlign: 'left' }}>
                        {it.medication_name}
                        {it.sparse_data && <div style={mutedStyle}>{t('supplyIntel.fed.sparse', 'sparse local data')}</div>}
                      </th>
                      <td style={cell}>
                        {it.national_prior_rate ?? p?.mean_daily_rate ?? t('supplyIntel.fed.noPrior', 'no prior')}
                        {p && <div style={mutedStyle}>{t('supplyIntel.fed.round', 'round')} {p.round_no} · {p.n_states} {t('supplyIntel.fed.states', 'states')}</div>}
                      </td>
                      <td style={cell}>{it.local_daily_rate}</td>
                      <td style={cell}>{Math.round(it.national_prior_weight * 100)}%</td>
                      <td style={{ ...cell, fontWeight: 700 }}>{it.forecast_daily_rate}</td>
                      <td style={cell}>{it.days_of_supply ?? '—'}</td>
                      <td style={cell}><TierBadge tier={it.risk_tier} /></td>
                      <td style={cell}>{Math.round(it.confidence * 100)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {priors.length === 0 && (
          <p style={mutedStyle}>{t('supplyIntel.fed.noPriors', 'No national prior has been published yet; forecasts use local data only.')}</p>
        )}
      </div>

      {canFederate && (
        <div style={cardStyle}>
          <h3 style={{ marginTop: 0 }}>{t('supplyIntel.fed.admin', 'Federation actions')}</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'flex-end' }}>
            <label style={{ display: 'grid', gap: 4, fontSize: '0.85rem' }}>
              {t('supplyIntel.fed.stateLabel', 'State')}
              <input value={stateName} onChange={(e) => setStateName(e.target.value)}
                placeholder={canAggregate ? t('supplyIntel.fed.stateRequired', 'Required for national users') : ''}
                style={{ padding: '0.4rem 0.6rem', borderRadius: 8, border: '1px solid var(--border-color, #cbd5e1)' }} />
            </label>
            <button className="btn-primary" disabled={action.busy || (canAggregate && !stateName)} onClick={() => void run('local')}>
              {action.busy && action.which === 'local' ? t('supplyIntel.running', 'Running…') : t('supplyIntel.fed.runLocal', 'Compute state update')}
            </button>
            {canAggregate && (
              <button className="btn-secondary" disabled={action.busy} onClick={() => void run('aggregate')}>
                {action.busy && action.which === 'aggregate' ? t('supplyIntel.running', 'Running…') : t('supplyIntel.fed.runAggregate', 'Aggregate national prior')}
              </button>
            )}
          </div>
          <div aria-live="polite" style={{ marginTop: '0.75rem' }}>
            {action.error && <div role="alert" style={{ color: '#b91c1c' }}>{action.error}</div>}
            {action.result && (
              <div>
                <strong>{t('supplyIntel.fed.response', 'Server response')}</strong>
                <pre style={{ overflowX: 'auto', background: 'rgba(100,116,139,0.1)', padding: '0.6rem', borderRadius: 8, fontSize: '0.8rem' }}>
                  {JSON.stringify(action.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
          <details style={{ marginTop: 8 }}>
            <summary style={{ cursor: 'pointer' }}>{t('supplyIntel.fed.priorsDetail', 'Published national priors')}</summary>
            {priors.map((p) => (
              <div key={p.medication_id} style={{ marginTop: 6 }}>
                <strong>{p.medication_name}</strong>
                <KeyValues data={{ round: p.round_no, states: p.n_states, samples: p.n_samples, mean_daily_rate: p.mean_daily_rate, variance: p.variance }} />
              </div>
            ))}
          </details>
        </div>
      )}
    </section>
  );
};

export default FederatedModelPanel;
