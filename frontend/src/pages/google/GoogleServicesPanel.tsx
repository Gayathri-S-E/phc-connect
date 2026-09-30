import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle, XCircle, Database, RefreshCw, Cloud, Cpu, MapPin, Radio, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { StateView } from '../../components/common/StateView';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '../../components/ui/table';

interface GoogleStatus {
  gemini: boolean;
  voice_translate: boolean;
  maps: boolean;
  service_account: boolean;
  bigquery: boolean;
  vertex_forecast: boolean;
}
interface ExportResult {
  aggregate_date: string;
  scope: string;
  rows_exported: number;
  beds_included: boolean;
  columns: string[];
}
interface SummaryRow {
  state?: string | null;
  facilities?: number | null;
  appointments?: number | null;
  stockouts?: number | null;
  staff_present_days?: number | null;
  staff_assigned_days?: number | null;
  beds_total_days?: number | null;
  beds_occupied_days?: number | null;
}
interface Summary {
  date_from: string;
  date_to: string;
  scope: string;
  rows: SummaryRow[];
  source: string;
}

type Fail = { status: number; message: string };

const cell = (v: number | string | null | undefined) => (v === null || v === undefined ? '—' : String(v));

const COLS: [keyof SummaryRow, string][] = [
  ['state', 'State'],
  ['facilities', 'Facilities'],
  ['appointments', 'Appointments'],
  ['stockouts', 'Stockouts'],
  ['staff_present_days', 'Staff Present Days'],
  ['staff_assigned_days', 'Staff Assigned Days'],
  ['beds_total_days', 'Bed Days Total'],
  ['beds_occupied_days', 'Bed Days Occupied'],
];

