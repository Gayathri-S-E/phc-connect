import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle, XCircle, Database, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';
import { StateView } from '../../components/common/StateView';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

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

const cell = (v: number | string | null | undefined) => (v === null || v === undefined ? '-' : String(v));

const COLS: [keyof SummaryRow, string][] = [
  ['state', 'State'],
  ['facilities', 'Facilities'],
  ['appointments', 'Appointments'],
  ['stockouts', 'Stockouts'],
  ['staff_present_days', 'Staff present days'],
  ['staff_assigned_days', 'Staff assigned days'],
  ['beds_total_days', 'Bed days total'],
  ['beds_occupied_days', 'Bed days occupied'],
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
        state="403"
        title={t('gsp.forbidden.title', 'Access Restricted')}
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

  const items: [keyof GoogleStatus, string][] = [
    ['gemini', t('gsp.svc.gemini', 'Gemini AI assistant')],
    ['voice_translate', t('gsp.svc.voice', 'Voice and translation')],
    ['maps', t('gsp.svc.maps', 'Google Maps (geocoding, driving time)')],
    ['service_account', t('gsp.svc.sa', 'Service account credentials')],
    ['bigquery', t('gsp.svc.bq', 'BigQuery analytics')],
    ['vertex_forecast', t('gsp.svc.vertex', 'Vertex AI forecasting')],
  ];

  const th: React.CSSProperties = { textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.8rem', whiteSpace: 'nowrap' };
  const td: React.CSSProperties = { padding: '0.5rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem' };
  const card: React.CSSProperties = { padding: '1.25rem', borderRadius: '14px' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{t('gsp.title', 'Google Cloud services')}</h2>

      <section className="glass-card" aria-labelledby="gsp-status" style={card}>
        <h3 id="gsp-status" style={{ marginTop: 0 }}>
          {t('gsp.status', 'Service status')}
        </h3>
        {statusLoading ? (
          <StateView state="loading" />
        ) : statusFail ? (
          <StateView state="error" message={failMsg(statusFail)} onRetry={() => void loadStatus()} />
        ) : (
          status && (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.5rem' }}>
              {items.map(([k, label]) => (
                <li key={k} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {status[k] ? <CheckCircle size={18} color="#059669" aria-hidden="true" /> : <XCircle size={18} color="#dc2626" aria-hidden="true" />}
                  <span>
                    {label}: <strong>{status[k] ? t('gsp.configured', 'Configured') : t('gsp.not_configured', 'Not configured')}</strong>
                  </span>
                </li>
              ))}
            </ul>
          )
        )}
      </section>

      <section className="glass-card" aria-labelledby="gsp-export" style={card}>
        <h3 id="gsp-export" style={{ marginTop: 0 }}>
          {t('gsp.export', 'BigQuery export')}
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          {t('gsp.export.desc', "Exports today's facility aggregates (counts only, no patient data) for your jurisdiction.")}
        </p>
        <button type="button" className="btn-primary" onClick={runExport} disabled={exporting} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={16} aria-hidden="true" />
          {exporting ? t('gsp.exporting', 'Exporting...') : t('gsp.export.run', "Export today's data")}
        </button>
        <div aria-live="polite" style={{ marginTop: '0.75rem' }}>
          {exportFail && (
            <div role="alert" style={{ color: '#b91c1c', fontSize: '0.9rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <span>{failMsg(exportFail)}</span>
              {exportFail.status !== 403 && exportFail.status !== 503 && (
                <button type="button" className="btn-secondary" onClick={runExport}>
                  {t('state.retry', 'Retry')}
                </button>
              )}
            </div>
          )}
          {exportResult && (
            <div style={{ fontSize: '0.9rem' }}>
              <strong>{t('gsp.export.done', 'Export complete.')}</strong> {exportResult.rows_exported} {t('gsp.rows', 'rows exported')} &middot;{' '}
              {t('gsp.date', 'date')} {exportResult.aggregate_date} &middot; {t('gsp.scope', 'scope')}: {exportResult.scope}
              <div style={{ color: 'var(--text-muted)' }}>
                {exportResult.beds_included ? t('gsp.beds.yes', 'Bed occupancy included.') : t('gsp.beds.no', 'Bed occupancy not included.')}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="glass-card" aria-labelledby="gsp-summary" style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 id="gsp-summary" style={{ margin: 0 }}>
            {t('gsp.summary', 'National summary (last 30 days)')}
          </h3>
          <button type="button" className="btn-secondary" onClick={() => void loadSummary()} disabled={summaryLoading} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            <RefreshCw size={14} aria-hidden="true" /> {t('gsp.refresh', 'Refresh')}
          </button>
        </div>
        <div style={{ marginTop: '0.75rem' }}>
          {summaryLoading ? (
            <StateView state="loading" />
          ) : summaryFail ? (
            summaryFail.status === 403 ? (
              <StateView state="403" message={failMsg(summaryFail)} />
            ) : (
              <StateView
                state="error"
                title={summaryFail.status === 503 ? t('gsp.err.unconfigured', 'Not configured') : undefined}
                message={failMsg(summaryFail)}
                onRetry={summaryFail.status === 503 ? undefined : () => void loadSummary()}
              />
            )
          ) : (
            summary &&
            (summary.rows.length === 0 ? (
              <StateView
                state="empty"
                title={t('gsp.summary.empty', 'No data yet')}
                message={t('gsp.summary.empty.msg', 'No aggregates exist for this period. Run an export first.')}
              />
            ) : (
              <>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {summary.date_from} to {summary.date_to} &middot; {summary.scope}
                </p>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <caption style={{ position: 'absolute', left: '-9999px' }}>{t('gsp.summary.caption', 'National summary by state')}</caption>
                    <thead>
                      <tr>
                        {COLS.map(([k, label]) => (
                          <th key={k} scope="col" style={th}>
                            {t(`gsp.col.${k}`, label)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {summary.rows.map((r, i) => (
                        <tr key={`${r.state ?? 'all'}-${i}`}>
                          {COLS.map(([k]) => (
                            <td key={k} style={td}>
                              {cell(r[k])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
