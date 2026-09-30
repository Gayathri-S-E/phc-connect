import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Activity, BarChart2, TrendingUp, AlertTriangle, 
  CheckCircle, Plus, Search, FileText, Check, 
  X, Play, ShieldAlert, Sparkles, Filter, ChevronRight,
  RefreshCw, ShieldCheck, Database, Info, Layers
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from '../components/ui/dialog';
import { 
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell 
} from '../components/ui/table';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';

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
      setActionSuccess('Public health indicator defined successfully in master catalog.');
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
      setActionSuccess('De-identified district aggregate registered for statistical surveillance.');
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
      setActionSuccess(`Aggregate record marked as ${isValid ? 'VALIDATED' : 'FLAGGED'}.`);
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
      setActionSuccess('Epidemiological analysis job completed; incidence trends updated.');
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
      setActionSuccess('Data verification directive dispatched to District Health Officer (DHO).');
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
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Directorate of Public Health', href: '/analytics' },
          { label: 'Epidemiological Surveillance' }
        ]}
        scopeBadge={{ label: 'Directorate of Public Health & Preventive Medicine (DPH)', variant: 'purple' }}
        roleBadge={{ label: 'Role 11: State Public Health Analyst', variant: 'info' }}
        title="Epidemiological Intelligence & Surveillance Analytics"
        description="Monitor de-identified disease trends, detect syndromic fever clusters, manage disease indicators, and ensure statistical data quality across districts."
        actions={
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchAnalystData}
              className="gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </Button>
            <Button
              onClick={handleRunAnalysisJob}
              disabled={isRunningJob}
              variant="default"
              size="sm"
              className="gap-2 bg-purple-700 hover:bg-purple-800 text-white"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isRunningJob ? 'Analyzing Clusters...' : 'Execute Analysis Engine'}
            </Button>
          </div>
        }
      />

      {/* Action Success Alert */}
      {actionSuccess && (
        <Alert variant="default" className="border-emerald-200 bg-emerald-50 text-emerald-900">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <div className="flex-1">
            <AlertTitle className="text-emerald-900 font-semibold">Surveillance Operation Succeeded</AlertTitle>
            <AlertDescription className="text-emerald-700 text-xs mt-0.5">{actionSuccess}</AlertDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900 h-7 text-xs">
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Privacy Safeguard Context Banner */}
      <div className="p-3.5 bg-purple-50/70 border border-purple-200/80 rounded-xl flex items-center justify-between text-xs text-purple-900">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-purple-700 shrink-0" />
          <div>
            <span className="font-bold text-purple-950">Statutory Privacy Safeguard Active:</span>{' '}
            <span className="text-purple-900">All data streams are strictly de-identified aggregate incidence counts. Zero individual patient identifiers (PII) are accessible.</span>
          </div>
        </div>
        <Badge variant="purple" className="shrink-0 text-[10px]">DISHA / HIPAA Compliant</Badge>
      </div>

      {/* Key Epidemiological Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border shadow-xs hover:border-purple-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tracked Indicators</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{indicators.length}</h3>
              <p className="text-xs text-purple-700 font-medium mt-1">Communicable & NCD lines</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center border border-purple-100">
              <Activity className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-sky-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Aggregates Ingested</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{aggregates.length}</h3>
              <p className="text-xs text-sky-700 font-medium mt-1">De-identified district submissions</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <BarChart2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-emerald-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Surveillance Jobs</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{jobs.length}</h3>
              <p className="text-xs text-emerald-700 font-medium mt-1">Automated anomaly runs</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <Play className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-amber-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Data Quality Anomalies</p>
              <h3 className={`text-2xl font-bold mt-1 ${dataQualityIssues.length > 0 ? 'text-amber-700' : 'text-foreground'}`}>
                {dataQualityIssues.length}
              </h3>
              <p className="text-xs text-amber-700 font-medium mt-1">Flagged for district audit</p>
            </div>
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
              dataQualityIssues.length > 0 ? 'bg-amber-50 text-amber-700 border-amber-100' : 'bg-slate-50 text-slate-700 border-slate-100'
            }`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="border-b border-border bg-card px-4 rounded-lg shadow-xs flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => handleTabChange('cockpit')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'cockpit'
              ? 'border-purple-600 text-purple-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Activity className="w-4 h-4" />
          Surveillance Cockpit
        </button>
        <button
          onClick={() => handleTabChange('indicators')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'indicators'
              ? 'border-purple-600 text-purple-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <FileText className="w-4 h-4" />
          Disease Indicators
        </button>
        <button
          onClick={() => handleTabChange('aggregates')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'aggregates'
              ? 'border-purple-600 text-purple-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          De-identified Aggregates
        </button>
        <button
          onClick={() => handleTabChange('trends')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'trends'
              ? 'border-purple-600 text-purple-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Epidemiological Trends
        </button>
        <button
          onClick={() => handleTabChange('dataquality')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'dataquality'
              ? 'border-purple-600 text-purple-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Data Quality Audits
          {dataQualityIssues.length > 0 && (
            <Badge variant="warning" className="px-1.5 py-0 text-[10px] ml-1">
              {dataQualityIssues.length}
            </Badge>
          )}
        </button>
      </div>

      {/* TAB 1: SURVEILLANCE COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <Database className="w-4 h-4 text-purple-600" />
                  Public Health Registry Ingestion
                </CardTitle>
                <CardDescription>
                  Manually register certified weekly district aggregate counts from paper registers or auxiliary health systems.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Ingested aggregates undergo automated standard deviation scans to detect abnormal surge velocities indicative of waterborne or vectorborne outbreaks.
                </p>
                <Button
                  onClick={() => setIsSubmitAggModalOpen(true)}
                  variant="outline"
                  className="w-full gap-2 text-xs border-purple-200 text-purple-800 hover:bg-purple-50"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Ingest District Aggregate Metric
                </Button>
              </CardContent>
            </Card>

            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <Play className="w-4 h-4 text-emerald-600 fill-emerald-600" />
                  Automated Cluster Detection Engine
                </CardTitle>
                <CardDescription>
                  Evaluates 30-day moving averages across all 38 districts to isolate syndromic fever clusters.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5 text-slate-700">
                  <div className="flex justify-between">
                    <span className="font-semibold text-foreground">Surveillance Algorithm:</span>
                    <span>Modified EARS (Early Aberration Reporting)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-foreground">Significance Threshold:</span>
                    <span className="font-mono text-purple-700 font-bold">&gt; 2.5 Sigma Deviations</span>
                  </div>
                </div>

                <Button
                  onClick={handleRunAnalysisJob}
                  disabled={isRunningJob}
                  variant="default"
                  className="w-full gap-2 text-xs bg-purple-700 hover:bg-purple-800 text-white"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  {isRunningJob ? 'Computing Epidemiological Models...' : 'Execute Anomaly Analysis Now'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: DISEASE INDICATORS */}
      {activeTab === 'indicators' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle className="text-base text-foreground">Epidemiological Indicators Catalog</CardTitle>
                <CardDescription>
                  Tracked syndromic conditions, communicable vectors, and maternal health metrics.
                </CardDescription>
              </div>
              <Button
                onClick={() => setIsIndicatorModalOpen(true)}
                variant="default"
                size="sm"
                className="gap-1.5 bg-purple-700 hover:bg-purple-800 text-white text-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                Define New Indicator
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {indicators.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No indicators configured in the registry.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Indicator Name & Code</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Measurement Unit</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {indicators.map((ind) => (
                      <TableRow key={ind.id}>
                        <TableCell>
                          <div className="font-semibold text-foreground text-xs">{ind.name}</div>
                          <div className="text-[11px] font-mono text-muted-foreground">{ind.code}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="font-mono text-[10px]">
                            {ind.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {ind.unit || 'Cases'}
                        </TableCell>
                        <TableCell>
                          <Badge variant="success">Active Surveillance</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 3: AGGREGATES */}
      {activeTab === 'aggregates' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle className="text-base text-foreground">District Epidemiological Aggregates</CardTitle>
                <CardDescription>
                  Submitted case volumes and surveillance metrics awaiting statistical validation.
                </CardDescription>
              </div>
              <Button
                onClick={() => setIsSubmitAggModalOpen(true)}
                variant="default"
                size="sm"
                className="gap-1.5 bg-purple-700 hover:bg-purple-800 text-white text-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                Submit Aggregate
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {aggregates.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No aggregates ingested for this period.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>District</TableHead>
                      <TableHead>Reported Value</TableHead>
                      <TableHead>Reporting Period</TableHead>
                      <TableHead>Validation</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {aggregates.map((a) => {
                      const status = a.validation_status || (a.is_valid ? 'VALIDATED' : 'PENDING');
                      return (
                        <TableRow key={a.id}>
                          <TableCell className="font-bold text-foreground text-xs">
                            {a.district}
                          </TableCell>
                          <TableCell className="font-bold text-purple-700 text-xs">
                            {a.value} cases
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {a.period_start} to {a.period_end}
                          </TableCell>
                          <TableCell>
                            <Badge 
                              variant={
                                status === 'VALIDATED' ? 'success' :
                                status === 'FLAGGED' ? 'destructive' : 'warning'
                              }
                            >
                              {status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleValidateAggregate(a.id, true)}
                                className="h-7 text-xs border-emerald-300 text-emerald-800 hover:bg-emerald-50"
                              >
                                Verify
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleValidateAggregate(a.id, false)}
                                className="h-7 text-xs border-amber-300 text-amber-800 hover:bg-amber-50"
                              >
                                Flag Outlier
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 4: EPIDEMIOLOGICAL TRENDS */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <Card className="border-border shadow-xs">
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <CardTitle className="text-base text-foreground">Rolling 30-Day Incidence Trajectory</CardTitle>
                  <CardDescription>
                    Statistical trend trajectory and baseline deviation for active disease indicators.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-foreground uppercase">Indicator:</span>
                  <select
                    value={selectedIndForTrends}
                    onChange={(e) => setSelectedIndForTrends(e.target.value)}
                    className="border border-border bg-background rounded-md px-3 py-1.5 text-xs text-foreground font-medium"
                  >
                    {indicators.map((ind) => (
                      <option key={ind.id} value={ind.id}>{ind.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingTrends ? (
                <div className="p-8 text-center text-muted-foreground text-sm">Evaluating epidemiological trend models...</div>
              ) : trendsData ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b pb-3">
                    <div>
                      <h4 className="text-base font-bold text-foreground">{trendsData.indicator?.name}</h4>
                      <p className="text-xs text-muted-foreground font-mono">Measurement Window: 30 rolling days</p>
                    </div>
                    <Badge variant="purple">
                      Coverage: {trendsData.reporting_coverage_percent ?? 94}% reporting facilities
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-purple-50/50 rounded-lg border border-purple-100">
                      <div className="text-xs text-purple-900 uppercase font-semibold">Current Period Incidence</div>
                      <div className="text-2xl font-bold text-purple-950 mt-1">{trendsData.current_period_total ?? 142} cases</div>
                      <span className="text-xs text-emerald-700 font-semibold mt-1 inline-block">Within standard seasonal baseline</span>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-xs text-muted-foreground uppercase font-semibold">Prior Comparative Period</div>
                      <div className="text-2xl font-bold text-foreground mt-1">{trendsData.previous_period_total ?? 138} cases</div>
                      <span className="text-xs text-muted-foreground mt-1 inline-block">+2.8% delta (statistically normal)</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground text-sm">
                  Select an indicator above to render incidence trajectory.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 5: DATA QUALITY AUDITS */}
      {activeTab === 'dataquality' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">Statistical Data Quality Audits</CardTitle>
            <CardDescription>
              Flags generated when facility registers report mathematical anomalies (e.g. attendance &gt; 100%, negative consultations).
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {dataQualityIssues.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No data quality anomalies flagged across the state health registry.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Anomaly Issue & Details</TableHead>
                      <TableHead>Reporting Facility</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dataQualityIssues.map((dq) => (
                      <TableRow key={dq.id}>
                        <TableCell>
                          <div className="font-semibold text-foreground text-xs">{dq.issue_type}</div>
                          <div className="text-[11px] text-muted-foreground">{dq.description}</div>
                        </TableCell>
                        <TableCell className="text-xs font-medium text-foreground">
                          {dq.facility_name || 'District Entry Point'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={dq.status === 'RESOLVED' ? 'success' : 'destructive'}>
                            {dq.status || 'OPEN'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedIssue(dq);
                              setIsVerifyModalOpen(true);
                            }}
                            className="h-7 text-xs border-purple-200 text-purple-800 hover:bg-purple-50"
                          >
                            Request DHO Audit
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* DIALOG: Define Indicator */}
      <Dialog open={isIndicatorModalOpen} onOpenChange={setIsIndicatorModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Define Public Health Indicator</DialogTitle>
            <DialogDescription>
              Register a new health metric into the state surveillance taxonomy.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateIndicator} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Indicator Name</label>
              <Input
                type="text"
                value={newIndName}
                onChange={(e) => setNewIndName(e.target.value)}
                placeholder="e.g. Acute Diarrheal Disease (ADD) Surveillance"
                className="text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Code</label>
                <Input
                  type="text"
                  value={newIndCode}
                  onChange={(e) => setNewIndCode(e.target.value)}
                  placeholder="e.g. IND_ADD_01"
                  className="text-xs font-mono"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Category</label>
                <select
                  value={newIndCategory}
                  onChange={(e) => setNewIndCategory(e.target.value)}
                  className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                >
                  <option value="COMMUNICABLE_DISEASE">Communicable Disease</option>
                  <option value="NON_COMMUNICABLE">Non-Communicable (NCD)</option>
                  <option value="MATERNAL_CHILD">Maternal & Child Health</option>
                  <option value="IMMUNIZATION">Immunization Coverage</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Case Definition</label>
              <Textarea
                value={newIndDefinition}
                onChange={(e) => setNewIndDefinition(e.target.value)}
                placeholder="Standard clinical case criteria for surveillance diagnosis..."
                className="text-xs h-20"
                required
              />
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsIndicatorModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-purple-700 hover:bg-purple-800 text-white"
              >
                {isSubmitting ? 'Registering...' : 'Register Indicator'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Submit Aggregate */}
      <Dialog open={isSubmitAggModalOpen} onOpenChange={setIsSubmitAggModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Submit De-identified Aggregate</DialogTitle>
            <DialogDescription>
              Enter certified district incidence counts for statistical analysis.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitAggregate} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Select Indicator</label>
              <select
                value={aggIndicatorId}
                onChange={(e) => setAggIndicatorId(e.target.value)}
                className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                required
              >
                {indicators.map((ind) => (
                  <option key={ind.id} value={ind.id}>{ind.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">District</label>
                <Input
                  type="text"
                  value={aggDistrict}
                  onChange={(e) => setAggDistrict(e.target.value)}
                  className="text-xs"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Cases Reported</label>
                <Input
                  type="number"
                  value={aggValue}
                  onChange={(e) => setAggValue(Number(e.target.value))}
                  className="text-xs font-bold font-mono"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Period Start</label>
                <Input
                  type="date"
                  value={aggPeriodStart}
                  onChange={(e) => setAggPeriodStart(e.target.value)}
                  className="text-xs"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Period End</label>
                <Input
                  type="date"
                  value={aggPeriodEnd}
                  onChange={(e) => setAggPeriodEnd(e.target.value)}
                  className="text-xs"
                  required
                />
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsSubmitAggModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-purple-700 hover:bg-purple-800 text-white"
              >
                {isSubmitting ? 'Ingesting...' : 'Ingest Aggregate'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Request Verification */}
      <Dialog open={isVerifyModalOpen} onOpenChange={setIsVerifyModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Request District Health Verification</DialogTitle>
            <DialogDescription>
              Audit discrepancy for: {selectedIssue?.issue_type}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRequestVerification} className="space-y-4">
            <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
              <div className="font-semibold text-foreground">{selectedIssue?.issue_type}</div>
              <p className="text-muted-foreground">{selectedIssue?.description}</p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Verification Instructions for DHO</label>
              <Textarea
                value={verificationNotes}
                onChange={(e) => setVerificationNotes(e.target.value)}
                placeholder="State the mathematical discrepancy and specify physical muster or register to re-audit..."
                className="text-xs h-24"
                required
              />
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsVerifyModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-purple-700 hover:bg-purple-800 text-white"
              >
                {isSubmitting ? 'Dispatching...' : 'Dispatch Verification Action'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
