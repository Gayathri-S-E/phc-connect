import React, { useCallback, useEffect, useState } from 'react';
import { RefreshCw, ArrowRight, ChevronDown, ChevronRight, AlertTriangle, ArrowRightLeft, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { TierBadge, KeyValues, stateViewTypeFor } from './shared';

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

  if (loading) return <StateView type="loading" message={t('supplyIntel.loading', 'Loading redistribution plans…')} />;
  if (error) {
    return (
      <StateView
        type={stateViewTypeFor(error)}
        title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : t('supplyIntel.redis.title', 'Cross-district redistribution')}
        message={error.detail}
        onRetry={() => void load()}
      />
    );
  }
  const recs = data?.recommendations || [];
  const unmet = data?.unmet_needs || [];

  return (
    <section aria-labelledby="redis-h" className="space-y-6">
      {/* Context-First Section Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Supply Intelligence', href: '/supply' },
          { label: 'Redistribution Planner' }
        ]}
        scopeBadge={{ label: 'Cross-Facility Rebalancing', variant: 'teal' }}
        roleBadge={{ label: `${recs.length} Proposals`, variant: recs.length > 0 ? 'info' : 'outline' }}
        title={t('supplyIntel.redis.title', 'Cross-District Redistribution Suggestions')}
        description="Optimization engine identifying surplus inventory near donor facilities to avert impending stockouts without new procurement."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load()}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {t('supplyIntel.refresh', 'Refresh Suggestions')}
          </Button>
        }
      />

      {/* Advisory Banner */}
      <Alert className="border-amber-200 bg-amber-50/70 text-amber-900">
        <AlertTriangle className="w-4 h-4 text-amber-600" />
        <div className="flex-1">
          <AlertTitle className="text-xs font-bold uppercase tracking-wider text-amber-900">
            {t('supplyIntel.advisoryApproval', 'Statutory Human-in-the-Loop Safeguard')}
          </AlertTitle>
          <AlertDescription className="text-xs text-amber-800 mt-0.5">
            {data?.advisory_notice || t('supplyIntel.advisoryText', 'Nothing is transferred or ordered automatically.')}{' '}
            {t('supplyIntel.raiseViaSupply', 'To execute a transfer, review and authorize via the Supply module.')}
            {supplyModulePath && (
              <a href={supplyModulePath} className="font-bold underline ml-1 text-amber-950">
                {t('supplyIntel.openSupply', 'Open Supply module →')}
              </a>
            )}
          </AlertDescription>
        </div>
      </Alert>

      {/* Recommendations List */}
      {recs.length === 0 ? (
        <StateView 
          type="empty" 
          message={t('supplyIntel.redis.empty', 'No redistribution suggestions for your scope right now.')} 
        />
      ) : (
        <div className="grid gap-4">
          {recs.map((r, i) => (
            <Card key={`${r.source_facility_id}-${r.destination_facility_id}-${r.medication_id}-${i}`} className="border-border shadow-xs hover:border-teal-300 transition-colors">
              <CardHeader className="pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <CardTitle className="text-base text-foreground font-bold">{r.medication_name}</CardTitle>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="border-amber-300 text-amber-800 text-[10px] font-bold">
                      {t('supplyIntel.advisoryTag', 'ADVISORY')} · {t('supplyIntel.needsApproval', 'needs approval')}
                    </Badge>
                    <TierBadge tier={r.urgency} />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Logistics Route Banner */}
                <div className="p-3 bg-muted/40 rounded-lg border border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
                  <div className="flex-1">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold">{t('supplyIntel.from', 'Donor Facility')}</span>
                    <div className="font-bold text-foreground text-sm">{r.source_facility_name}</div>
                    <div className="text-[11px] text-muted-foreground">{r.source_district}{r.source_state ? `, ${r.source_state}` : ''}</div>
                  </div>

                  <div className="flex items-center gap-2 text-teal-600 font-bold self-center px-2">
                    <ArrowRight className="w-5 h-5 hidden sm:block" />
                    <span className="text-[11px] bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                      {r.distance_km != null ? `${r.distance_km} km` : t('supplyIntel.distanceUnknown', 'unknown distance')}
                    </span>
                  </div>

                  <div className="flex-1 sm:text-right">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold">{t('supplyIntel.to', 'Recipient Facility')}</span>
                    <div className="font-bold text-foreground text-sm">{r.destination_facility_name}</div>
                    <div className="text-[11px] text-muted-foreground">{r.destination_district}{r.destination_state ? `, ${r.destination_state}` : ''}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                    <div className="text-[10px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.quantity', 'Suggested Transfer')}</div>
                    <div className="text-base font-bold text-teal-700 mt-0.5">{r.recommended_quantity} units</div>
                  </div>
                  {r.level && (
                    <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                      <div className="text-[10px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.level', 'Administrative Level')}</div>
                      <div className="font-semibold text-foreground mt-0.5">{r.level.replace(/_/g, ' ')}</div>
                    </div>
                  )}
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                    <div className="text-[10px] text-muted-foreground uppercase font-semibold">Priority Urgency</div>
                    <div className="font-semibold text-foreground mt-0.5">{r.urgency}</div>
                  </div>
                </div>

                <p className="text-xs text-foreground leading-relaxed">{r.rationale}</p>
                {r.next_step && <p className="text-xs text-muted-foreground italic">{r.next_step}</p>}

                <div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setOpen((o) => ({ ...o, [i]: !o[i] }))}
                    className="h-7 text-xs font-semibold text-sky-700 hover:text-sky-900 gap-1 p-0"
                  >
                    {open[i] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    {t('supplyIntel.evidence', 'View Evidence & Calculations')}
                  </Button>

                  {open[i] && (
                    <div className="mt-3 p-3 bg-muted/60 rounded-lg border border-border space-y-2 text-xs">
                      {r.distance_basis && <p className="text-muted-foreground text-[11px]">{r.distance_basis}</p>}
                      <KeyValues data={r.evidence || {}} />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Unmet Needs */}
      {unmet.length > 0 && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold text-foreground">
              {t('supplyIntel.unmet', 'Unmet Needs (No Eligible Local Donor Identified)')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {unmet.map((u, i) => (
                <div key={`${u.facility_id}-${u.medication_id}-${i}`} className="py-2.5 flex items-center justify-between text-xs gap-3">
                  <div className="flex items-center gap-2">
                    <TierBadge tier={u.urgency} />
                    <span className="font-semibold text-foreground">{u.medication_name}</span>
                    <span className="text-muted-foreground">@ {u.facility_name}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-rose-600">{u.unmet_quantity} {t('supplyIntel.units', 'units')} deficit</span>
                    <div className="text-[11px] text-muted-foreground">{u.suggestion}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Methodology Section */}
      {data?.methodology && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {t('supplyIntel.methodology', 'Redistribution Methodology & Optimization Weights')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <KeyValues data={data.methodology} />
          </CardContent>
        </Card>
      )}
    </section>
  );
};

export default RedistributionPlanner;
