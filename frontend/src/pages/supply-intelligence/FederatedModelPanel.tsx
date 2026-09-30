import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, ShieldCheck, Database, Cpu, Play } from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '../../components/ui/table';
import { TierBadge, KeyValues, stateViewTypeFor } from './shared';

interface Prior { medication_id: string; medication_name: string; round_no: number; n_states: number; n_samples: number; mean_daily_rate: number; variance: number }
interface FcItem {
  medication_id: string; medication_name: string; local_daily_rate: number; sparse_data: boolean;
  national_prior_weight: number; national_prior_rate: number | null;
  forecast_daily_rate: number; days_of_supply: number | null; risk_tier: string; confidence: number;
}

export interface FederatedModelPanelProps {
  facilityId?: string;
  medicationId?: string;
  horizonDays?: number;
}

const unwrap = (d: any) => (d && d.data !== undefined ? d.data : d);

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

  if (loading) return <StateView type="loading" message={t('supplyIntel.loading', 'Loading federated models…')} />;
  if (error) {
    return (
      <StateView
        type={stateViewTypeFor(error)}
        title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : t('supplyIntel.fed.title', 'Federated model')}
        message={error.detail}
        onRetry={() => void load()}
      />
    );
  }

  const priorFor = (id: string) => priors.find((p) => p.medication_id === id);
  const cols: [string, string][] = [
    ['medication', 'Medication'], ['nationalPrior', 'National prior'], ['localRate', 'Local rate'], ['priorWeight', 'Prior weight'],
    ['forecastRate', 'Blended forecast'], ['daysSupply', 'Days of supply'], ['risk', 'Risk'], ['confidence', 'Confidence'],
  ];

  return (
    <section aria-labelledby="fed-h" className="space-y-6">
      {/* Context-First Section Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Supply Intelligence', href: '/supply' },
          { label: 'Federated Demand Model' }
        ]}
        scopeBadge={{ label: 'Federated Learning Grid', variant: 'purple' }}
        roleBadge={{ label: 'Bayesian Aggregation', variant: 'outline' }}
        title={t('supplyIntel.fed.title', 'Federated Medicine Demand Forecasting')}
        description="Privacy-preserving Bayesian parameter sharing blends national consumption baselines with rural facility consumption velocities."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load()}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {t('supplyIntel.refresh', 'Refresh')}
          </Button>
        }
      />

      {/* Privacy Guarantee Context Banner */}
      <Alert className="border-purple-200 bg-purple-50/70 text-purple-950">
        <ShieldCheck className="w-4 h-4 text-purple-700" />
        <div className="flex-1">
          <AlertTitle className="text-xs font-bold uppercase tracking-wider text-purple-950">
            Privacy-Preserving Edge Learning Architecture
          </AlertTitle>
          <AlertDescription className="text-xs text-purple-900 mt-0.5 leading-relaxed">
            {t('supplyIntel.fed.privacy', 'Only aggregate mathematical parameters (daily rate, variance, seasonality and sample counts) are shared between states and the national coordinator. Patient records and individual prescription transactions strictly never leave their facility or state boundary.')}
          </AlertDescription>
        </div>
      </Alert>

      {/* National Prior vs Facility Forecast Table */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-foreground font-bold">
            {t('supplyIntel.fed.priorVsForecast', 'National Prior vs. Facility Forecast')}
          </CardTitle>
          <CardDescription className="text-xs">
            {t('supplyIntel.fed.caption', 'Consumption rates expressed in standard units per day.')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {forecastError && (
            <div className="p-4">
              <Alert variant="destructive" className="text-xs">
                <AlertDescription>
                  {t('supplyIntel.fed.forecastError', 'Facility forecast unavailable')}: {forecastError.detail}
                </AlertDescription>
              </Alert>
            </div>
          )}

          {items.length === 0 && !forecastError ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              {t('supplyIntel.fed.empty', 'No forecast items for this facility.')}
            </div>
          ) : items.length > 0 && (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {cols.map(([k, fb]) => (
                      <TableHead key={k}>{t(`supplyIntel.fed.col.${k}`, fb)}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((it) => {
                    const p = priorFor(it.medication_id);
                    return (
                      <TableRow key={it.medication_id}>
                        <TableCell>
                          <div className="font-semibold text-foreground text-xs">{it.medication_name}</div>
                          {it.sparse_data && (
                            <Badge variant="outline" className="text-[10px] text-amber-700 border-amber-200 mt-0.5">
                              {t('supplyIntel.fed.sparse', 'sparse local data')}
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-xs">
                          <div className="font-medium text-foreground">
                            {it.national_prior_rate ?? p?.mean_daily_rate ?? t('supplyIntel.fed.noPrior', 'no prior')}
                          </div>
                          {p && (
                            <div className="text-[10px] text-muted-foreground">
                              {t('supplyIntel.fed.round', 'round')} {p.round_no} · {p.n_states} {t('supplyIntel.fed.states', 'states')}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="font-mono text-xs">{it.local_daily_rate}</TableCell>
                        <TableCell className="text-xs font-semibold text-purple-700">
                          {Math.round(it.national_prior_weight * 100)}%
                        </TableCell>
                        <TableCell className="font-mono font-bold text-foreground text-xs">
                          {it.forecast_daily_rate}
                        </TableCell>
                        <TableCell className="text-xs text-foreground font-semibold">
                          {it.days_of_supply ?? '—'} days
                        </TableCell>
                        <TableCell>
                          <TierBadge tier={it.risk_tier} />
                        </TableCell>
                        <TableCell className="text-xs font-medium text-emerald-700">
                          {Math.round(it.confidence * 100)}%
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          {priors.length === 0 && (
            <div className="p-4 text-xs text-muted-foreground italic border-t">
              {t('supplyIntel.fed.noPriors', 'No national prior has been published yet; forecasts use local data only.')}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Federation Control Panel for State/Global roles */}
      {canFederate && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground font-bold flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-700" />
              {t('supplyIntel.fed.admin', 'Federation Engine Governance')}
            </CardTitle>
            <CardDescription className="text-xs">
              Execute local federated updates or aggregate national prior weights.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">
                  {t('supplyIntel.fed.stateLabel', 'State')}
                </label>
                <Input
                  value={stateName}
                  onChange={(e) => setStateName(e.target.value)}
                  placeholder={canAggregate ? t('supplyIntel.fed.stateRequired', 'Required for national users') : ''}
                  className="text-xs h-9 w-48"
                />
              </div>

              <Button
                variant="default"
                size="sm"
                disabled={action.busy || (canAggregate && !stateName)}
                onClick={() => void run('local')}
                className="h-9 text-xs bg-purple-700 hover:bg-purple-800 text-white gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {action.busy && action.which === 'local' ? t('supplyIntel.running', 'Running…') : t('supplyIntel.fed.runLocal', 'Compute State Update')}
              </Button>

              {canAggregate && (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={action.busy}
                  onClick={() => void run('aggregate')}
                  className="h-9 text-xs gap-1.5"
                >
                  <Database className="w-3.5 h-3.5" />
                  {action.busy && action.which === 'aggregate' ? t('supplyIntel.running', 'Running…') : t('supplyIntel.fed.runAggregate', 'Aggregate National Prior')}
                </Button>
              )}
            </div>

            <div aria-live="polite">
              {action.error && (
                <Alert variant="destructive" className="text-xs">
                  <AlertDescription>{action.error}</AlertDescription>
                </Alert>
              )}
              {action.result && (
                <div className="p-3 bg-muted/60 rounded-lg border border-border space-y-1 text-xs">
                  <div className="font-semibold text-foreground">{t('supplyIntel.fed.response', 'Server Response')}</div>
                  <pre className="font-mono text-[11px] overflow-x-auto p-2 bg-background rounded border">
                    {JSON.stringify(action.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {priors.length > 0 && (
              <details className="p-3 bg-muted/30 rounded-lg border border-border text-xs">
                <summary className="cursor-pointer font-semibold text-foreground">
                  {t('supplyIntel.fed.priorsDetail', 'Published National Priors')} ({priors.length})
                </summary>
                <div className="mt-3 space-y-3">
                  {priors.map((p) => (
                    <div key={p.medication_id} className="p-2.5 bg-background rounded border space-y-1">
                      <div className="font-bold text-foreground">{p.medication_name}</div>
                      <KeyValues data={{ round: p.round_no, states: p.n_states, samples: p.n_samples, mean_daily_rate: p.mean_daily_rate, variance: p.variance }} />
                    </div>
                  ))}
                </div>
              </details>
            )}
          </CardContent>
        </Card>
      )}
    </section>
  );
};

export default FederatedModelPanel;
