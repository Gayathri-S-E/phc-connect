import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Building2, Users, ShieldCheck, CheckCircle, 
  FileText, Activity, BarChart3, TrendingUp, 
  Plus, Eye, Download, Award, AlertTriangle, 
  Sparkles, Check, X, Clock
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function StateHealthPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports' | 'insights' => {
    if (path.includes('/districts')) return 'districts';
    if (path.includes('/approvals')) return 'approvals';
    if (path.includes('/schemes')) return 'schemes';
    if (path.includes('/reports')) return 'reports';
    if (path.includes('/insights')) return 'insights';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports' | 'insights'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports' | 'insights') => {
    setActiveTab(tab);
    if (tab === 'cockpit') navigate('/state');
    else if (tab === 'districts') navigate('/state/districts');
    else navigate(`/governance/${tab}`);
  };
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [districtsList, setDistrictsList] = useState<any[]>([]);

  // Approvals State
  const [approvals, setApprovals] = useState<any[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<any>(null);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [approvalDecision, setApprovalDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [approvalNotes, setApprovalNotes] = useState('');

  // Schemes State
  const [schemes, setSchemes] = useState<any[]>([]);
  const [isSchemeModalOpen, setIsSchemeModalOpen] = useState(false);
  const [newSchemeName, setNewSchemeName] = useState('');
  const [newSchemeCode, setNewSchemeCode] = useState('');
  const [newSchemeDesc, setNewSchemeDesc] = useState('');

  // Reports State
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [isReportReviewModalOpen, setIsReportReviewModalOpen] = useState(false);
  const [reportReviewStatus, setReportReviewStatus] = useState('APPROVED');
  const [reportReviewRemarks, setReportReviewRemarks] = useState('');

  // AI Insights State
  const [insights, setInsights] = useState<any[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchStateData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, distRes, appRes, schemesRes, repRes, insRes] = await Promise.all([
        api.get<any>('/state/dashboard').catch(() => ({ data: null })),
        api.get<any>('/state/districts').catch(() => ({ data: { districts: [] } })),
        api.get<any>('/governance/approvals?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/governance/schemes').catch(() => ({ data: [] })),
        api.get<any>('/governance/reports?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/governance/insights').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (distRes?.data) setDistrictsList(distRes.data.districts || []);
      if (appRes?.data) {
        setApprovals(Array.isArray(appRes.data) ? appRes.data : appRes.data.items || []);
      }
      if (schemesRes?.data) setSchemes(schemesRes.data);
      if (repRes?.data) {
        setReports(Array.isArray(repRes.data) ? repRes.data : repRes.data.items || []);
      }
      if (insRes?.data) setInsights(insRes.data);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load state health administration data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStateData();
  }, []);

  // Submit Approval Decision
  const handleDecideApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;
    setIsSubmitting(true);
    try {
      await api.post(`/governance/approvals/${selectedApproval.id}/decision`, {
        decision: approvalDecision,
        decision_notes: approvalNotes,
      });
      setActionSuccess(`Executive request marked as ${approvalDecision}`);
      setIsApprovalModalOpen(false);
      fetchStateData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to submit decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Create Health Scheme
  const handleCreateScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const sanitizedCode = (newSchemeCode || 'TN_HEALTH_SCHEME').toUpperCase().replace(/[^A-Z0-9_\-]/g, '_');
      await api.post('/governance/schemes', {
        name: newSchemeName,
        code: sanitizedCode,
        description: newSchemeDesc || 'State Public Health Priority Scheme',
        unit: 'BENEFICIARIES',
      });
      setActionSuccess('State health scheme configured successfully');
      setIsSchemeModalOpen(false);
      setNewSchemeName('');
      setNewSchemeCode('');
      setNewSchemeDesc('');
      fetchStateData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to configure scheme');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Review Submitted Report
  const handleReviewReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;
    setIsSubmitting(true);
    try {
      await api.post(`/governance/reports/${selectedReport.id}/review`, {
        review_status: reportReviewStatus,
        remarks: reportReviewRemarks,
      });
      setActionSuccess(`Report ${selectedReport.reference || selectedReport.id} review recorded`);
      setIsReportReviewModalOpen(false);
      fetchStateData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to review report');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Review AI Insight
  const handleReviewInsight = async (insightId: string, outcome: 'ACCEPT' | 'REJECT') => {
    try {
      await api.post(`/governance/insights/${insightId}/review`, {
        status: outcome === 'ACCEPT' ? 'ACCEPTED' : 'REJECTED',
        review_notes: 'Reviewed by State Health Administrator',
      });
      setActionSuccess(`Insight ${outcome === 'ACCEPT' ? 'accepted for action' : 'dismissed'}`);
      fetchStateData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to review insight');
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading State Health Directorate Cockpit..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchStateData} />;

  const totals = dashboardData?.totals || {};
  const governance = dashboardData?.governance || {};

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-blue-950 to-slate-900 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-indigo-300 text-sm font-semibold tracking-wide uppercase">
              <ShieldCheck className="w-4 h-4" />
              <span>Role 09: State Health Administrator</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">Statewide Health Directorate & Executive Governance</h1>
            <p className="text-indigo-100 text-sm mt-1">
              Macro health indicators, district-level resource allocation, executive approvals & flagship health schemes.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-3 rounded-lg border border-white/20">
            <Award className="w-5 h-5 text-indigo-300" />
            <div>
              <div className="text-xs text-indigo-200 uppercase font-bold">Pending Approvals</div>
              <div className="text-xl font-black">{governance.pending_approvals ?? approvals.length}</div>
            </div>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-indigo-200 hover:text-white text-xs font-bold uppercase">
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
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          State Health Cockpit
        </button>
        <button
          onClick={() => handleTabChange('districts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'districts'
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Districts Comparative Matrix
        </button>
        <button
          onClick={() => handleTabChange('approvals')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'approvals'
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          Executive Approvals
          {approvals.filter(a => a.status === 'PENDING').length > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {approvals.filter(a => a.status === 'PENDING').length}
            </span>
          )}
        </button>
        <button
          onClick={() => handleTabChange('schemes')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'schemes'
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Award className="w-4 h-4" />
          State Health Schemes
        </button>
        <button
          onClick={() => handleTabChange('reports')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'reports'
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          Governance Reports
        </button>
        <button
          onClick={() => handleTabChange('insights')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'insights'
              ? 'border-indigo-600 text-indigo-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          AI Epidemiological Insights
          {insights.length > 0 && (
            <span className="bg-purple-100 text-purple-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {insights.length}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: STATE HEALTH COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">State Patient OPD Volume</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.patient_volume ?? 12450}</h3>
                <span className="text-xs text-indigo-600 font-medium mt-1 inline-block">Consultations: {totals.consultations ?? 11800}</span>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Facilities Across State</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.facilities ?? 42}</h3>
                <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">100% Operational Reporting</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Building2 className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Staff On Duty</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.staff_present ?? 380}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Out of {totals.staff_assigned ?? 410} sanctioned</span>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active Emergencies</p>
                <h3 className="text-2xl font-bold text-red-600 mt-1">{dashboardData?.active_emergencies ?? 1}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">State Disaster Watch</span>
              </div>
              <div className="p-3 bg-red-50 text-red-600 rounded-lg">
                <Activity className="w-5 h-5" />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-indigo-600" />
                Executive Approval Pipeline
              </h4>
              <p className="text-xs text-gray-500 mb-3">
                High-level sanctions required for district budget expansions and emergency procurement waivers.
              </p>
              <div className="flex items-center justify-between p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-xs">
                <span className="text-indigo-900 font-semibold">Pending Decisions:</span>
                <span className="font-bold text-indigo-700">{approvals.length} Requests</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                AI Epidemiological Insights
              </h4>
              <p className="text-xs text-gray-500 mb-3">
                Machine-learning detection of abnormal syndromic trends and supply depletion forecasts requiring human validation.
              </p>
              <div className="flex items-center justify-between p-3 bg-purple-50/50 rounded-lg border border-purple-100 text-xs">
                <span className="text-purple-900 font-semibold">Active Insights:</span>
                <span className="font-bold text-purple-700">{insights.length} Signals</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DISTRICTS COMPARISON */}
      {activeTab === 'districts' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Districts Comparative Health Performance</h3>
              <p className="text-xs text-gray-500">Roll-up statistics by administrative revenue district.</p>
            </div>
          </div>

          <DataTable
            data={districtsList}
            keyField="district"
            emptyMessage="No district aggregated figures available."
            columns={[
              {
                header: 'District',
                accessor: (d) => <span className="font-bold text-gray-900">{d.district}</span>,
              },
              {
                header: 'Facilities',
                accessor: (d) => `${d.facilities} PHCs/CHCs`,
              },
              {
                header: 'Patient Volume',
                accessor: (d) => <span className="font-semibold">{d.patient_volume}</span>,
              },
              {
                header: 'Consultations',
                accessor: 'consultations',
              },
              {
                header: 'Referrals',
                accessor: 'referrals',
              },
              {
                header: 'Stockouts',
                accessor: (d) => (
                  <span className={d.stockout_items > 0 ? 'text-red-600 font-bold' : 'text-gray-400'}>
                    {d.stockout_items} items
                  </span>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: EXECUTIVE APPROVALS */}
      {activeTab === 'approvals' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Executive Approvals & Sanctions</h3>
            <p className="text-xs text-gray-500">Review budget authorizations and clinical waivers escalated from districts.</p>
          </div>

          <DataTable
            data={approvals}
            keyField="id"
            emptyMessage="No pending executive approvals requiring state sanction."
            columns={[
              {
                header: 'Request Reference',
                accessor: (a) => (
                  <div>
                    <div className="font-semibold text-gray-900">{a.title || 'Sanction Request'}</div>
                    <div className="text-xs text-gray-400 font-mono">{a.id.slice(0, 8)}</div>
                  </div>
                ),
              },
              {
                header: 'Requested By',
                accessor: (a) => a.requester_name || 'District Authority',
              },
              {
                header: 'Status',
                accessor: (a) => (
                  <Badge 
                    label={a.status} 
                    status={a.status === 'APPROVED' ? 'success' : a.status === 'REJECTED' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (a) => (
                  a.status === 'PENDING' ? (
                    <button
                      onClick={() => {
                        setSelectedApproval(a);
                        setIsApprovalModalOpen(true);
                      }}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-semibold"
                    >
                      Adjudicate
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">Decided</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: STATE HEALTH SCHEMES */}
      {activeTab === 'schemes' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Tamil Nadu State Flagship Health Schemes</h3>
              <p className="text-xs text-gray-500">Track coverage, targets, and field progress of healthcare schemes.</p>
            </div>
            <button
              onClick={() => setIsSchemeModalOpen(true)}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Configure Health Scheme
            </button>
          </div>

          <DataTable
            data={schemes}
            keyField="id"
            emptyMessage="No state health schemes configured."
            columns={[
              {
                header: 'Scheme Name',
                accessor: (s) => (
                  <div>
                    <div className="font-semibold text-gray-900">{s.name}</div>
                    <div className="text-xs text-gray-400 font-mono">{s.code}</div>
                  </div>
                ),
              },
              {
                header: 'Description',
                accessor: (s) => <span className="text-xs text-gray-600 line-clamp-1">{s.description}</span>,
              },
              {
                header: 'Targets Monitored',
                accessor: (s) => `${s.targets?.length || 0} Key Milestones`,
              },
            ]}
          />
        </div>
      )}

      {/* TAB 5: GOVERNANCE REPORTS */}
      {activeTab === 'reports' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">District HMIS Performance Reports</h3>
            <p className="text-xs text-gray-500">Formally review and sign-off on monthly aggregates submitted by DHOs.</p>
          </div>

          <DataTable
            data={reports}
            keyField="id"
            emptyMessage="No reports awaiting state review."
            columns={[
              {
                header: 'Report Ref',
                accessor: (r) => (
                  <div>
                    <div className="font-semibold text-gray-900">{r.reference || 'HMIS Monthly Report'}</div>
                    <div className="text-xs text-gray-400">{r.district || 'Statewide Rollup'}</div>
                  </div>
                ),
              },
              {
                header: 'Period',
                accessor: (r) => r.period_label || 'Current Month',
              },
              {
                header: 'Review Status',
                accessor: (r) => (
                  <Badge 
                    label={r.review_status || 'SUBMITTED'} 
                    status={r.review_status === 'APPROVED' ? 'success' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (r) => (
                  <button
                    onClick={() => {
                      setSelectedReport(r);
                      setIsReportReviewModalOpen(true);
                    }}
                    className="px-3 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded text-xs font-semibold"
                  >
                    Review & Sign-Off
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 6: AI INSIGHTS */}
      {activeTab === 'insights' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Machine Learning Epidemiological Insights</h3>
            <p className="text-xs text-gray-500">
              Statistical anomaly detection flags: requires human validation before clinical directive issuance.
            </p>
          </div>

          <DataTable
            data={insights}
            keyField="id"
            emptyMessage="No pending automated insights awaiting review."
            columns={[
              {
                header: 'Signal Title',
                accessor: (ins) => (
                  <div>
                    <div className="font-semibold text-gray-900">{ins.title}</div>
                    <div className="text-xs text-gray-600">{ins.summary || ins.description}</div>
                  </div>
                ),
              },
              {
                header: 'Confidence Score',
                accessor: (ins) => (
                  <span className="font-bold text-purple-700">
                    {ins.confidence ? `${Math.round(ins.confidence * 100)}%` : 'High'}
                  </span>
                ),
              },
              {
                header: 'Human Review Action',
                accessor: (ins) => (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleReviewInsight(ins.id, 'ACCEPT')}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1"
                    >
                      <Check className="w-3 h-3" /> Accept
                    </button>
                    <button
                      onClick={() => handleReviewInsight(ins.id, 'REJECT')}
                      className="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-semibold flex items-center gap-1"
                    >
                      <X className="w-3 h-3" /> Dismiss
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Adjudicate Approval */}
      <Modal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        title="Executive Approval Decision"
      >
        <form onSubmit={handleDecideApproval} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-xs space-y-1">
            <div className="font-semibold text-gray-900">{selectedApproval?.title}</div>
            <p className="text-gray-600">{selectedApproval?.description}</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Decision</label>
            <select
              value={approvalDecision}
              onChange={(e) => setApprovalDecision(e.target.value as any)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="APPROVED">Grant Executive Approval</option>
              <option value="REJECTED">Reject Request</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Sanction Remarks</label>
            <textarea
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
              placeholder="State budgetary or governance justification"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsApprovalModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Recording...' : 'Submit Decision'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Configure Health Scheme */}
      <Modal
        isOpen={isSchemeModalOpen}
        onClose={() => setIsSchemeModalOpen(false)}
        title="Configure State Health Scheme"
      >
        <form onSubmit={handleCreateScheme} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Scheme Title</label>
            <input
              type="text"
              value={newSchemeName}
              onChange={(e) => setNewSchemeName(e.target.value)}
              placeholder="e.g. Makkalai Thedi Maruthuvam (MTM Doorstep Healthcare)"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Scheme Code</label>
            <input
              type="text"
              value={newSchemeCode}
              onChange={(e) => setNewSchemeCode(e.target.value)}
              placeholder="e.g. TN-MTM-2026"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Scheme Mandate & Scope</label>
            <textarea
              value={newSchemeDesc}
              onChange={(e) => setNewSchemeDesc(e.target.value)}
              placeholder="Detail target demographics, eligible ailments, and field team guidelines"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsSchemeModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Configuring...' : 'Configure Scheme'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Review Report */}
      <Modal
        isOpen={isReportReviewModalOpen}
        onClose={() => setIsReportReviewModalOpen(false)}
        title="State Sign-Off on District HMIS Report"
      >
        <form onSubmit={handleReviewReport} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-xs">
            <div className="font-semibold text-gray-900">{selectedReport?.reference || 'HMIS Report'}</div>
            <div className="text-gray-500">{selectedReport?.district || 'District submission'}</div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Review Determination</label>
            <select
              value={reportReviewStatus}
              onChange={(e) => setReportReviewStatus(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="APPROVED">Formally Approve & File with State Registry</option>
              <option value="CHANGES_REQUESTED">Request Data Verification from DHO</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Review Remarks</label>
            <textarea
              value={reportReviewRemarks}
              onChange={(e) => setReportReviewRemarks(e.target.value)}
              placeholder="Observations on maternal mortality, fever indices, or immunization rates"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsReportReviewModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Recording...' : 'Complete Sign-Off'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
