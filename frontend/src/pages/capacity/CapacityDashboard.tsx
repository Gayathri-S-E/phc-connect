import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BedDouble, Users, RefreshCw, Clock, AlertTriangle, Building2, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '../../components/ui/table';
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

export default function CapacityDashboard() {
  const { t } = useLanguage();
  const { user, hasPermission } = useAuth();

  const candidates = useMemo<Level[]>(() => {
    const list: Level[] = [];
    if (hasPermission('governance.national.view')) list.push('national');
    if (hasPermission('governance.state.view')) list.push('state');
    if (hasPermission('governance.district.view')) list.push('district');
    return list;
  }, [user, hasPermission]);

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
      if (res.error.status !== 403) break;
    }
    setData(null);
    setLevel(null);
    setError(last);
    setLoading(false);
  }, [candidates, stateFilter, districtFilter]);

  useEffect(() => {
    load();
  }, []);

  const levelLabel = (lv: Level) =>
    lv === 'national' ? t('capacity.level.national', 'National')
      : lv === 'state' ? t('capacity.level.state', 'State') : t('capacity.level.district', 'District');

  const notReported = t('capacity.not_reported', 'Not reported');
  const num = (v: number | null | undefined) => (isNum(v) ? v.toLocaleString() : notReported);
  const pct = (v: number | null | undefined) => (isNum(v) ? `${v}%` : notReported);

  if (loading && !data) {
    return <StateView type="loading" message={t('capacity.loading', 'Loading capacity data...')} />;
  }

  const needsFilters = candidates.length > 0 && candidates[0] !== 'national';
  const filters = needsFilters ? (
    <Card className="border-border shadow-xs">
      <CardContent className="p-4">
        <form
          onSubmit={(e) => { e.preventDefault(); load(); }}
          className="flex flex-wrap items-end gap-3"
        >
          <div className="space-y-1">
            <label htmlFor="cap-state" className="text-xs font-semibold text-foreground">
              {t('capacity.filter.state', 'State')}
            </label>
            <Input 
              id="cap-state" 
              value={stateFilter} 
              onChange={(e) => setStateFilter(e.target.value)} 
              className="text-xs h-9 w-40" 
            />
          </div>
          {candidates[0] === 'district' && (
            <div className="space-y-1">
              <label htmlFor="cap-district" className="text-xs font-semibold text-foreground">
                {t('capacity.filter.district', 'District')}
              </label>
              <Input 
                id="cap-district" 
                value={districtFilter} 
                onChange={(e) => setDistrictFilter(e.target.value)} 
                className="text-xs h-9 w-40" 
              />
            </div>
          )}
          <Button type="submit" variant="secondary" size="sm" className="h-9 text-xs">
            {t('capacity.filter.apply', 'Apply Filters')}
          </Button>
        </form>
      </CardContent>
    </Card>
  ) : null;

  if (error) {
    if (error.status === 403) {
      return (
        <StateView
          type="403"
          message={t('capacity.forbidden.message', 'Your role does not have access to district, state or national capacity roll-ups.')}
        />
      );
    }
    return (
      <div className="space-y-4">
        {filters}
        <StateView
          type="error"
          message={error.detail || t('capacity.error.title', 'Could not load capacity data')}
          onRetry={load}
        />
      </div>
    );
  }

  if (!data || !level) return <StateView type="empty" message={t('capacity.empty', 'No capacity data available for this scope.')} />;

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
    <div className="space-y-6">
      {/* Context-First Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Operations & Capacity', href: '/capacity' },
          { label: `${levelLabel(level)} Roll-Up` }
        ]}
        scopeBadge={{ label: `${data.scope || levelLabel(level)} Scope`, variant: 'teal' }}
        roleBadge={{ label: 'Capacity Intelligence', variant: 'outline' }}
        title={`${t('capacity.title', 'Bed and Staff Capacity')} — ${levelLabel(level)}`}
        description={`Real-time occupancy status, clinical staffing availability, and telemetry freshness across ${data.facilities} network facilities.`}
        actions={
          <Button
            onClick={load}
            disabled={loading}
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {t('capacity.refresh', 'Refresh Data')}
          </Button>
        }
      />

      {filters}

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border shadow-xs hover:border-teal-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('capacity.kpi.total', 'Total Beds Reported')}</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{noBedData ? notReported : num(b.total)}</h3>
              <p className="text-xs text-muted-foreground mt-1">
                {t('capacity.kpi.facilities', '{n} facilities in scope', { n: data.facilities })}
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
              <BedDouble className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-amber-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('capacity.kpi.occupied', 'Occupied Beds')}</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{noBedData ? notReported : num(b.occupied)}</h3>
              <p className="text-xs text-amber-700 font-medium mt-1">
                {t('capacity.kpi.occ_pct', 'Occupancy {pct}', { pct: pct(b.occupancy_pct) })}
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
              <BedDouble className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-emerald-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('capacity.kpi.available', 'Available Beds')}</p>
              <h3 className="text-2xl font-bold text-emerald-700 mt-1">{noBedData ? notReported : num(b.available)}</h3>
              <p className="text-xs text-muted-foreground mt-1">
                {t('capacity.kpi.fresh_avail', '{n} available in fresh units', { n: num(b.fresh_available) })}
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <CheckCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-sky-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('capacity.kpi.staff', 'Staff Present Today')}</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">
                {s.assigned_in_reporting_facilities > 0 ? `${s.present_today} / ${s.assigned_in_reporting_facilities}` : notReported}
              </h3>
              <p className="text-xs text-sky-700 font-medium mt-1">
                {t('capacity.kpi.staff_pct', 'Availability {pct}', { pct: pct(s.availability_pct) })}
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <Users className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Completeness & Reporting Freshness */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-foreground flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-600" />
            {t('capacity.data_quality', 'Data Completeness & Freshness')}
          </CardTitle>
          <CardDescription>
            {t('capacity.as_of', 'As of {time}', { time: asOf || notReported })}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex flex-wrap gap-4 text-xs font-semibold">
            <div className="flex items-center gap-1.5 text-emerald-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>{t('capacity.dq.fresh', 'Bed data up to date: {n}', { n: b.facilities_fresh })}</span>
            </div>
            <div className="flex items-center gap-1.5 text-amber-700">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>{t('capacity.dq.stale', 'Bed data stale: {n}', { n: b.facilities_stale })}</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <span className="w-2 h-2 rounded-full bg-slate-300" />
              <span>{t('capacity.dq.no_data', 'No bed data: {n}', { n: b.facilities_no_data })}</span>
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground pt-1">
            {t('capacity.dq.note', 'Totals include only recorded values. Facilities with no data are not counted as zero beds.')}
          </p>
        </CardContent>
      </Card>

      {/* Ward Breakdown */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-foreground">
            {t('capacity.wards.title', 'Ward Breakdown')}
          </CardTitle>
          <CardDescription>
            Occupancy breakdown across clinical care departments.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {wardKeys.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">{notReported}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {wardKeys.map((w) => {
                const v = byWard[w];
                const name = t(wardLabelKey(w), wardFallback(w));
                return (
                  <div key={w} className="p-3.5 bg-muted/40 rounded-lg border border-border space-y-2">
                    <div className="flex justify-between items-center text-xs font-bold text-foreground">
                      <span>{name}</span>
                      <span className="text-emerald-700">
                        {t('capacity.wards.avail', '{n} available', { n: v.available })}
                      </span>
                    </div>
                    <OccupancyBar occupied={v.occupied} total={v.total} label={name} />
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Facilities Needing Attention */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                {t('capacity.flagged.title', 'Facilities Needing Attention')} ({data.flagged_facilities_count})
              </CardTitle>
              <CardDescription>
                {t('capacity.flagged.note', 'Bed or attendance data is missing or older than {h} hours.', { h: data.stale_after_hours ?? 24 })}
              </CardDescription>
            </div>
            {data.flagged_facilities.length > 0 && (
              <Badge variant="warning">{data.flagged_facilities_count} Flagged</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {data.flagged_facilities.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="font-semibold text-foreground">{t('capacity.flagged.none', 'All facilities are reporting')}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{t('capacity.flagged.none_msg', 'No missing or stale data in this scope.')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('capacity.col.facility', 'Facility')}</TableHead>
                    <TableHead>{t('capacity.col.beds', 'Bed Data Status')}</TableHead>
                    <TableHead>{t('capacity.col.attendance', 'Attendance Status')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.flagged_facilities.map((f) => (
                    <TableRow key={f.facility_id}>
                      <TableCell>
                        <div className="font-semibold text-foreground text-xs">{f.facility_name}</div>
                        <div className="text-[11px] text-muted-foreground">
                          {[f.district, f.state].filter(Boolean).join(', ')}
                        </div>
                      </TableCell>
                      <TableCell>
                        <FreshnessBadge status={f.beds_status} />
                        <div className="text-[11px] text-muted-foreground mt-1">
                          {formatDateTime(f.beds_last_updated_at) || t('capacity.never', 'Never reported')}
                        </div>
                      </TableCell>
                      <TableCell>
                        <FreshnessBadge status={f.attendance_status} />
                        <div className="text-[11px] text-muted-foreground mt-1">
                          {formatDateTime(f.last_attendance_at) || t('capacity.never', 'Never reported')}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          {data.flagged_truncated && (
            <div className="p-3 text-[11px] text-muted-foreground text-center border-t">
              {t('capacity.flagged.truncated', 'List truncated; showing the first {n} of {total}.',
                { n: data.flagged_facilities.length, total: data.flagged_facilities_count })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
