import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BedDouble, Users, RefreshCw, Clock } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import { FreshnessBadge, OccupancyBar, WARD_TYPES, wardFallback, wardLabelKey, formatDateTime, isNum } from './capacityShared';

type Level = 'national' | 'state' | 'district';

interface FlaggedFacility {
  facility_id: string;
  facility_name: string;
  state?: string | null;
  district?: string | null;
  beds_status: string;
  beds_last_updated_at?: string | null;
  attendance_status: string;
  last_attendance_at?: string | null;
}

interface Rollup {
  scope?: string;
  as_of: string;
  stale_after_hours?: number;
  facilities: number;
  beds: {
    total: number; occupied: number; available: number; occupancy_pct: number | null;
    fresh_total: number; fresh_occupied: number; fresh_available: number;
    by_ward: Record<string, { total: number; occupied: number; available: number }>;
    facilities_fresh: number; facilities_stale: number; facilities_no_data: number;
  };
  staff: {
    assigned_total: number; assigned_in_reporting_facilities: number; present_today: number;
    availability_pct: number | null;
    facilities_attendance_fresh: number; facilities_attendance_stale: number; facilities_attendance_no_data: number;
  };
  flagged_facilities_count: number;
  flagged_facilities: FlaggedFacility[];
  flagged_truncated: boolean;
}

const card: React.CSSProperties = { padding: '1.25rem', borderRadius: '14px' };
const inputStyle: React.CSSProperties = { padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-color)', minWidth: '10rem' };

const Kpi: React.FC<{ label: string; value: string; hint?: string; icon: React.ReactNode }> = ({ label, value, hint, icon }) => (
  <div className="glass-card" style={{ ...card, display: 'flex', gap: '0.85rem', alignItems: 'flex-start' }}>
    <div style={{ color: 'var(--primary)' }} aria-hidden="true">{icon}</div>
    <div style={{ minWidth: 0 }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 800, lineHeight: 1.2 }}>{value}</div>
      {hint && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{hint}</div>}
    </div>
  </div>
);

/**
 * Bed availability and staff attendance roll-up. Route-agnostic, takes no props.
 * Picks the widest roll-up the user's permissions suggest and falls back to narrower ones on 403.
 */