export default function GoogleServicesPanel() {
  const { t } = useLanguage();
  const { hasPermission } = useAuth();
  const allowed = hasPermission('governance.report.generate');

  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [statusFail, setStatusFail] = useState<Fail | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);
  const [exportFail, setExportFail] = useState<Fail | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [summaryFail, setSummaryFail] = useState<Fail | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    setStatusFail(null);
    const res = await api.get<GoogleStatus>('/google/status');
    if (res.error) setStatusFail({ status: res.error.status, message: res.error.detail });
    else setStatus(res.data);
    setStatusLoading(false);
  }, []);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryFail(null);
    const res = await api.get<Summary>('/google/bigquery/national-summary');
    if (res.error) setSummaryFail({ status: res.error.status, message: res.error.detail });
    else setSummary(res.data);
    setSummaryLoading(false);
  }, []);

  useEffect(() => {
    if (!allowed) return;
    void loadStatus();
    void loadSummary();
  }, [allowed, loadStatus, loadSummary]);

  const runExport = async () => {
    setExporting(true);
    setExportFail(null);
    setExportResult(null);
    const res = await api.post<ExportResult>('/google/bigquery/export', {});
    if (res.error) {
      setExportFail({ status: res.error.status, message: res.error.detail });
    } else {
      setExportResult(res.data);
      void loadSummary();
    }
    setExporting(false);
  };

  if (!allowed) {
    return (
      <StateView
        type="403"
        message={t('gsp.forbidden.msg', 'Google Cloud services are available to governance and administrator users only.')}
      />
    );
  }

  const failMsg = (f: Fail) =>
    f.status === 503
      ? t('gsp.err.503', 'BigQuery is not configured on this server, so this action is unavailable.')
      : f.status === 403
        ? t('gsp.err.403', 'Your account does not have permission for this action.')
        : f.message;

  const items: [keyof GoogleStatus, string, string][] = [
    ['gemini', t('gsp.svc.gemini', 'Gemini AI Assistant'), 'Clinical reasoning & trilingual assistance'],
    ['voice_translate', t('gsp.svc.voice', 'Speech-to-Text & Translation'), 'Tamil, Hindi & English speech recognition'],
    ['maps', t('gsp.svc.maps', 'Google Maps & Routes'), 'Facility geocoding & road transit calculations'],
    ['service_account', t('gsp.svc.sa', 'Service Account IAM'), 'GCP authentication and credential keys'],
    ['bigquery', t('gsp.svc.bq', 'BigQuery Analytics'), 'Serverless epidemiological telemetry data warehouse'],
    ['vertex_forecast', t('gsp.svc.vertex', 'Vertex AI Forecasting'), 'Machine learning surge prediction models'],
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Cloud Infrastructure', href: '/governance' },
          { label: 'Google Cloud Services' }
        ]}
        scopeBadge={{ label: 'Google Cloud Platform (GCP)', variant: 'sky' }}
        roleBadge={{ label: 'Cloud Governance Tier', variant: 'outline' }}
        title={t('gsp.title', 'Google Cloud Services & BigQuery Analytics')}
        description="Unified health telemetry pipeline connecting primary health centers with BigQuery data warehousing, Vertex AI forecasting, and Maps routing."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => { void loadStatus(); void loadSummary(); }}
            disabled={statusLoading || summaryLoading}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${statusLoading || summaryLoading ? 'animate-spin' : ''}`} />
            {t('gsp.refresh', 'Refresh All Services')}
          </Button>
        }
      />

      {/* Service Status Matrix */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-foreground font-bold flex items-center gap-2">
            <Cloud className="w-4 h-4 text-sky-600" />
            {t('gsp.status', 'Connected Service Status')}
          </CardTitle>
          <CardDescription className="text-xs">
            Operational status of Google Cloud integration modules.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {statusLoading ? (
            <StateView type="loading" message="Loading Google services..." />
          ) : statusFail ? (
            <StateView type="error" message={failMsg(statusFail)} onRetry={() => void loadStatus()} />
          ) : (
            status && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {items.map(([k, label, desc]) => {
                  const isReady = status[k];
                  return (
                    <div key={k} className="p-3 bg-muted/40 rounded-lg border border-border flex items-start gap-3">
                      {isReady ? (
                        <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                      )}
                      <div className="min-w-0">
                        <div className="font-semibold text-foreground text-xs">{label}</div>
                        <div className="text-[11px] text-muted-foreground mt-0.5">{desc}</div>
                        <Badge variant={isReady ? 'success' : 'outline'} className="text-[10px] mt-2">
                          {isReady ? t('gsp.configured', 'Connected') : t('gsp.not_configured', 'Not Configured')}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          )}
        </CardContent>
      </Card>

      {/* BigQuery Export Card */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle className="text-base text-foreground font-bold flex items-center gap-2">
                <Database className="w-4 h-4 text-teal-600" />
                {t('gsp.export', 'BigQuery Health Telemetry Export')}
              </CardTitle>
              <CardDescription className="text-xs">
                {t('gsp.export.desc', "Exports today's facility aggregates (counts only, zero patient identifiers) for your jurisdiction.")}
              </CardDescription>
            </div>
            <Button
              type="button"
              variant="teal"
              size="sm"
              onClick={runExport}
              disabled={exporting}
              className="gap-2 text-xs font-semibold shrink-0"
            >
              <Database className="w-3.5 h-3.5" />
              {exporting ? t('gsp.exporting', 'Exporting...') : t('gsp.export.run', "Export Today's Telemetry")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div aria-live="polite">
            {exportFail && (
              <Alert variant="destructive" className="text-xs">
                <AlertDescription className="flex items-center justify-between">
                  <span>{failMsg(exportFail)}</span>
                  {exportFail.status !== 403 && exportFail.status !== 503 && (
                    <Button variant="outline" size="sm" onClick={runExport} className="h-6 text-[10px]">
                      {t('state.retry', 'Retry')}
                    </Button>
                  )}
                </AlertDescription>
              </Alert>
            )}

            {exportResult && (
              <Alert variant="default" className="border-emerald-200 bg-emerald-50 text-emerald-900 text-xs">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <div className="flex-1">
                  <AlertTitle className="font-semibold">{t('gsp.export.done', 'Export Complete')}</AlertTitle>
                  <AlertDescription className="text-[11px] mt-0.5 text-emerald-800">
                    {exportResult.rows_exported} {t('gsp.rows', 'rows exported')} &middot; {t('gsp.date', 'Date')}: {exportResult.aggregate_date} &middot; {t('gsp.scope', 'Scope')}: {exportResult.scope}
                    <div className="mt-0.5">
                      {exportResult.beds_included ? t('gsp.beds.yes', 'Bed occupancy figures included.') : t('gsp.beds.no', 'Bed occupancy not included.')}
                    </div>
                  </AlertDescription>
                </div>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* National Summary Table */}
      <Card className="border-border shadow-xs">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-base text-foreground font-bold">
                {t('gsp.summary', 'National Telemetry Roll-Up (Last 30 Days)')}
              </CardTitle>
              {summary && (
                <CardDescription className="text-xs">
                  {summary.date_from} to {summary.date_to} &middot; {summary.scope} &middot; Source: {summary.source}
                </CardDescription>
              )}
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void loadSummary()}
              disabled={summaryLoading}
              className="gap-1.5 text-xs h-8"
            >
              <RefreshCw className={`w-3 h-3 ${summaryLoading ? 'animate-spin' : ''}`} />
              {t('gsp.refresh', 'Refresh')}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {summaryLoading ? (
            <div className="p-8"><StateView type="loading" message="Loading national aggregates..." /></div>
          ) : summaryFail ? (
            <div className="p-4">
              <StateView
                type={summaryFail.status === 403 ? '403' : 'error'}
                message={failMsg(summaryFail)}
                onRetry={summaryFail.status === 503 ? undefined : () => void loadSummary()}
              />
            </div>
          ) : summary && summary.rows.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              {t('gsp.summary.empty.msg', 'No aggregates exist for this period. Run an export first.')}
            </div>
          ) : summary ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {COLS.map(([k, label]) => (
                      <TableHead key={k}>{t(`gsp.col.${k}`, label)}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.rows.map((r, i) => (
                    <TableRow key={`${r.state ?? 'all'}-${i}`}>
                      {COLS.map(([k]) => (
                        <TableCell key={k} className="text-xs">
                          {k === 'state' ? (
                            <span className="font-bold text-foreground">{r[k] || 'All States'}</span>
                          ) : (
                            <span className="font-mono text-muted-foreground">{cell(r[k])}</span>
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
