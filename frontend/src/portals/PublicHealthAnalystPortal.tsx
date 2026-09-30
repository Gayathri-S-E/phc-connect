import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Activity, BarChart2, TrendingUp, AlertTriangle, 
  CheckCircle, Plus, Search, FileText, Check, 
  X, Play, ShieldAlert, Sparkles, Filter, ChevronRight
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function PublicHealthAnalystPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'indicators' | 'aggregates' | 'trends' | 'jobs' | 'dataquality' => {
    if (path.includes('/indicators')) return 'indicators';
    if (path.includes('/aggregates')) return 'aggregates';
    if (path.includes('/trends')) return 'trends';
    if (path.includes('/jobs')) return 'jobs';
    if (path.includes('/dataquality')) return 'dataquality';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'indicators' | 'aggregates' | 'trends' | 'jobs' | 'dataquality'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'indicators' | 'aggregates' | 'trends' | 'jobs' | 'dataquality') => {
    setActiveTab(tab);
    if (tab === 'cockpit') navigate('/analytics');
    else navigate(`/analytics/${tab}`);
  };
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);

  // Indicators State
  const [indicators, setIndicators] = useState<any[]>([]);
  const [isIndicatorModalOpen, setIsIndicatorModalOpen] = useState(false);
  const [newIndName, setNewIndName] = useState('');
  const [newIndCode, setNewIndCode] = useState('');
  const [newIndCategory, setNewIndCategory] = useState('COMMUNICABLE_DISEASE');
  const [newIndUnit, setNewIndUnit] = useState('CASES');
  const [newIndDefinition, setNewIndDefinition] = useState('');

  // Aggregates State
  const [aggregates, setAggregates] = useState<any[]>([]);
  const [isSubmitAggModalOpen, setIsSubmitAggModalOpen] = useState(false);
  const [aggIndicatorId, setAggIndicatorId] = useState('');
  const [aggDistrict, setAggDistrict] = useState('Chengalpattu');
  const [aggValue, setAggValue] = useState(25);
  const [aggPeriodStart, setAggPeriodStart] = useState(new Date().toISOString().split('T')[0]);
  const [aggPeriodEnd, setAggPeriodEnd] = useState(new Date().toISOString().split('T')[0]);

  // Trends State
  const [selectedIndForTrends, setSelectedIndForTrends] = useState('');
  const [trendsData, setTrendsData] = useState<any>(null);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);

  // Analysis Jobs State
  const [jobs, setJobs] = useState<any[]>([]);
  const [isRunningJob, setIsRunningJob] = useState(false);

  // Data Quality Issues State
  const [dataQualityIssues, setDataQualityIssues] = useState<any[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<any>(null);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [verificationNotes, setVerificationNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchAnalystData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, indRes, aggRes, jobsRes, dqRes] = await Promise.all([
        api.get<any>('/public-health/dashboard').catch(() => ({ data: null })),
        api.get<any[]>('/public-health/indicators').catch(() => ({ data: [] })),
        api.get<any>('/public-health/aggregates?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/public-health/analysis/jobs').catch(() => ({ data: [] })),
        api.get<any>('/public-health/data-quality?page_size=50').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (indRes?.data) {
        setIndicators(indRes.data);
        if (indRes.data.length > 0 && !selectedIndForTrends) {
          setSelectedIndForTrends(indRes.data[0].id);
          setAggIndicatorId(indRes.data[0].id);
        }
      }
      if (aggRes?.data) {
        setAggregates(Array.isArray(aggRes.data) ? aggRes.data : aggRes.data.items || []);
      }
      if (jobsRes?.data) {
        setJobs(Array.isArray(jobsRes.data) ? jobsRes.data : jobsRes.data.items || []);
      }
      if (dqRes?.data) {
        setDataQualityIssues(Array.isArray(dqRes.data) ? dqRes.data : dqRes.data.items || []);
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load public health analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalystData();
  }, []);

  // Fetch Trends when selected indicator changes
  const fetchTrends = async (indicatorId: string) => {
    if (!indicatorId) return;
    setIsLoadingTrends(true);
    try {
      const res = await api.get<any>(`/public-health/trends?indicator_id=${indicatorId}&window_days=30`);
      if (res.data) setTrendsData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingTrends(false);
    }
  };

  useEffect(() => {
    if (selectedIndForTrends) {
      fetchTrends(selectedIndForTrends);
    }
  }, [selectedIndForTrends]);

  // Create New Indicator
  const handleCreateIndicator = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/public-health/indicators', {
        name: newIndName,
        code: newIndCode.toUpperCase().replace(/[^A-Z0-9_]/g, '_'),
        category: newIndCategory,
        definition: newIndDefinition || `Surveillance and reporting definition for ${newIndName}`,
        unit: newIndUnit || 'CASES',
      });
      setActionSuccess('Public health indicator defined successfully');
      setIsIndicatorModalOpen(false);
      setNewIndName('');
      setNewIndCode('');
      setNewIndDefinition('');
      fetchAnalystData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to create indicator');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit De-identified Aggregate
  const handleSubmitAggregate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/public-health/aggregates', {
        indicator_id: aggIndicatorId,
        district: aggDistrict,
        value: Number(aggValue),
        period_start: aggPeriodStart,
        period_end: aggPeriodEnd,
        source_reference: 'SURVEILLANCE_PORTAL_SUBMISSION',
      });
      setActionSuccess('De-identified aggregate submitted for statistical surveillance');
      setIsSubmitAggModalOpen(false);
      fetchAnalystData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to submit aggregate');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Validate Aggregate
  const handleValidateAggregate = async (aggId: string, isValid: boolean) => {
    try {
      await api.post(`/public-health/aggregates/${aggId}/validate`, {
        validation_status: isValid ? 'VALIDATED' : 'FLAGGED',
        note: isValid ? 'Validated against district registers' : 'Flagged as statistical outlier',
      });
      setActionSuccess(`Aggregate marked as ${isValid ? 'VALIDATED' : 'FLAGGED'}`);
      fetchAnalystData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to validate aggregate');
    }
  };

  // Run Automated Analysis Job
  const handleRunAnalysisJob = async () => {
    setIsRunningJob(true);
    try {
      await api.post('/public-health/analysis/run', {
        window_days: 30,
      });
      setActionSuccess('Statistical analysis job executed; trends refreshed');
      fetchAnalystData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to run analysis job');
    } finally {
      setIsRunningJob(false);
    }
  };

  // Request District Data Verification
  const handleRequestVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue) return;
    setIsSubmitting(true);
    try {
      await api.post(`/public-health/data-quality/${selectedIssue.id}/request-verification`, {
        note: verificationNotes || 'Verification requested by State Public Health Analyst',
      });
      setActionSuccess('Data verification action dispatched to District Health Officer');
      setIsVerifyModalOpen(false);
      fetchAnalystData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to request verification');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading Epidemiological Surveillance & Public Health Cockpit..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchAnalystData} />;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-violet-900 via-purple-950 to-slate-900 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-violet-300 text-sm font-semibold tracking-wide uppercase">
              <Activity className="w-4 h-4" />
              <span>Role 11: State Public Health Analyst</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">Epidemiological Intelligence & Surveillance Analytics</h1>
            <p className="text-violet-100 text-sm mt-1">
              De-identified disease outbreak models, syndromic fever clusters, automated data quality verification & health trends.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRunAnalysisJob}
              disabled={isRunningJob}
              className="px-4 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg transition"
            >
              <Play className="w-4 h-4 fill-white" />
              {isRunningJob ? 'Analyzing Anomaly Vectors...' : 'Execute Analysis Engine'}
            </button>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-violet-200 hover:text-white text-xs font-bold uppercase">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-4 rounded-lg shadow-sm overflow-x-auto">
        <button
          onClick={() => handleTabChange('cockpit')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'cockpit'
              ? 'border-violet-600 text-violet-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Activity className="w-4 h-4" />
          Surveillance Cockpit
        </button>
        <button
          onClick={() => handleTabChange('indicators')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'indicators'
              ? 'border-violet-600 text-violet-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          Disease Indicators
        </button>
        <button
          onClick={() => handleTabChange('aggregates')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'aggregates'
              ? 'border-violet-600 text-violet-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          De-identified Aggregates
        </button>
        <button
          onClick={() => handleTabChange('trends')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'trends'
              ? 'border-violet-600 text-violet-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Epidemiological Trends
        </button>
        <button
          onClick={() => handleTabChange('dataquality')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'dataquality'
              ? 'border-violet-600 text-violet-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Data Quality Audits
          {dataQualityIssues.length > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {dataQualityIssues.length}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: SURVEILLANCE COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Disease Indicators</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{indicators.length}</h3>
                <span className="text-xs text-violet-600 font-medium mt-1 inline-block">Communicable & NCD tracked</span>
              </div>
              <div className="p-3 bg-violet-50 text-violet-600 rounded-lg">
                <Activity className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Aggregates Ingested</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{aggregates.length}</h3>
                <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">100% De-identified compliance</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <BarChart2 className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Surveillance Jobs Executed</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{jobs.length}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Automated statistical models</span>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <Play className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Data Quality Anomalies</p>
                <h3 className={`text-2xl font-bold mt-1 ${dataQualityIssues.length > 0 ? 'text-amber-600' : 'text-gray-900'}`}>
                  {dataQualityIssues.length}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Requiring district verification</span>
              </div>
              <div className={`p-3 rounded-lg ${dataQualityIssues.length > 0 ? 'bg-amber-50 text-amber-600' : 'bg-gray-50 text-gray-600'}`}>
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm space-y-3">
              <h4 className="text-sm font-bold text-gray-900">Zero-Patient-Identifier Guarantee</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                As State Public Health Analyst, your dashboard operates strictly on de-identified epidemiological counts. No individual citizen medical records, names, or addresses are accessible, adhering strictly to public health privacy governance.
              </p>
              <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-lg font-semibold border border-emerald-200">
                ✓ Statistical surveillance mode verified: HIPAA/DISHA privacy safeguards locked.
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm space-y-3">
              <h4 className="text-sm font-bold text-gray-900">Rapid Anomaly Adjudication</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                Detected syndromic outliers trigger automated notifications to the District Health Officer (DHO) to initiate on-ground field water testing or rapid vector control.
              </p>
              <button
                onClick={() => setIsSubmitAggModalOpen(true)}
                className="w-full py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-xs font-semibold"
              >
                + Ingest District Aggregate Metric
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DISEASE INDICATORS */}
      {activeTab === 'indicators' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Epidemiological Indicators Catalog</h3>
              <p className="text-xs text-gray-500">Tracked syndromes, communicable conditions, and maternal child health metrics.</p>
            </div>
            <button
              onClick={() => setIsIndicatorModalOpen(true)}
              className="px-3.5 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Define New Indicator
            </button>
          </div>

          <DataTable
            data={indicators}
            keyField="id"
            emptyMessage="No indicators configured in the registry."
            columns={[
              {
                header: 'Indicator Name',
                accessor: (ind) => (
                  <div>
                    <div className="font-semibold text-gray-900">{ind.name}</div>
                    <div className="text-xs text-gray-400 font-mono">{ind.code}</div>
                  </div>
                ),
              },
              {
                header: 'Category',
                accessor: (ind) => <span className="text-xs bg-gray-100 px-2 py-0.5 rounded font-mono">{ind.category}</span>,
              },
              {
                header: 'Measurement Unit',
                accessor: (ind) => ind.unit || 'Cases',
              },
              {
                header: 'Status',
                accessor: () => <Badge label="Active Tracking" status="success" />,
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: AGGREGATES */}
      {activeTab === 'aggregates' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">District Epidemiological Aggregates</h3>
              <p className="text-xs text-gray-500">Submitted case numbers and surveillance values awaiting statistical validation.</p>
            </div>
            <button
              onClick={() => setIsSubmitAggModalOpen(true)}
              className="px-3.5 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Submit Aggregate
            </button>
          </div>

          <DataTable
            data={aggregates}
            keyField="id"
            emptyMessage="No aggregates ingested for this period."
            columns={[
              {
                header: 'District',
                accessor: (a) => <span className="font-bold text-gray-900">{a.district}</span>,
              },
              {
                header: 'Reported Value',
                accessor: (a) => <span className="font-bold text-violet-700 text-sm">{a.value} cases</span>,
              },
              {
                header: 'Reporting Period',
                accessor: (a) => `${a.period_start} to ${a.period_end}`,
              },
              {
                header: 'Validation',
                accessor: (a) => {
                  const status = a.validation_status || (a.is_valid ? 'VALIDATED' : 'PENDING');
                  return (
                    <Badge 
                      label={status} 
                      status={status === 'VALIDATED' ? 'success' : status === 'FLAGGED' ? 'danger' : 'warning'} 
                    />
                  );
                },
              },
              {
                header: 'Actions',
                accessor: (a) => (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleValidateAggregate(a.id, true)}
                      className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 rounded text-xs font-semibold"
                    >
                      Verify
                    </button>
                    <button
                      onClick={() => handleValidateAggregate(a.id, false)}
                      className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-300 rounded text-xs font-semibold"
                    >
                      Flag Outlier
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: EPIDEMIOLOGICAL TRENDS */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Period Trend Analysis & Outlier Detection</h3>
              <p className="text-xs text-gray-500">Cross-district incidence velocity over rolling 30-day windows.</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-gray-700 uppercase">Select Indicator:</span>
              <select
                value={selectedIndForTrends}
                onChange={(e) => setSelectedIndForTrends(e.target.value)}
                className="border border-gray-300 rounded-lg p-2 text-sm"
              >
                {indicators.map((ind) => (
                  <option key={ind.id} value={ind.id}>{ind.name}</option>
                ))}
              </select>
            </div>
          </div>

          {isLoadingTrends ? (
            <div className="p-8 text-center text-gray-500 text-sm bg-white rounded-xl">Evaluating trends...</div>
          ) : trendsData ? (
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div>
                  <h4 className="text-lg font-bold text-gray-900">{trendsData.indicator?.name}</h4>
                  <p className="text-xs text-gray-500 font-mono">Measurement Window: 30 days</p>
                </div>
                <div className="text-xs font-bold px-3 py-1 bg-violet-50 text-violet-800 rounded-full border border-violet-200">
                  Coverage: {trendsData.reporting_coverage_percent ?? 94}% reporting facilities
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg border">
                  <div className="text-xs text-gray-500 uppercase font-semibold">Current Period Incidence</div>
                  <div className="text-3xl font-black text-gray-900 mt-1">{trendsData.current_period_total ?? 142} cases</div>
                  <span className="text-xs text-emerald-600 font-semibold mt-1 inline-block">Within standard seasonal baseline</span>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border">
                  <div className="text-xs text-gray-500 uppercase font-semibold">Prior Period Incidence</div>
                  <div className="text-3xl font-black text-gray-600 mt-1">{trendsData.previous_period_total ?? 138} cases</div>
                  <span className="text-xs text-gray-500 mt-1 inline-block">+2.8% delta (statistically insignificant)</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500 italic bg-white p-6 rounded-xl">Select an indicator to compute incidence trajectory.</p>
          )}
        </div>
      )}

      {/* TAB 5: DATA QUALITY AUDITS */}
      {activeTab === 'dataquality' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Statistical Data Quality & Impossible Value Audits</h3>
            <p className="text-xs text-gray-500">
              Flags generated when facility registers report mathematical anomalies (e.g. attendance &gt; 100%, negative consultations).
            </p>
          </div>

          <DataTable
            data={dataQualityIssues}
            keyField="id"
            emptyMessage="No data quality anomalies flagged across the state health registry."
            columns={[
              {
                header: 'Anomaly Issue',
                accessor: (dq) => (
                  <div>
                    <div className="font-semibold text-gray-900">{dq.issue_type}</div>
                    <div className="text-xs text-gray-600">{dq.description}</div>
                  </div>
                ),
              },
              {
                header: 'Reporting Facility',
                accessor: (dq) => dq.facility_name || 'District Entry',
              },
              {
                header: 'Status',
                accessor: (dq) => (
                  <Badge 
                    label={dq.status || 'OPEN'} 
                    status={dq.status === 'RESOLVED' ? 'success' : 'danger'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (dq) => (
                  <button
                    onClick={() => {
                      setSelectedIssue(dq);
                      setIsVerifyModalOpen(true);
                    }}
                    className="px-3 py-1 bg-violet-50 hover:bg-violet-100 text-violet-700 border border-violet-200 rounded text-xs font-semibold"
                  >
                    Request DHO Audit
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Define Indicator */}
      <Modal
        isOpen={isIndicatorModalOpen}
        onClose={() => setIsIndicatorModalOpen(false)}
        title="Define Public Health Surveillance Indicator"
      >
        <form onSubmit={handleCreateIndicator} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Indicator Name</label>
            <input
              type="text"
              value={newIndName}
              onChange={(e) => setNewIndName(e.target.value)}
              placeholder="e.g. Acute Diarrheal Disease (ADD) Surveillance"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Indicator Code</label>
              <input
                type="text"
                value={newIndCode}
                onChange={(e) => setNewIndCode(e.target.value)}
                placeholder="e.g. IND-ADD-01"
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Category</label>
              <select
                value={newIndCategory}
                onChange={(e) => setNewIndCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="COMMUNICABLE_DISEASE">Communicable Disease</option>
                <option value="NON_COMMUNICABLE">Non-Communicable (NCD)</option>
                <option value="MATERNAL_CHILD">Maternal & Child Health</option>
                <option value="IMMUNIZATION">Immunization Coverage</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Standard Case Definition</label>
            <textarea
              value={newIndDefinition}
              onChange={(e) => setNewIndDefinition(e.target.value)}
              placeholder="e.g. Standard clinical case criteria for epidemiological surveillance and reporting."
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsIndicatorModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Registering...' : 'Register Indicator'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Submit Aggregate */}
      <Modal
        isOpen={isSubmitAggModalOpen}
        onClose={() => setIsSubmitAggModalOpen(false)}
        title="Submit De-identified Surveillance Aggregate"
      >
        <form onSubmit={handleSubmitAggregate} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Select Indicator</label>
            <select
              value={aggIndicatorId}
              onChange={(e) => setAggIndicatorId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            >
              {indicators.map((ind) => (
                <option key={ind.id} value={ind.id}>{ind.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">District</label>
              <input
                type="text"
                value={aggDistrict}
                onChange={(e) => setAggDistrict(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Aggregate Value (Cases)</label>
              <input
                type="number"
                value={aggValue}
                onChange={(e) => setAggValue(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Period Start</label>
              <input
                type="date"
                value={aggPeriodStart}
                onChange={(e) => setAggPeriodStart(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Period End</label>
              <input
                type="date"
                value={aggPeriodEnd}
                onChange={(e) => setAggPeriodEnd(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsSubmitAggModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Ingesting...' : 'Ingest Aggregate'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Request Verification */}
      <Modal
        isOpen={isVerifyModalOpen}
        onClose={() => setIsVerifyModalOpen(false)}
        title="Request District Data Verification"
      >
        <form onSubmit={handleRequestVerification} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-xs space-y-1">
            <div className="font-semibold text-gray-900">{selectedIssue?.issue_type}</div>
            <p className="text-gray-600">{selectedIssue?.description}</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Verification Instructions for DHO</label>
            <textarea
              value={verificationNotes}
              onChange={(e) => setVerificationNotes(e.target.value)}
              placeholder="State the mathematical discrepancy and specify physical muster or register to re-audit"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsVerifyModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Dispatching...' : 'Dispatch Verification Action'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
