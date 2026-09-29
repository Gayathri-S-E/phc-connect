import React, { useState, useEffect } from 'react';
import { 
  Building2, Users, AlertTriangle, CheckCircle, 
  Clock, Plus, ShieldCheck, MapPin, Activity, 
  Send, FileText, ChevronRight, BarChart3, TrendingUp,
  AlertCircle, Eye, ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function DistrictHealthPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [activeTab, setActiveTab] = useState<'cockpit' | 'facilities' | 'actions' | 'alerts' | 'supply_impacts'>('cockpit');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [analyticsData, setAnalyticsData] = useState<any>(null);

  // Actions State
  const [actions, setActions] = useState<any[]>([]);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [newActionTitle, setNewActionTitle] = useState('');
  const [newActionDesc, setNewActionDesc] = useState('');
  const [newActionCategory, setNewActionCategory] = useState('STAFFING');
  const [newActionPriority, setNewActionPriority] = useState('HIGH');
  const [newActionDueAt, setNewActionDueAt] = useState('');

  // Alerts State
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [newAlertTitle, setNewAlertTitle] = useState('');
  const [newAlertCategory, setNewAlertCategory] = useState('SURVEILLANCE');
  const [newAlertSeverity, setNewAlertSeverity] = useState('HIGH');
  const [newAlertDesc, setNewAlertDesc] = useState('');

  // Supply Impacts State
  const [supplyImpacts, setSupplyImpacts] = useState<any[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchDistrictData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, analyticsRes, actionsRes, alertsRes, impactsRes] = await Promise.all([
        api.get<any>('/district/dashboard').catch(() => ({ data: null })),
        api.get<any>('/district/analytics').catch(() => ({ data: null })),
        api.get<any>('/governance/actions?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/governance/alerts?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/supply-impacts?page_size=50').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (analyticsRes?.data) setAnalyticsData(analyticsRes.data);
      if (actionsRes?.data) {
        setActions(Array.isArray(actionsRes.data) ? actionsRes.data : actionsRes.data.items || []);
      }
      if (alertsRes?.data) {
        setAlerts(Array.isArray(alertsRes.data) ? alertsRes.data : alertsRes.data.items || []);
      }
      if (impactsRes?.data) {
        setSupplyImpacts(Array.isArray(impactsRes.data) ? impactsRes.data : impactsRes.data.items || []);
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load district health officer data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDistrictData();
  }, []);

  // Create Administrative Action Directive
  const handleCreateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/governance/actions', {
        title: newActionTitle,
        description: newActionDesc,
        category: newActionCategory,
        priority: newActionPriority,
        due_at: newActionDueAt ? new Date(newActionDueAt).toISOString() : undefined,
      });
      setActionSuccess('Administrative directive issued successfully');
      setIsActionModalOpen(false);
      setNewActionTitle('');
      setNewActionDesc('');
      fetchDistrictData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to create administrative action');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Raise District Governance Alert
  const handleRaiseAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/governance/alerts', {
        title: newAlertTitle,
        category: newAlertCategory,
        severity: newAlertSeverity,
        description: newAlertDesc,
      });
      setActionSuccess('District health alert published');
      setIsAlertModalOpen(false);
      setNewAlertTitle('');
      setNewAlertDesc('');
      fetchDistrictData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to publish health alert');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Acknowledge Supply Impact
  const handleAcknowledgeImpact = async (impactId: string) => {
    try {
      await api.post(`/supply-impacts/${impactId}/acknowledge`, {});
      setActionSuccess('Supply impact acknowledged');
      fetchDistrictData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to acknowledge supply impact');
    }
  };

  // Acknowledge Governance Alert
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await api.post(`/governance/alerts/${alertId}/transitions`, {
        operation: 'RESPOND',
        note: 'District Health Officer acknowledged and deployed clinical response team',
      });
      setActionSuccess('District alert response recorded');
      fetchDistrictData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to acknowledge alert');
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading District Health Administration Cockpit..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchDistrictData} />;

  const totals = dashboardData?.totals || analyticsData?.totals || {};
  const governance = dashboardData?.governance || {};

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-teal-800 to-emerald-950 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-teal-200 text-sm font-semibold tracking-wide uppercase">
              <ShieldCheck className="w-4 h-4" />
              <span>Role 06: District Health Officer (DHO)</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">
              {dashboardData?.scope || user?.district || 'District Health Administration Cockpit'}
            </h1>
            <p className="text-teal-100 text-sm mt-1">
              Cross-facility performance oversight, disease outbreak alerts, administrative directives & supply impact monitoring.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-3 rounded-lg border border-white/20">
            <Activity className="w-5 h-5 text-teal-200" />
            <div>
              <div className="text-xs text-teal-200 uppercase font-bold">Active Emergencies</div>
              <div className="text-xl font-black">{dashboardData?.active_emergencies ?? 0}</div>
            </div>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-teal-200 hover:text-white text-xs font-bold uppercase">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-4 rounded-lg shadow-sm overflow-x-auto">
        <button
          onClick={() => setActiveTab('cockpit')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'cockpit'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          District Command Cockpit
        </button>
        <button
          onClick={() => setActiveTab('facilities')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'facilities'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Building2 className="w-4 h-4" />
          PHC Comparison & Watchlist
          {dashboardData?.attention?.length > 0 && (
            <span className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {dashboardData.attention.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('actions')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'actions'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Send className="w-4 h-4" />
          Administrative Directives
          {governance.pending_actions > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {governance.pending_actions}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'alerts'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          District Health Alerts
          {governance.open_alerts > 0 && (
            <span className="bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {governance.open_alerts}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('supply_impacts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'supply_impacts'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Supply Shortage Impacts
          {governance.unacknowledged_supply_impacts > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {governance.unacknowledged_supply_impacts}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: DISTRICT COMMAND COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          {/* Key KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total District OPD Volume</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.patient_volume ?? 0}</h3>
                <span className="text-xs text-teal-600 font-medium mt-1 inline-block">Consultations: {totals.consultations ?? 0}</span>
              </div>
              <div className="p-3 bg-teal-50 text-teal-600 rounded-lg">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Health Facilities Monitored</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.facilities ?? 0}</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Active: {totals.active_facilities ?? totals.facilities ?? 0} PHCs/CHCs</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Building2 className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Staff On Duty Today</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">
                  {totals.staff_present ?? 0} / {totals.staff_assigned ?? 0}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">
                  {totals.staff_assigned ? `${Math.round((totals.staff_present / totals.staff_assigned) * 100)}% attendance rate` : 'Full muster'}
                </span>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Supply Stockouts</p>
                <h3 className={`text-2xl font-bold mt-1 ${totals.stockout_items > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                  {totals.stockout_items ?? 0}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Open Supply Indents: {governance.open_supply_requests ?? 0}</span>
              </div>
              <div className={`p-3 rounded-lg ${totals.stockout_items > 0 ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-600'}`}>
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Attention Watchlist Card */}
          {dashboardData?.attention?.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2 text-red-800 font-bold text-sm">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span>Facilities Requiring Immediate Attention ({dashboardData.attention.length})</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {dashboardData.attention.map((fac: any) => (
                  <div key={fac.facility_id} className="bg-white p-3.5 rounded-lg border border-red-200 text-xs space-y-1">
                    <div className="font-bold text-gray-900">{fac.facility_name}</div>
                    <div className="text-red-600 font-semibold">Status: {fac.operational_status}</div>
                    <div className="text-gray-600">{fac.status_reasons?.join(', ') || 'Low attendance or stockout'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Governance Pipeline Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Send className="w-4 h-4 text-teal-600" />
                Administrative Directives
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1 border-b border-gray-100">
                  <span className="text-gray-600">Pending Actions</span>
                  <span className="font-bold text-amber-700">{governance.pending_actions ?? 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-100">
                  <span className="text-gray-600">Overdue Directives</span>
                  <span className="font-bold text-red-700">{governance.overdue_actions ?? 0}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-600">Reports Awaiting Review</span>
                  <span className="font-bold text-teal-700">{governance.reports_awaiting_review ?? 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                District Alerts Status
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1 border-b border-gray-100">
                  <span className="text-gray-600">Active Health Alerts</span>
                  <span className="font-bold text-red-600">{governance.open_alerts ?? 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-100">
                  <span className="text-gray-600">Emergency Supply Indents</span>
                  <span className="font-bold text-amber-600">{governance.open_emergency_supply_requests ?? 0}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-gray-600">Unacknowledged Supply Impacts</span>
                  <span className="font-bold text-purple-700">{governance.unacknowledged_supply_impacts ?? 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                DHO Policy Action Centre
              </h4>
              <p className="text-xs text-gray-500 leading-relaxed mb-4">
                Execute cross-block medical officer transfers, declare district emergency measures, and escalate critical deficits to the State Directorate.
              </p>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => setIsActionModalOpen(true)}
                  className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Issue Directive
                </button>
                <button
                  onClick={() => setIsAlertModalOpen(true)}
                  className="w-full py-2 border border-red-300 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Publish Health Alert
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PHC COMPARISON & WATCHLIST */}
      {activeTab === 'facilities' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Primary Health Centres (PHC) Comparative Matrix</h3>
              <p className="text-xs text-gray-500">Cross-block clinical throughput, staffing, and stock availability.</p>
            </div>
            <button
              onClick={fetchDistrictData}
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 px-3 py-1.5 bg-teal-50 rounded-lg"
            >
              Refresh Data
            </button>
          </div>

          <DataTable
            data={analyticsData?.comparison || dashboardData?.facilities || []}
            keyField="facility_id"
            emptyMessage="No facility records available for this district."
            columns={[
              {
                header: 'Facility Name',
                accessor: (f: any) => (
                  <div>
                    <div className="font-semibold text-gray-900">{f.facility_name || 'PHC Unit'}</div>
                    <div className="text-xs text-gray-400 font-mono">ID: {f.facility_id?.slice(0, 8)}</div>
                  </div>
                ),
              },
              {
                header: 'Patient Volume',
                accessor: (f: any) => <span className="font-bold text-gray-900">{f.patient_volume ?? 0}</span>,
              },
              {
                header: 'Consultations',
                accessor: (f: any) => f.consultations ?? 0,
              },
              {
                header: 'Referrals Out',
                accessor: (f: any) => <span className="text-amber-700 font-medium">{f.referrals ?? 0}</span>,
              },
              {
                header: 'Staff Attendance',
                accessor: (f: any) => (
                  <div>
                    <span className="font-semibold text-gray-900">{f.staff_present_today ?? 0}</span>
                    <span className="text-xs text-gray-500"> / {f.staff_assigned ?? 0}</span>
                  </div>
                ),
              },
              {
                header: 'Stockouts',
                accessor: (f: any) => (
                  <span className={(f.stockout_items || 0) > 0 ? 'text-red-600 font-bold' : 'text-gray-400'}>
                    {f.stockout_items ?? 0} items
                  </span>
                ),
              },
              {
                header: 'Operational Status',
                accessor: (f: any) => (
                  <Badge 
                    label={f.operational_status || 'NORMAL'} 
                    status={f.operational_status === 'NORMAL' ? 'success' : f.operational_status === 'DISRUPTED' ? 'danger' : 'warning'} 
                  />
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: ADMINISTRATIVE DIRECTIVES */}
      {activeTab === 'actions' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Administrative Directives & Mandates</h3>
              <p className="text-xs text-gray-500">Action items assigned to facility in-charges and district coordinators.</p>
            </div>
            <button
              onClick={() => setIsActionModalOpen(true)}
              className="px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Issue New Directive
            </button>
          </div>

          <DataTable
            data={actions}
            keyField="id"
            emptyMessage="No administrative directives currently pending in this district."
            columns={[
              {
                header: 'Directive',
                accessor: (a) => (
                  <div>
                    <div className="font-semibold text-gray-900">{a.title}</div>
                    <div className="text-xs text-gray-600 line-clamp-1">{a.description}</div>
                  </div>
                ),
              },
              {
                header: 'Category',
                accessor: (a) => <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{a.category}</span>,
              },
              {
                header: 'Priority',
                accessor: (a) => (
                  <Badge 
                    label={a.priority} 
                    status={a.priority === 'CRITICAL' ? 'danger' : a.priority === 'HIGH' ? 'warning' : 'info'} 
                  />
                ),
              },
              {
                header: 'Status',
                accessor: (a) => (
                  <Badge 
                    label={a.status} 
                    status={a.status === 'RESOLVED' ? 'success' : a.status === 'OVERDUE' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Due Date',
                accessor: (a) => a.due_at ? new Date(a.due_at).toLocaleDateString() : 'Immediate',
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: DISTRICT HEALTH ALERTS */}
      {activeTab === 'alerts' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">District Health & Epidemic Alerts</h3>
              <p className="text-xs text-gray-500">Live surveillance alarms, fever spikes, and environmental contamination alerts.</p>
            </div>
            <button
              onClick={() => setIsAlertModalOpen(true)}
              className="px-3.5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <AlertTriangle className="w-4 h-4" />
              Publish Health Alert
            </button>
          </div>

          <DataTable
            data={alerts}
            keyField="id"
            emptyMessage="No active health alerts published in this district."
            columns={[
              {
                header: 'Alert Title',
                accessor: (al) => (
                  <div>
                    <div className="font-semibold text-gray-900">{al.title}</div>
                    <div className="text-xs text-gray-600 line-clamp-1">{al.description}</div>
                  </div>
                ),
              },
              {
                header: 'Category',
                accessor: 'category',
              },
              {
                header: 'Severity',
                accessor: (al) => (
                  <Badge 
                    label={al.severity} 
                    status={al.severity === 'CRITICAL' ? 'danger' : al.severity === 'HIGH' ? 'warning' : 'info'} 
                  />
                ),
              },
              {
                header: 'Status',
                accessor: (al) => (
                  <Badge 
                    label={al.status} 
                    status={al.status === 'RESOLVED' ? 'success' : al.status === 'OPEN' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Published At',
                accessor: (al: any) => new Date(al.created_at).toLocaleString(),
              },
              {
                header: 'Action',
                accessor: (al: any) => (
                  al.status !== 'RESOLVED' ? (
                    <button
                      onClick={() => handleAcknowledgeAlert(al.id)}
                      className="px-2.5 py-1 text-xs font-semibold rounded bg-blue-50 text-blue-700 hover:bg-blue-100"
                    >
                      Acknowledge & Respond
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">Addressed</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 5: SUPPLY IMPACTS */}
      {activeTab === 'supply_impacts' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Supply Shortages Impacting Clinical Services</h3>
            <p className="text-xs text-gray-500">
              Notices communicated from District Supply Chain Officer (DSCO) regarding life-saving drug depletion.
            </p>
          </div>

          <DataTable
            data={supplyImpacts}
            keyField="id"
            emptyMessage="No clinical supply impacts registered for this district."
            columns={[
              {
                header: 'Impact Notice',
                accessor: (imp) => (
                  <div>
                    <div className="font-semibold text-gray-900">{imp.title || 'Medicine Shortage'}</div>
                    <div className="text-xs text-gray-600">{imp.clinical_consequence || imp.description}</div>
                  </div>
                ),
              },
              {
                header: 'Affected Facility',
                accessor: (imp) => imp.facility_name || 'Multiple PHCs',
              },
              {
                header: 'Reported At',
                accessor: (imp) => new Date(imp.created_at).toLocaleDateString(),
              },
              {
                header: 'Status',
                accessor: (imp) => (
                  <Badge 
                    label={imp.acknowledged_by ? 'Acknowledged' : 'Pending Review'} 
                    status={imp.acknowledged_by ? 'success' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (imp) => (
                  !imp.acknowledged_by ? (
                    <button
                      onClick={() => handleAcknowledgeImpact(imp.id)}
                      className="px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded text-xs font-semibold"
                    >
                      Acknowledge
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">Seen</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Issue Administrative Directive */}
      <Modal
        isOpen={isActionModalOpen}
        onClose={() => setIsActionModalOpen(false)}
        title="Issue Administrative Directive (DHO Mandate)"
      >
        <form onSubmit={handleCreateAction} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Directive Title</label>
            <input
              type="text"
              value={newActionTitle}
              onChange={(e) => setNewActionTitle(e.target.value)}
              placeholder="e.g. Mandatory Fever Surveillance & Vector Control Drive"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Category</label>
              <select
                value={newActionCategory}
                onChange={(e) => setNewActionCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="STAFFING">Staffing & Muster</option>
                <option value="SUPPLY_CHAIN">Supply Chain & Stock</option>
                <option value="SURVEILLANCE">Disease Surveillance</option>
                <option value="INFRASTRUCTURE">Facility Infrastructure</option>
                <option value="DATA_VERIFICATION">Data Quality Audit</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Priority</label>
              <select
                value={newActionPriority}
                onChange={(e) => setNewActionPriority(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="ROUTINE">ROUTINE</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Target Compliance Date</label>
            <input
              type="date"
              value={newActionDueAt}
              onChange={(e) => setNewActionDueAt(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Directive Text & Instructions</label>
            <textarea
              value={newActionDesc}
              onChange={(e) => setNewActionDesc(e.target.value)}
              placeholder="Detail specific protocols, required rosters, and reporting deadlines"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsActionModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Transmitting...' : 'Issue Directive'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Publish Health Alert */}
      <Modal
        isOpen={isAlertModalOpen}
        onClose={() => setIsAlertModalOpen(false)}
        title="Publish District Health Alert"
      >
        <form onSubmit={handleRaiseAlert} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Alert Headline</label>
            <input
              type="text"
              value={newAlertTitle}
              onChange={(e) => setNewAlertTitle(e.target.value)}
              placeholder="e.g. Cluster of Acute Diarrheal Disease (ADD) in Block 3"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Category</label>
              <select
                value={newAlertCategory}
                onChange={(e) => setNewAlertCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="SURVEILLANCE">Epidemiological Surveillance</option>
                <option value="OUTBREAK">Disease Outbreak</option>
                <option value="WEATHER">Extreme Weather / Cyclone</option>
                <option value="CONTAMINATION">Water / Food Contamination</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Severity</label>
              <select
                value={newAlertSeverity}
                onChange={(e) => setNewAlertSeverity(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL (Emergency)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Alert Description & Clinical Guidance</label>
            <textarea
              value={newAlertDesc}
              onChange={(e) => setNewAlertDesc(e.target.value)}
              placeholder="Advise on symptomatic management, sample collection, and mandatory reporting"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsAlertModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Publishing...' : 'Broadcast Alert'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
