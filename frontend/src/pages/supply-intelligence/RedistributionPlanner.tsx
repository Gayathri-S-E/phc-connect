import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, ArrowRight, ChevronDown, ChevronRight } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { TierBadge, cardStyle, mutedStyle, advisoryStyle, KeyValues, stateViewTypeFor } from './shared';

interface Rec {
  medication_id: string; medication_name: string;
  source_facility_id: string; source_facility_name: string; source_district?: string; source_state?: string;
  destination_facility_id: string; destination_facility_name: string; destination_district?: string; destination_state?: string;
  recommended_quantity: number; level?: string; distance_km: number | null; distance_basis?: string;
  urgency: string; evidence: Record<string, any>; rationale: string; next_step?: string;
}
interface Unmet { medication_id: string; medication_name: string; facility_id: string; facility_name: string; unmet_quantity: number; urgency: string; suggestion: string }
interface Resp { count: number; recommendations: Rec[]; unmet_needs: Unmet[]; advisory_notice?: string; methodology?: Record<string, any> }

export interface RedistributionPlannerProps {
  medicationId?: string;
  maxDistanceKm?: number;
  crossDistrictOnly?: boolean;
  /** Route of the Supply module where a transfer request is raised (the backend has no endpoint that creates one from a suggestion). */
  supplyModulePath?: string;
}

