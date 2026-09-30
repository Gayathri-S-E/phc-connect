import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, Clock, Check, BedDouble, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
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
    <Card className="border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base text-foreground font-bold">{name}</CardTitle>
          <Badge variant="teal" className="text-xs">
            {t('capacity.wards.avail', '{n} available', { n: ward.available_beds })}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          {t('capacity.last_updated', 'Last updated {time}', { time: formatDateTime(ward.updated_at) || t('capacity.not_reported', 'Not reported') })}
          {ward.last_updated_by ? ` · by user ${ward.last_updated_by.slice(0, 8)}` : ''}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <OccupancyBar occupied={ward.occupied_beds} total={ward.total_beds} label={name} />

        <form onSubmit={submit} className="space-y-3 pt-1" noValidate>
          <div className={`grid gap-3 ${canManage ? 'grid-cols-2' : 'grid-cols-1'}`}>
            <div className="space-y-1">
              <label htmlFor={`${idBase}-occ`} className="text-xs font-semibold text-foreground">
                {t('capacity.form.occupied', 'Occupied Beds')}
              </label>
              <Input
                id={`${idBase}-occ`}
                type="number"
                inputMode="numeric"
                min={0}
                max={effectiveTotal}
                step={1}
                value={occupied}
                onChange={(e) => setOccupied(e.target.value)}
                className="text-xs font-mono font-bold"
                aria-invalid={!!validation}
                aria-describedby={validation ? errId : undefined}
              />
            </div>
            {canManage && (
              <div className="space-y-1">
                <label htmlFor={`${idBase}-tot`} className="text-xs font-semibold text-foreground">
                  {t('capacity.form.total', 'Total Capacity')}
                </label>
                <Input
                  id={`${idBase}-tot`}
                  type="number"
                  inputMode="numeric"
                  min={0}
                  step={1}
                  value={total}
                  onChange={(e) => setTotal(e.target.value)}
                  className="text-xs font-mono font-bold"
                />
              </div>
            )}
          </div>

          <div className="space-y-1">
            <label htmlFor={`${idBase}-note`} className="text-xs font-semibold text-foreground">
              {t('capacity.form.note', 'Census Note (optional)')}
            </label>
            <Input
              id={`${idBase}-note`}
              type="text"
              maxLength={500}
              placeholder="e.g. 2 discharges scheduled at 14:00"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="text-xs"
            />
          </div>

          {validation && (
            <p id={errId} role="alert" className="text-xs text-rose-600 font-medium">
              {validation}
            </p>
          )}

          <Button
            type="submit"
            disabled={saving || !!validation}
            variant="teal"
            size="sm"
            className="w-full gap-1.5 text-xs font-semibold"
          >
            <Check className="w-3.5 h-3.5" />
            {saving ? t('capacity.form.saving', 'Recording Census...') : t('capacity.form.save', 'Save Bed Census')}
          </Button>

          {result && (
            <Alert variant={result.ok ? 'default' : 'destructive'} className="py-2 text-xs">
              {result.ok ? (
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <AlertCircle className="w-3.5 h-3.5" />
              )}
              <AlertDescription className="text-xs">{result.msg}</AlertDescription>
            </Alert>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

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
        type="empty"
        message={t('capacity.panel.no_facility_msg', 'Your account is not linked to a facility, so there are no beds to manage.')}
      />
    );
  }
  if (loading && !beds) return <StateView type="loading" message={t('capacity.panel.loading', 'Loading facility bed data...')} />;
  if (error) {
    return (
      <StateView
        type={error.status === 403 ? '403' : 'error'}
        message={error.detail || t('capacity.panel.error', 'Could not load bed data')}
        onRetry={() => load()}
      />
    );
  }
  if (!beds) return null;

  const wardsSorted = [...beds.wards].sort(
    (a, b) => (WARD_TYPES as readonly string[]).indexOf(a.ward_type as any) - (WARD_TYPES as readonly string[]).indexOf(b.ward_type as any),
  );
  const notReported = t('capacity.not_reported', 'Not reported');

  return (
    <div className="space-y-6">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Facility Inpatient Care', href: '/facility' },
          { label: 'Ward Bed Census' }
        ]}
        scopeBadge={{ label: 'Facility Inpatient Ward', variant: 'teal' }}
        roleBadge={{ label: canUpdate ? 'Census Recording Active' : 'Read Only', variant: canUpdate ? 'success' : 'outline' }}
        title={t('capacity.panel.title', 'Facility Ward Bed Census')}
        description="Daily occupancy log and available capacity management across inpatient care wards."
        actions={
          <div className="flex items-center gap-2">
            <FreshnessBadge status={beds.status} />
            <Button
              onClick={() => load()}
              disabled={loading}
              variant="outline"
              size="sm"
              className="gap-1.5 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              {t('capacity.refresh', 'Refresh')}
            </Button>
          </div>
        }
      />

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-border shadow-xs hover:border-teal-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('capacity.kpi.total', 'Total Beds Reported')}</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{isNum(beds.total_beds) ? beds.total_beds : notReported}</h3>
              <p className="text-xs text-muted-foreground mt-1">Authorized bed strength</p>
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
              <h3 className="text-2xl font-bold text-foreground mt-1">{isNum(beds.occupied_beds) ? beds.occupied_beds : notReported}</h3>
              <p className="text-xs text-amber-700 font-medium mt-1">Active inpatient census</p>
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
              <h3 className="text-2xl font-bold text-emerald-700 mt-1">{isNum(beds.available_beds) ? beds.available_beds : notReported}</h3>
              <p className="text-xs text-emerald-700 font-medium mt-1">Ready for immediate admission</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <CheckCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ward Cards / Forms */}
      {wardsSorted.length === 0 ? (
        <StateView
          type="empty"
          message={t('capacity.panel.no_wards_msg', 'No bed data has been reported for this facility. A bed-inventory manager must register its wards.')}
        />
      ) : canUpdate ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {wardsSorted.map((w) => (
            <WardForm key={w.ward_type} ward={w} facilityId={fid} canManage={canManage} onSaved={() => load(true)} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {wardsSorted.map((w) => {
            const name = t(wardLabelKey(w.ward_type), wardFallback(w.ward_type));
            return (
              <Card key={w.ward_type} className="border-border shadow-xs">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-base text-foreground font-bold">{name}</CardTitle>
                    <Badge variant="teal">{w.available_beds} available</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <OccupancyBar occupied={w.occupied_beds} total={w.total_beds} label={name} />
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Recent Updates History Log */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-foreground flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-600" />
            {t('capacity.history.title', 'Recent Census Updates')}
          </CardTitle>
          <CardDescription>
            Audit log of ward bed census entries submitted by clinical nursing staff.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {historyError ? (
            <Alert variant="destructive" className="text-xs">
              <AlertDescription>{historyError}</AlertDescription>
            </Alert>
          ) : history.length === 0 ? (
            <p className="text-xs text-muted-foreground italic">
              {t('capacity.history.empty', 'No updates recorded yet.')}
            </p>
          ) : (
            <div className="divide-y divide-border">
              {history.map((h) => (
                <div key={h.id} className="py-2.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs">
                  <div>
                    <div className="font-semibold text-foreground">
                      {t(wardLabelKey(h.ward_type), wardFallback(h.ward_type))}
                    </div>
                    <div className="text-muted-foreground">
                      {t('capacity.history.change', 'Occupied {prev} to {occ} of {total}', {
                        prev: isNum(h.previous_occupied_beds) ? h.previous_occupied_beds : '-',
                        occ: h.occupied_beds,
                        total: h.total_beds,
                      })}
                      {h.note && <span className="ml-2 italic text-foreground">"{h.note}"</span>}
                    </div>
                  </div>
                  <div className="text-right sm:self-center">
                    <div className="text-[11px] text-muted-foreground font-mono">
                      {formatDateTime(h.recorded_at) || notReported}
                    </div>
                    {h.recorded_by && (
                      <div className="text-[10px] text-muted-foreground">
                        {t('capacity.updated_by', 'by user {id}', { id: h.recorded_by.slice(0, 8) })}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
