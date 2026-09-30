import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, Sparkles, ChevronDown, ChevronRight, AlertTriangle, ShieldAlert, Info } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../context/LanguageContext';
import { StateView } from '../../components/common/StateView';
import type { ApiError } from '../../services/types';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { TierBadge, TIER_ORDER, KeyValues, stateViewTypeFor, fmtDate } from './shared';

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

  const title = t('supplyIntel.stockout.title', 'Emergency-Surge Stock-Out Warnings');

  if (loading) return <StateView type="loading" message={t('supplyIntel.loading', 'Loading warnings…')} />;
  if (error) {
    return (
      <StateView
        type={stateViewTypeFor(error)}
        title={error.status === 403 ? t('supplyIntel.forbidden', 'Access restricted') : title}
        message={error.detail}
        onRetry={() => void load(false)}
      />
    );
  }

  const explainRequested = !!data?.ai_explanation || (!!data?.ai_explanation_reason && data.ai_explanation_reason !== 'NOT_REQUESTED');

  return (
    <section aria-labelledby="stockout-h" className="space-y-6">
      {/* Context-First Section Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Supply Intelligence', href: '/supply' },
          { label: 'Stock-Out Warnings' }
        ]}
        scopeBadge={{ label: 'Dynamic Surge Risk Grid', variant: 'amber' }}
        roleBadge={{ label: `${items.length} Active Warnings`, variant: items.length > 0 ? 'warning' : 'success' }}
        title={title}
        description="Predictive inventory depletion model tracking elevated burn rate under public health surges."
        actions={
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => void load(false)}
              className="gap-1.5 text-xs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              {t('supplyIntel.refresh', 'Refresh')}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => void load(true)}
              disabled={explaining || items.length === 0}
              className="gap-1.5 text-xs bg-purple-700 hover:bg-purple-800 text-white"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {explaining ? t('supplyIntel.explaining', 'Explaining…') : t('supplyIntel.explainAi', 'Explain with AI')}
            </Button>
          </div>
        }
      />

      {/* Advisory Banner */}
      <Alert className="border-amber-200 bg-amber-50/70 text-amber-900">
        <AlertTriangle className="w-4 h-4 text-amber-600" />
        <div className="flex-1">
          <AlertTitle className="text-xs font-bold uppercase tracking-wider text-amber-900">
            {t('supplyIntel.advisory', 'Predictive Advisory Notice')}
          </AlertTitle>
          <AlertDescription className="text-xs text-amber-800 mt-0.5">
            {data?.advisory_notice || t('supplyIntel.advisoryText', 'Advisory only. Nothing is ordered or transferred automatically.')}
          </AlertDescription>
        </div>
      </Alert>

      {/* AI Explanation Area */}
      <div aria-live="polite">
        {explainError && (
          <Alert variant="destructive" className="text-xs">
            <AlertDescription>
              {t('supplyIntel.aiUnavailable', 'AI explanation unavailable')}: {explainError}
            </AlertDescription>
          </Alert>
        )}
        {!explainError && data && explainRequested && (
          <Card className="border-purple-200 bg-purple-50/40 shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold text-purple-950 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-700" />
                {t('supplyIntel.aiExplanation', 'AI Clinical Supply Assessment')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {data.ai_explanation ? (
                <p className="text-purple-950 whitespace-pre-wrap leading-relaxed">{data.ai_explanation}</p>
              ) : (
                <p className="text-muted-foreground italic">
                  {t('supplyIntel.aiUnavailable', 'AI explanation unavailable')}: {data.ai_explanation_reason || t('supplyIntel.unknownReason', 'unknown reason')}
                </p>
              )}
              {data.explanation && (
                <div className="p-2.5 bg-white/80 rounded border border-purple-100 text-slate-700">
                  <span className="font-semibold text-foreground">{t('supplyIntel.deterministic', 'Rule-based summary')}:</span> {data.explanation}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Warnings List */}
      {items.length === 0 ? (
        <StateView 
          type="empty" 
          message={t('supplyIntel.stockout.empty', 'No stock-out risks at or above the selected tier in your scope.')} 
        />
      ) : (
        <div className="grid gap-4">
          {items.map((it) => {
            const key = `${it.facility_id}:${it.medication_id}`;
            const isOpen = !!open[key];
            return (
              <Card key={key} className="border-border shadow-xs hover:border-amber-300 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-base text-foreground font-bold">{it.medication_name}</CardTitle>
                      <CardDescription className="text-xs">
                        {it.facility_name}{it.district ? ` · ${it.district}` : ''}{it.state ? `, ${it.state}` : ''}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <TierBadge tier={it.risk_tier} />
                      {it.escalated_by_emergency && (
                        <Badge variant="warning" className="text-[10px]">
                          {t('supplyIntel.escalated', 'raised by emergency')} ({t('supplyIntel.was', 'was')} {it.baseline_risk_tier})
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 p-3 bg-muted/40 rounded-lg border border-border text-xs">
                    <div>
                      <div className="text-[11px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.daysSurge', 'Surge Supply')}</div>
                      <div className="font-bold text-foreground text-sm mt-0.5">{it.days_of_supply_surge ?? '—'} days</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.daysBase', 'Baseline Supply')}</div>
                      <div className="text-foreground text-sm mt-0.5">{it.days_of_supply_baseline ?? '—'} days</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.stockoutDate', 'Predicted Depletion')}</div>
                      <div className="text-foreground font-medium text-xs mt-0.5">{fmtDate(it.predicted_stockout_date, language)}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.multiplier', 'Surge Multiplier')}</div>
                      <div className="font-bold text-amber-700 text-sm mt-0.5">×{it.evidence?.surge_multiplier ?? 1}</div>
                    </div>
                    <div>
                      <div className="text-[11px] text-muted-foreground uppercase font-semibold">{t('supplyIntel.confidence', 'Confidence')}</div>
                      <div className="text-emerald-700 font-bold text-sm mt-0.5">{Math.round((it.confidence || 0) * 100)}%</div>
                    </div>
                  </div>

                  <p className="text-xs text-foreground leading-relaxed">{it.explanation}</p>

                  <div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setOpen((o) => ({ ...o, [key]: !o[key] }))}
                      className="h-7 text-xs font-semibold text-sky-700 hover:text-sky-900 gap-1 p-0"
                    >
                      {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      {t('supplyIntel.evidence', 'Evidence and calculation formula')}
                    </Button>

                    {isOpen && (
                      <div id={`ev-${key}`} className="mt-3 p-3 bg-muted/60 rounded-lg border border-border space-y-2 text-xs">
                        {it.evidence?.incident?.formula && (
                          <div className="p-2 bg-background rounded border font-mono text-[11px]">
                            <span className="font-semibold text-foreground">{t('supplyIntel.formula', 'Multiplier formula')}:</span> {it.evidence.incident.formula}
                          </div>
                        )}
                        <KeyValues data={it.evidence || {}} />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Methodology Section */}
      {data?.methodology && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-3">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {t('supplyIntel.methodology', 'Methodology and Multiplier Configuration')}
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

export default StockoutWarnings;
