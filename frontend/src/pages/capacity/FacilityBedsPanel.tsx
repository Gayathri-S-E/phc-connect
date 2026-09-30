import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Clock, Check } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import { FreshnessBadge, OccupancyBar, WARD_TYPES, wardFallback, wardLabelKey, formatDateTime, isNum } from './capacityShared';

interface Ward {
  id: string;
  facility_id: string;
  ward_type: string;
  total_beds: number;
  occupied_beds: number;
  available_beds: number;
  last_updated_by?: string | null;
  updated_at: string;
}

interface FacilityBeds {
  facility_id: string;
  as_of: string;
  status: string;
  last_updated_at?: string | null;
  total_beds: number | null;
  occupied_beds: number | null;
  available_beds: number | null;
  wards: Ward[];
}

interface CensusLog {
  id: string;
  ward_type: string;
  total_beds: number;
  occupied_beds: number;
  previous_total_beds?: number | null;
  previous_occupied_beds?: number | null;
  recorded_by?: string | null;
  note?: string | null;
  recorded_at: string;
}

interface Props {
  /** Defaults to the signed-in user's facility. */
  facilityId?: string;
}

const inputStyle: React.CSSProperties = { padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', width: '100%' };

interface WardFormProps {
  ward: Ward;
  facilityId: string;
  canManage: boolean;
  onSaved: () => void;
}

const WardForm: React.FC<WardFormProps> = ({ ward, facilityId, canManage, onSaved }) => {
  const { t } = useLanguage();
  const [occupied, setOccupied] = useState(String(ward.occupied_beds));
  const [total, setTotal] = useState(String(ward.total_beds));
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);

  // Keep inputs in sync after a refresh from the server
  useEffect(() => {
    setOccupied(String(ward.occupied_beds));
    setTotal(String(ward.total_beds));
  }, [ward.occupied_beds, ward.total_beds, ward.updated_at]);

  const name = t(wardLabelKey(ward.ward_type), wardFallback(ward.ward_type));
  const occNum = occupied.trim() === '' ? NaN : Number(occupied);
  const totNum = total.trim() === '' ? NaN : Number(total);
  const effectiveTotal = canManage ? totNum : ward.total_beds;

  let validation: string | null = null;
  if (!Number.isInteger(occNum) || occNum < 0) {
    validation = t('capacity.form.err_occupied', 'Enter a whole number of occupied beds, 0 or more.');
  } else if (canManage && (!Number.isInteger(totNum) || totNum < 0)) {
    validation = t('capacity.form.err_total', 'Enter a whole number of total beds, 0 or more.');
  } else if (occNum > effectiveTotal) {
    validation = t('capacity.form.err_exceeds', 'Occupied beds cannot exceed total beds ({total}).', { total: effectiveTotal });
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validation) return;
    setSaving(true);
    setResult(null);
    const body: { occupied_beds: number; total_beds?: number; note?: string } = { occupied_beds: occNum };
    if (canManage && totNum !== ward.total_beds) body.total_beds = totNum;
    if (note.trim()) body.note = note.trim();
    const res = await api.put<Ward>(`/capacity/facilities/${facilityId}/beds/${ward.ward_type}`, body);
    setSaving(false);
    if (res.data) {
      setResult({ ok: true, msg: t('capacity.form.saved', '{ward} updated: {occ} of {total} beds occupied.', {
        ward: name, occ: res.data.occupied_beds, total: res.data.total_beds,
      }) });
      setNote('');
      onSaved();
    } else {
      setResult({ ok: false, msg: res.error.detail || t('capacity.form.failed', 'Update failed.') });
    }
  };

  const idBase = `ward-${ward.ward_type}`;
  const errId = `${idBase}-err`;

  return (
    <form onSubmit={submit} className="glass-card" style={{ padding: '1.1rem', borderRadius: '14px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }} noValidate>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: '0.5rem', flexWrap: 'wrap' }}>
        <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>{name}</h4>
        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
          {t('capacity.wards.avail', '{n} available', { n: ward.available_beds })}
        </span>
      </div>
      <OccupancyBar occupied={ward.occupied_beds} total={ward.total_beds} label={name} />
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {t('capacity.last_updated', 'Last updated {time}', { time: formatDateTime(ward.updated_at) || t('capacity.not_reported', 'Not reported') })}
        {ward.last_updated_by ? ` · ${t('capacity.updated_by', 'by user {id}', { id: ward.last_updated_by.slice(0, 8) })}` : ''}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: canManage ? '1fr 1fr' : '1fr', gap: '0.75rem' }}>
        <div>
          <label htmlFor={`${idBase}-occ`} style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
            {t('capacity.form.occupied', 'Occupied beds')}
          </label>
          <input
            id={`${idBase}-occ`} type="number" inputMode="numeric" min={0} max={effectiveTotal} step={1}
            value={occupied} onChange={(e) => setOccupied(e.target.value)}
            aria-invalid={!!validation} aria-describedby={validation ? errId : undefined} style={inputStyle}
          />
        </div>
        {canManage && (
          <div>
            <label htmlFor={`${idBase}-tot`} style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
              {t('capacity.form.total', 'Total beds (capacity)')}
            </label>
            <input
              id={`${idBase}-tot`} type="number" inputMode="numeric" min={0} step={1}
              value={total} onChange={(e) => setTotal(e.target.value)} style={inputStyle}
            />
          </div>
        )}
      </div>
      <div>
        <label htmlFor={`${idBase}-note`} style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
          {t('capacity.form.note', 'Note (optional)')}
        </label>
        <input id={`${idBase}-note`} type="text" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} style={inputStyle} />
      </div>

      {validation && (
        <div id={errId} role="alert" style={{ fontSize: '0.8rem', color: '#dc2626' }}>{validation}</div>
      )}
      <button type="submit" className="btn-primary" disabled={saving || !!validation}
        style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center', justifyContent: 'center', padding: '0.6rem' }}>
        <Check size={16} aria-hidden="true" />
        {saving ? t('capacity.form.saving', 'Saving...') : t('capacity.form.save', 'Save occupancy')}
      </button>
      {result && (
        <div
          role={result.ok ? 'status' : 'alert'}
          style={{
            padding: '0.6rem 0.75rem', borderRadius: '8px', fontSize: '0.8rem',
            backgroundColor: result.ok ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.1)',
            color: result.ok ? '#047857' : '#b91c1c',
          }}
        >
          {result.msg}
        </div>
      )}
    </form>
  );
};