export default function CapacityDashboard() {
  const { t } = useLanguage();
  const { user, hasPermission } = useAuth();

  const candidates = useMemo<Level[]>(() => {
    const list: Level[] = [];
    if (hasPermission('governance.national.view')) list.push('national');
    if (hasPermission('governance.state.view')) list.push('state');
    if (hasPermission('governance.district.view')) list.push('district');
    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const [stateFilter, setStateFilter] = useState(user?.state || '');
  const [districtFilter, setDistrictFilter] = useState(user?.district || '');
  const [level, setLevel] = useState<Level | null>(null);
  const [data, setData] = useState<Rollup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number; detail: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    if (candidates.length === 0) {
      setData(null);
      setError({ status: 403, detail: '' });
      setLoading(false);
      return;
    }
    let last: { status: number; detail: string } | null = null;
    for (const lv of candidates) {
      const qs = new URLSearchParams();
      if (lv !== 'national' && stateFilter.trim()) qs.set('state', stateFilter.trim());
      if (lv === 'district' && districtFilter.trim()) qs.set('district', districtFilter.trim());
      const q = qs.toString();
      const res = await api.get<Rollup>(`/capacity/${lv}${q ? `?${q}` : ''}`);
      if (res.data) {
        setData(res.data);
        setLevel(lv);
        setLoading(false);
        return;
      }
      last = { status: res.error.status, detail: res.error.detail };
      if (res.error.status !== 403) break; // only fall back to a narrower level on 403
    }
    setData(null);
    setLevel(null);
    setError(last);
    setLoading(false);
  }, [candidates, stateFilter, districtFilter]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const levelLabel = (lv: Level) =>
    lv === 'national' ? t('capacity.level.national', 'National')
      : lv === 'state' ? t('capacity.level.state', 'State') : t('capacity.level.district', 'District');

  const notReported = t('capacity.not_reported', 'Not reported');
  const num = (v: number | null | undefined) => (isNum(v) ? v.toLocaleString() : notReported);
  const pct = (v: number | null | undefined) => (isNum(v) ? `${v}%` : notReported);

  if (loading && !data) {
    return <StateView state="loading" message={t('capacity.loading', 'Loading capacity data...')} />;
  }

  // State/district filters are needed only when the widest available level requires a jurisdiction choice
  const needsFilters = candidates.length > 0 && candidates[0] !== 'national';
  const filters = needsFilters ? (
    <form
      onSubmit={(e) => { e.preventDefault(); load(); }}
      style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}
    >
      <div>
        <label htmlFor="cap-state" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
          {t('capacity.filter.state', 'State')}
        </label>
        <input id="cap-state" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)} style={inputStyle} />
      </div>
      {candidates[0] === 'district' && (
        <div>
          <label htmlFor="cap-district" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
            {t('capacity.filter.district', 'District')}
          </label>
          <input id="cap-district" value={districtFilter} onChange={(e) => setDistrictFilter(e.target.value)} style={inputStyle} />
        </div>
      )}
      <button type="submit" className="btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.825rem' }}>
        {t('capacity.filter.apply', 'Apply')}
      </button>
    </form>
  ) : null;

  if (error) {
    if (error.status === 403) {
      return (
        <StateView
          state="403"
          title={t('capacity.forbidden.title', 'Capacity view not available')}
          message={t('capacity.forbidden.message', 'Your role does not have access to district, state or national capacity roll-ups.')}
        />
      );
    }
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {filters}
        <StateView
          state={error.status === 0 ? 'offline' : 'error'}
          title={t('capacity.error.title', 'Could not load capacity data')}
          message={error.detail || undefined}
          onRetry={load}
        />
      </div>
    );
  }

  if (!data || !level) return <StateView state="empty" title={t('capacity.empty', 'No capacity data')} />;

  const b = data.beds;
  const s = data.staff;
  const asOf = formatDateTime(data.as_of);
  const byWard = b.by_ward || {};
  const wardKeys = [
    ...WARD_TYPES.filter((w) => byWard[w]),
    ...Object.keys(byWard).filter((w) => !(WARD_TYPES as readonly string[]).includes(w)),
  ];
  const noBedData = b.facilities_fresh + b.facilities_stale === 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>
            {t('capacity.title', 'Bed and Staff Capacity')} - {levelLabel(level)}
          </h2>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '0.4rem', alignItems: 'center', marginTop: '0.2rem' }}>
            <Clock size={13} aria-hidden="true" />
            <span>
              {data.scope ? `${data.scope} · ` : ''}
              {t('capacity.as_of', 'As of {time}', { time: asOf || notReported })}
            </span>
          </div>
        </div>
        <button
          className="btn-secondary"
          onClick={load}
          disabled={loading}
          style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center', fontSize: '0.825rem', padding: '0.5rem 0.9rem' }}
        >
          <RefreshCw size={14} aria-hidden="true" /> {t('capacity.refresh', 'Refresh')}
        </button>
      </div>

      {filters}

      <div aria-live="polite" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1rem' }}>
        <Kpi icon={<BedDouble size={22} />} label={t('capacity.kpi.total', 'Total beds reported')} value={noBedData ? notReported : num(b.total)}
          hint={t('capacity.kpi.facilities', '{n} facilities in scope', { n: data.facilities })} />
        <Kpi icon={<BedDouble size={22} />} label={t('capacity.kpi.occupied', 'Occupied beds')} value={noBedData ? notReported : num(b.occupied)}
          hint={t('capacity.kpi.occ_pct', 'Occupancy {pct}', { pct: pct(b.occupancy_pct) })} />
        <Kpi icon={<BedDouble size={22} />} label={t('capacity.kpi.available', 'Available beds')} value={noBedData ? notReported : num(b.available)}
          hint={t('capacity.kpi.fresh_avail', '{n} available in up-to-date facilities', { n: num(b.fresh_available) })} />
        <Kpi icon={<Users size={22} />} label={t('capacity.kpi.staff', 'Staff present today')}
          value={s.assigned_in_reporting_facilities > 0 ? `${s.present_today} / ${s.assigned_in_reporting_facilities}` : notReported}
          hint={t('capacity.kpi.staff_pct', 'Availability {pct} (reporting facilities only)', { pct: pct(s.availability_pct) })} />
      </div>

      <div className="glass-card" style={card}>
        <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.05rem', fontWeight: 700 }}>
          {t('capacity.data_quality', 'Data completeness')}
        </h3>
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', gap: '0.5rem 1.5rem', flexWrap: 'wrap', fontSize: '0.85rem' }}>
          <li>{t('capacity.dq.fresh', 'Bed data up to date: {n}', { n: b.facilities_fresh })}</li>
          <li>{t('capacity.dq.stale', 'Bed data stale: {n}', { n: b.facilities_stale })}</li>
          <li>{t('capacity.dq.no_data', 'No bed data: {n}', { n: b.facilities_no_data })}</li>
        </ul>
        <p style={{ margin: '0.6rem 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {t('capacity.dq.note', 'Totals include only recorded values. Facilities with no data are not counted as zero beds.')}
        </p>
      </div>

      <div className="glass-card" style={card}>
        <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.05rem', fontWeight: 700 }}>
          {t('capacity.wards.title', 'Ward breakdown')}
        </h3>
        {wardKeys.length === 0 ? (
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.875rem' }}>{notReported}</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            {wardKeys.map((w) => {
              const v = byWard[w];
              const name = t(wardLabelKey(w), wardFallback(w));
              return (
                <div key={w}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.3rem' }}>
                    <span>{name}</span>
                    <span>{t('capacity.wards.avail', '{n} available', { n: v.available })}</span>
                  </div>
                  <OccupancyBar occupied={v.occupied} total={v.total} label={name} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="glass-card" style={card}>
        <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.05rem', fontWeight: 700 }}>
          {t('capacity.flagged.title', 'Facilities needing attention')} ({data.flagged_facilities_count})
        </h3>
        <p style={{ margin: '0 0 0.75rem 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {t('capacity.flagged.note', 'Bed or attendance data is missing or older than {h} hours.', { h: data.stale_after_hours ?? 24 })}
        </p>
        {data.flagged_facilities.length === 0 ? (
          <StateView
            state="empty"
            title={t('capacity.flagged.none', 'All facilities are reporting')}
            message={t('capacity.flagged.none_msg', 'No missing or stale data in this scope.')}
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: '560px' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                  <th scope="col" style={{ padding: '0.5rem' }}>{t('capacity.col.facility', 'Facility')}</th>
                  <th scope="col" style={{ padding: '0.5rem' }}>{t('capacity.col.beds', 'Bed data')}</th>
                  <th scope="col" style={{ padding: '0.5rem' }}>{t('capacity.col.attendance', 'Attendance')}</th>
                </tr>
              </thead>
              <tbody>
                {data.flagged_facilities.map((f) => (
                  <tr key={f.facility_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <th scope="row" style={{ padding: '0.5rem', textAlign: 'left', fontWeight: 600 }}>
                      {f.facility_name}
                      <div style={{ fontWeight: 400, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {[f.district, f.state].filter(Boolean).join(', ')}
                      </div>
                    </th>
                    <td style={{ padding: '0.5rem' }}>
                      <FreshnessBadge status={f.beds_status} />
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {formatDateTime(f.beds_last_updated_at) || t('capacity.never', 'Never reported')}
                      </div>
                    </td>
                    <td style={{ padding: '0.5rem' }}>
                      <FreshnessBadge status={f.attendance_status} />
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {formatDateTime(f.last_attendance_at) || t('capacity.never', 'Never reported')}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data.flagged_truncated && (
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            {t('capacity.flagged.truncated', 'List truncated; showing the first {n} of {total}.',
              { n: data.flagged_facilities.length, total: data.flagged_facilities_count })}
          </p>
        )}
      </div>
    </div>
  );
}