const RedistributionPlanner: React.FC<RedistributionPlannerProps> = ({ medicationId, maxDistanceKm, crossDistrictOnly = false, supplyModulePath }) => {
  const { t } = useLanguage();
  const [data, setData] = useState<Resp | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState<Record<number, boolean>>({});

  const load = useCallback(async () => {
    setLoading(true);
    const q = new URLSearchParams();
    if (medicationId) q.set('medication_id', medicationId);
    if (maxDistanceKm) q.set('max_distance_km', String(maxDistanceKm));
    if (crossDistrictOnly) q.set('cross_district_only', 'true');
    const res = await api.get<any>(`/analytics/redistribution?${q}`);
    setLoading(false);
    if (res.error) { setError(res.error); setData(null); return; }
    setError(null);
    setData((res.data && res.data.data) || res.data);
  }, [medicationId, maxDistanceKm, crossDistrictOnly]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <StateView state="loading" message={t('supplyIntel.loading', 'Loading…')} />;
  if (error) {
    return <StateView state={stateViewTypeFor(error)} title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : t('supplyIntel.redis.title', 'Cross-district redistribution')}
      message={error.detail} onRetry={() => void load()} />;
  }
  const recs = data?.recommendations || [];
  const unmet = data?.unmet_needs || [];

  return (
    <section aria-labelledby="redis-h" style={{ display: 'grid', gap: '1rem' }}>
      <header style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'center' }}>
        <h2 id="redis-h" style={{ margin: 0 }}>{t('supplyIntel.redis.title', 'Cross-district redistribution suggestions')}</h2>
        <button className="btn-secondary" onClick={() => void load()} style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
          <RefreshCw size={14} aria-hidden="true" /> {t('supplyIntel.refresh', 'Refresh')}
        </button>
      </header>

      <div role="note" style={advisoryStyle}>
        <strong>{t('supplyIntel.advisoryApproval', 'ADVISORY - needs human approval.')}</strong>{' '}
        {data?.advisory_notice || t('supplyIntel.advisoryText', 'Nothing is transferred or ordered automatically.')}{' '}
        {t('supplyIntel.raiseViaSupply', 'To act on a suggestion, raise a transfer request via the Supply module.')}
        {supplyModulePath && <> <a href={supplyModulePath}>{t('supplyIntel.openSupply', 'Open Supply module')}</a></>}
      </div>

      {recs.length === 0 ? (
        <StateView state="empty" message={t('supplyIntel.redis.empty', 'No redistribution suggestions for your scope right now.')} />
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.75rem' }}>
          {recs.map((r, i) => (
            <li key={`${r.source_facility_id}-${r.destination_facility_id}-${r.medication_id}-${i}`} style={cardStyle}>
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: 8 }}>
                <strong>{r.medication_name}</strong>
                <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ ...mutedStyle, fontWeight: 700, border: '1px dashed #d97706', borderRadius: 6, padding: '1px 6px' }}>
                    {t('supplyIntel.advisoryTag', 'ADVISORY')} · {t('supplyIntel.needsApproval', 'needs approval')}
                  </span>
                  <TierBadge tier={r.urgency} />
                </span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', margin: '0.6rem 0' }}>
                <span><span style={mutedStyle}>{t('supplyIntel.from', 'From')}</span><br />{r.source_facility_name}<br /><span style={mutedStyle}>{r.source_district}{r.source_state ? `, ${r.source_state}` : ''}</span></span>
                <ArrowRight size={18} aria-label={t('supplyIntel.toLower', 'to')} />
                <span><span style={mutedStyle}>{t('supplyIntel.to', 'To')}</span><br />{r.destination_facility_name}<br /><span style={mutedStyle}>{r.destination_district}{r.destination_state ? `, ${r.destination_state}` : ''}</span></span>
              </div>
              <dl style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', margin: 0 }}>
                <div><dt style={mutedStyle}>{t('supplyIntel.quantity', 'Suggested quantity')}</dt><dd style={{ margin: 0, fontWeight: 700 }}>{r.recommended_quantity}</dd></div>
                <div><dt style={mutedStyle}>{t('supplyIntel.distance', 'Distance')}</dt><dd style={{ margin: 0 }}>{r.distance_km != null ? `${r.distance_km} km` : t('supplyIntel.distanceUnknown', 'unknown')}</dd></div>
                {r.level && <div><dt style={mutedStyle}>{t('supplyIntel.level', 'Level')}</dt><dd style={{ margin: 0 }}>{r.level.replace(/_/g, ' ')}</dd></div>}
              </dl>
              <p style={{ margin: '0.6rem 0 0.3rem', fontSize: '0.9rem' }}>{r.rationale}</p>
              {r.next_step && <p style={{ ...mutedStyle, margin: '0 0 0.3rem' }}>{r.next_step}</p>}
              <button className="btn-reset" aria-expanded={!!open[i]} onClick={() => setOpen((o) => ({ ...o, [i]: !o[i] }))}
                style={{ display: 'inline-flex', gap: 4, alignItems: 'center', cursor: 'pointer', color: 'var(--primary, #2563eb)', fontWeight: 600 }}>
                {open[i] ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
                {t('supplyIntel.evidence', 'Evidence')}
              </button>
              {open[i] && (
                <div style={{ marginTop: 6 }}>
                  {r.distance_basis && <p style={mutedStyle}>{r.distance_basis}</p>}
                  <KeyValues data={r.evidence || {}} />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {unmet.length > 0 && (
        <div style={cardStyle}>
          <h3 style={{ marginTop: 0 }}>{t('supplyIntel.unmet', 'Unmet needs (no eligible donor)')}</h3>
          <ul style={{ margin: 0, paddingLeft: '1.1rem', display: 'grid', gap: 6 }}>
            {unmet.map((u, i) => (
              <li key={`${u.facility_id}-${u.medication_id}-${i}`}>
                <TierBadge tier={u.urgency} />{' '}
                <strong>{u.medication_name}</strong> @ {u.facility_name}: {u.unmet_quantity} {t('supplyIntel.units', 'units')} - <span style={mutedStyle}>{u.suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data?.methodology && (
        <details style={cardStyle}>
          <summary style={{ cursor: 'pointer', fontWeight: 600 }}>{t('supplyIntel.methodology', 'Methodology')}</summary>
          <div style={{ marginTop: 6 }}><KeyValues data={data.methodology} /></div>
        </details>
      )}
    </section>
  );
};

export default RedistributionPlanner;