/**
 * Current beds per ward with occupancy update forms and census history for one facility.
 * Props: optional facilityId (defaults to user.facility_id). Route-agnostic.
 */
export default function FacilityBedsPanel({ facilityId }: Props) {
  const { t } = useLanguage();
  const { user, hasPermission } = useAuth();
  const fid = facilityId || user?.facility_id || '';
  const canUpdate = hasPermission('beds.occupancy.update');
  const canManage = hasPermission('beds.inventory.manage');

  const [beds, setBeds] = useState<FacilityBeds | null>(null);
  const [history, setHistory] = useState<CensusLog[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number; detail: string } | null>(null);

  const load = useCallback(async (silent = false) => {
    if (!fid) return;
    if (!silent) setLoading(true);
    setError(null);
    const [bedsRes, histRes] = await Promise.all([
      api.get<FacilityBeds>(`/capacity/facilities/${fid}/beds`),
      api.get<CensusLog[]>(`/capacity/facilities/${fid}/beds/history?limit=25`),
    ]);
    if (bedsRes.data) {
      setBeds(bedsRes.data);
    } else {
      setBeds(null);
      setError({ status: bedsRes.error.status, detail: bedsRes.error.detail });
    }
    if (histRes.data) {
      setHistory(histRes.data);
      setHistoryError(null);
    } else {
      setHistoryError(histRes.error.detail);
    }
    setLoading(false);
  }, [fid]);

  useEffect(() => {
    load();
  }, [load]);

  if (!fid) {
    return (
      <StateView
        state="empty"
        title={t('capacity.panel.no_facility', 'No facility assigned')}
        message={t('capacity.panel.no_facility_msg', 'Your account is not linked to a facility, so there are no beds to manage.')}
      />
    );
  }
  if (loading && !beds) return <StateView state="loading" message={t('capacity.panel.loading', 'Loading bed data...')} />;
  if (error) {
    return (
      <StateView
        state={error.status === 403 ? '403' : error.status === 0 ? 'offline' : 'error'}
        title={t('capacity.panel.error', 'Could not load bed data')}
        message={error.detail || undefined}
        onRetry={() => load()}
      />
    );
  }
  if (!beds) return null;

  const wardsSorted = [...beds.wards].sort(
    (a, b) => (WARD_TYPES as readonly string[]).indexOf(a.ward_type) - (WARD_TYPES as readonly string[]).indexOf(b.ward_type),
  );
  const notReported = t('capacity.not_reported', 'Not reported');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>{t('capacity.panel.title', 'Facility Beds')}</h2>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap', marginTop: '0.3rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <FreshnessBadge status={beds.status} />
            <span style={{ display: 'inline-flex', gap: '0.3rem', alignItems: 'center' }}>
              <Clock size={13} aria-hidden="true" />
              {t('capacity.last_updated', 'Last updated {time}', { time: formatDateTime(beds.last_updated_at) || t('capacity.never', 'Never reported') })}
            </span>
          </div>
        </div>
        <button className="btn-secondary" onClick={() => load()} disabled={loading}
          style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center', fontSize: '0.825rem', padding: '0.5rem 0.9rem' }}>
          <RefreshCw size={14} aria-hidden="true" /> {t('capacity.refresh', 'Refresh')}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem' }}>
        {[
          { k: 'total', label: t('capacity.kpi.total', 'Total beds reported'), v: beds.total_beds },
          { k: 'occ', label: t('capacity.kpi.occupied', 'Occupied beds'), v: beds.occupied_beds },
          { k: 'avail', label: t('capacity.kpi.available', 'Available beds'), v: beds.available_beds },
        ].map((x) => (
          <div key={x.k} className="glass-card" style={{ padding: '0.9rem 1rem', borderRadius: '12px' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>{x.label}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{isNum(x.v) ? x.v : notReported}</div>
          </div>
        ))}
      </div>

      {wardsSorted.length === 0 ? (
        <StateView
          state="empty"
          title={t('capacity.panel.no_wards', 'No wards registered')}
          message={t('capacity.panel.no_wards_msg', 'No bed data has been reported for this facility. A bed-inventory manager must register its wards.')}
        />
      ) : canUpdate ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {wardsSorted.map((w) => (
            <WardForm key={w.ward_type} ward={w} facilityId={fid} canManage={canManage} onSaved={() => load(true)} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {wardsSorted.map((w) => {
            const name = t(wardLabelKey(w.ward_type), wardFallback(w.ward_type));
            return (
              <div key={w.ward_type} className="glass-card" style={{ padding: '1rem', borderRadius: '14px' }}>
                <div style={{ fontWeight: 700, marginBottom: '0.4rem' }}>{name}</div>
                <OccupancyBar occupied={w.occupied_beds} total={w.total_beds} label={name} />
              </div>
            );
          })}
        </div>
      )}

      <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
        <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.05rem', fontWeight: 700 }}>
          {t('capacity.history.title', 'Recent updates')}
        </h3>
        {historyError ? (
          <StateView state="error" title={t('capacity.history.error', 'Could not load history')} message={historyError} onRetry={() => load(true)} />
        ) : history.length === 0 ? (
          <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            {t('capacity.history.empty', 'No updates recorded yet.')}
          </p>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {history.map((h) => (
              <li key={h.id} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <strong>{t(wardLabelKey(h.ward_type), wardFallback(h.ward_type))}</strong>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{formatDateTime(h.recorded_at) || notReported}</span>
                </div>
                <div>
                  {t('capacity.history.change', 'Occupied {prev} to {occ} of {total}', {
                    prev: isNum(h.previous_occupied_beds) ? h.previous_occupied_beds : '-',
                    occ: h.occupied_beds,
                    total: h.total_beds,
                  })}
                </div>
                {h.note && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{h.note}</div>}
                {h.recorded_by && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {t('capacity.updated_by', 'by user {id}', { id: h.recorded_by.slice(0, 8) })}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
