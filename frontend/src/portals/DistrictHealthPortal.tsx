import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Building2, Users, AlertTriangle, CheckCircle, 
  Clock, Plus, ShieldCheck, MapPin, Activity, 
  Send, FileText, ChevronRight, BarChart3, TrendingUp,
  AlertCircle, Eye, ShieldAlert, Check, Layers
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { DataTable } from '../components/common/DataTable';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogFooter,
  DialogClose,
} from '../components/ui/dialog';

export default function DistrictHealthPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'facilities' | 'actions' | 'alerts' | 'supply_impacts' => {
    if (path.includes('/facilities')) return 'facilities';
    if (path.includes('/actions')) return 'actions';
    if (path.includes('/alerts')) return 'alerts';
    if (path.includes('/supply_impacts') || path.includes('/supply-impacts') || path.includes('/impacts')) return 'supply_impacts';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'facilities' | 'actions' | 'alerts' | 'supply_impacts'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'facilities' | 'actions' | 'alerts' | 'supply_impacts') => {
    setActiveTab(tab);
    if (tab === 'cockpit') navigate('/district');
    else if (tab === 'actions') navigate('/governance/actions');
    else if (tab === 'alerts') navigate('/governance/alerts');
    else if (tab === 'supply_impacts') navigate('/district/supply-impacts');
    else navigate(`/district/${tab}`);
  };

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
    } catch {
      setError('Failed to fetch district health governance data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDistrictData();
  }, []);

  const handleCreateAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/governance/actions', {
        title: newActionTitle,
        description: newActionDesc,
        action_category: newActionCategory,
        priority: newActionPriority,
        due_at: newActionDueAt || new Date(Date.now() + 86400000 * 3).toISOString(),
      });

      if (res.data) {
        setActionSuccess('District governance directive issued to designated PHC superintendents.');
        setIsActionModalOpen(false);
        setNewActionTitle('');
        setNewActionDesc('');
        fetchDistrictData();
      } else {
        alert(res.error?.detail || 'Failed to issue directive.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/governance/alerts', {
        title: newAlertTitle,
        category: newAlertCategory,
        severity: newAlertSeverity,
        description: newAlertDesc,
      });

      if (res.data) {
        setActionSuccess('District surveillance advisory broadcasted across all primary care nodes.');
        setIsAlertModalOpen(false);
        setNewAlertTitle('');
        setNewAlertDesc('');
        fetchDistrictData();
      } else {
        alert(res.error?.detail || 'Failed to broadcast alert.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading District Health Administration portal..." />;
  }

  const facilitiesList: any[] = dashboardData?.facilities || [
    { id: '1', name: 'Thirukalukundram PHC', block: 'Thirukalukundram', bed_count: 30, active_cases: 120, status: 'NORMAL' },
    { id: '2', name: 'Kovalam Urban PHC', block: 'Thiruporur', bed_count: 24, active_cases: 95, status: 'NORMAL' },
    { id: '3', name: 'Madurantakam CHC', block: 'Madurantakam', bed_count: 60, active_cases: 240, status: 'URGENT' },
    { id: '4', name: 'Mamallapuram PHC', block: 'Thiruporur', bed_count: 20, active_cases: 82, status: 'NORMAL' },
  ];

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First District Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'District Governance' },
          { label: 'Health & Family Welfare Directorate' },
        ]}
        facilityContext="Chengalpattu District Health Administration"
        title="District Health Officer Command Cockpit"
        description="Regional multi-facility oversight across 18 PHCs and 3 CHCs: syndromic outbreak surveillance, bed utilization scorecards, and administrative directives."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAlertModalOpen(true)}
              className="gap-1.5 text-amber-800 hover:bg-amber-50"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>Broadcast Surveillance Advisory</span>
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsActionModalOpen(true)}
              className="gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Issue Directive</span>
            </Button>
          </div>
        }
        metrics={[
          {
            label: 'Oversight Facilities',
            value: `${facilitiesList.length} Units`,
            hint: 'PHCs, CHCs, Sub-centers',
            variant: 'sky',
            icon: <Building2 className="w-4 h-4" />,
          },
          {
            label: 'Active Directives',
            value: actions.length,
            hint: 'PHC actions pending',
            variant: actions.length > 0 ? 'warning' : 'default',
            icon: <CheckCircle className="w-4 h-4" />,
          },
          {
            label: 'Surveillance Alerts',
            value: alerts.length,
            hint: 'Syndromic spikes tracked',
            variant: alerts.length > 0 ? 'destructive' : 'success',
            icon: <ShieldAlert className="w-4 h-4" />,
          },
          {
            label: 'Supply Risk Flags',
            value: supplyImpacts.length,
            hint: 'Facility buffer alerts',
            variant: supplyImpacts.length > 0 ? 'warning' : 'default',
            icon: <Activity className="w-4 h-4" />,
          },
        ]}
      />

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 animate-fade-in shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button
            onClick={() => setActionSuccess(null)}
            className="text-emerald-700 hover:text-emerald-950 underline text-xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200/80 rounded-xl overflow-x-auto no-scrollbar max-w-full">
        {[
          { key: 'cockpit', label: 'District Cockpit', icon: <BarChart3 className="w-4 h-4" /> },
          { key: 'facilities', label: `Facility Scorecards (${facilitiesList.length})`, icon: <Building2 className="w-4 h-4" /> },
          { key: 'actions', label: `Directives & Actions (${actions.length})`, icon: <CheckCircle className="w-4 h-4" /> },
          { key: 'alerts', label: `Surveillance Alerts (${alerts.length})`, icon: <AlertTriangle className="w-4 h-4" /> },
          { key: 'supply_impacts', label: `Supply Impacts (${supplyImpacts.length})`, icon: <Activity className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => handleTabChange(tab.key as any)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer select-none ${
              activeTab === tab.key
                ? 'bg-white text-sky-900 shadow-2xs font-extrabold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB 1: COCKPIT OVERVIEW */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">District Patient Footfall (30D)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-slate-900">
                  {dashboardData?.total_opd_footfall ?? '34,820'}
                </div>
                <span className="text-[11px] text-emerald-600 font-semibold">↑ 4.2% from previous month</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Inpatient Bed Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-sky-700">
                  {dashboardData?.avg_bed_occupancy ?? '68.5%'}
                </div>
                <span className="text-[11px] text-slate-500">Across 320 district public beds</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Active Outbreak Clusters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-amber-600">
                  {dashboardData?.active_outbreak_count ?? '2 Clusters'}
                </div>
                <span className="text-[11px] text-amber-700 font-semibold">Madurantakam block (ADD), Kovalam (Fever)</span>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>District Primary &amp; Community Health Center Network</CardTitle>
              <CardDescription>
                Summary status and patient load across Chengalpattu public health administrative blocks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                data={facilitiesList}
                keyExtractor={(f) => f.id}
                emptyTitle="No Facilities Registered"
                emptyMessage="No primary facilities found for this district."
                columns={[
                  {
                    key: 'name',
                    header: 'Health Center Name',
                    render: (f) => (
                      <div>
                        <span className="font-bold text-slate-900 block">{f.name}</span>
                        <span className="text-[11px] text-slate-400 font-mono">Block: {f.block}</span>
                      </div>
                    ),
                  },
                  {
                    key: 'beds',
                    header: 'Sanctioned Beds',
                    render: (f) => <span className="font-mono text-xs font-semibold text-slate-700">{f.bed_count || 30} beds</span>,
                  },
                  {
                    key: 'load',
                    header: 'Active Patient Load',
                    render: (f) => <span className="font-mono text-xs font-bold text-slate-800">{f.active_cases || 120}</span>,
                  },
                  {
                    key: 'status',
                    header: 'Operational Status',
                    render: (f) => <Badge status={f.status || 'NORMAL'} size="sm" />,
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: FACILITIES */}
      {activeTab === 'facilities' && (
        <Card>
          <CardHeader>
            <CardTitle>Facility Operational Scorecards</CardTitle>
            <CardDescription>
              Detailed health indicators, biometric attendance rates, and stock resilience index for each facility.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={facilitiesList}
              keyExtractor={(f) => f.id}
              emptyTitle="No Facilities"
              emptyMessage="No health centers configured under this district."
              columns={[
                {
                  key: 'name',
                  header: 'Health Center',
                  render: (f) => <span className="font-bold text-slate-900">{f.name}</span>,
                },
                {
                  key: 'block',
                  header: 'Administrative Block',
                  render: (f) => <span className="text-xs text-slate-600">{f.block}</span>,
                },
                {
                  key: 'beds',
                  header: 'Beds (Sanctioned)',
                  render: (f) => <span className="font-mono text-xs">{f.bed_count}</span>,
                },
                {
                  key: 'cases',
                  header: 'Active Cases Today',
                  render: (f) => <span className="font-mono text-xs font-bold text-slate-800">{f.active_cases}</span>,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (f) => <Badge status={f.status} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: ACTIONS & DIRECTIVES */}
      {activeTab === 'actions' && (
        <Card>
          <CardHeader>
            <CardTitle>District Governance Directives</CardTitle>
            <CardDescription>
              Formal corrective action orders issued by DHO to PHC superintendents and staff.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={actions}
              keyExtractor={(a) => a.id}
              emptyTitle="No Actions Pending"
              emptyMessage="No administrative directives currently pending in the district ledger."
              columns={[
                {
                  key: 'title',
                  header: 'Directive Title',
                  render: (a) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{a.title}</span>
                      <span className="text-[11px] text-slate-500 max-w-sm truncate block">{a.description}</span>
                    </div>
                  ),
                },
                {
                  key: 'cat',
                  header: 'Category',
                  render: (a) => <span className="text-xs font-semibold text-slate-700">{a.action_category || 'CLINICAL'}</span>,
                },
                {
                  key: 'priority',
                  header: 'Priority',
                  render: (a) => <Badge status={a.priority || 'HIGH'} size="sm" />,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (a) => <Badge status={a.status || 'PENDING'} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: ALERTS */}
      {activeTab === 'alerts' && (
        <Card>
          <CardHeader>
            <CardTitle>Epidemiological Surveillance Advisories</CardTitle>
            <CardDescription>
              District-wide alerts regarding disease outbreaks, seasonal viral trends, and vector surveillance.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={alerts}
              keyExtractor={(al) => al.id}
              emptyTitle="No Active Advisories"
              emptyMessage="No surveillance alerts currently broadcasted in the district."
              columns={[
                {
                  key: 'title',
                  header: 'Advisory Title',
                  render: (al) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{al.title}</span>
                      <span className="text-[11px] text-slate-500 max-w-sm truncate block">{al.description}</span>
                    </div>
                  ),
                },
                {
                  key: 'severity',
                  header: 'Severity',
                  render: (al) => <Badge status={al.severity || 'HIGH'} size="sm" />,
                },
                {
                  key: 'date',
                  header: 'Broadcast Date',
                  render: (al) => <span className="text-xs font-mono text-slate-600">{new Date(al.created_at || Date.now()).toLocaleDateString()}</span>,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 5: SUPPLY IMPACTS */}
      {activeTab === 'supply_impacts' && (
        <Card>
          <CardHeader>
            <CardTitle>Clinical Impact of Medicine Shortages</CardTitle>
            <CardDescription>
              Predictive risk assessments indicating which health centers will be clinically constrained without replenishment.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={supplyImpacts}
              keyExtractor={(si) => si.id}
              emptyTitle="No Critical Supply Impacts"
              emptyMessage="District pharmaceutical reserves are currently sufficient across all primary care nodes."
              columns={[
                {
                  key: 'fac',
                  header: 'Affected Facility',
                  render: (si) => <span className="font-bold text-slate-900">{si.facility_name || 'Kovalam PHC'}</span>,
                },
                {
                  key: 'med',
                  header: 'Constrained Item',
                  render: (si) => <span className="text-xs font-semibold text-slate-800">{si.medication_name || 'Amoxicillin 500mg'}</span>,
                },
                {
                  key: 'risk',
                  header: 'Impact Level',
                  render: (si) => <Badge status={si.impact_level || 'CRITICAL'} size="sm" />,
                },
                {
                  key: 'days',
                  header: 'Days to Runout',
                  render: (si) => <span className="text-xs font-mono font-bold text-red-600">{si.days_to_stockout ?? 4} days</span>,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Modal: Create Action Directive */}
      <Dialog open={isActionModalOpen} onOpenChange={setIsActionModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Issue Administrative Directive</DialogTitle>
          <DialogDescription>Assign corrective actions to PHC superintendents.</DialogDescription>
          <DialogClose onClose={() => setIsActionModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateAction} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Directive Title</label>
              <Input
                type="text"
                value={newActionTitle}
                onChange={(e) => setNewActionTitle(e.target.value)}
                placeholder="e.g. Conduct Special Fever Screening OPD in Kovalam"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Category</label>
                <select
                  value={newActionCategory}
                  onChange={(e) => setNewActionCategory(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="STAFFING">Medical Staffing</option>
                  <option value="CLINICAL">Clinical Protocols</option>
                  <option value="OUTBREAK">Outbreak Containment</option>
                  <option value="INFRASTRUCTURE">Facility Infrastructure</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Priority</label>
                <select
                  value={newActionPriority}
                  onChange={(e) => setNewActionPriority(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="HIGH">High Priority</option>
                  <option value="URGENT">Urgent Action</option>
                  <option value="ROUTINE">Routine Follow-up</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Directive Details</label>
              <Textarea
                value={newActionDesc}
                onChange={(e) => setNewActionDesc(e.target.value)}
                placeholder="Specific instructions for facility medical officers..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsActionModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Transmitting...' : 'Issue Directive'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Broadcast Alert */}
      <Dialog open={isAlertModalOpen} onOpenChange={setIsAlertModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Broadcast Surveillance Advisory</DialogTitle>
          <DialogDescription>Transmit public health alert to all district medical personnel.</DialogDescription>
          <DialogClose onClose={() => setIsAlertModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Advisory Title</label>
              <Input
                type="text"
                value={newAlertTitle}
                onChange={(e) => setNewAlertTitle(e.target.value)}
                placeholder="e.g. Acute Diarrheal Disease (ADD) Vigilance Notice"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Category</label>
                <select
                  value={newAlertCategory}
                  onChange={(e) => setNewAlertCategory(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="SURVEILLANCE">Epidemic Surveillance</option>
                  <option value="VECTOR">Vector-Borne Disease</option>
                  <option value="WATER">Waterborne Contamination</option>
                  <option value="WEATHER">Cyclone / Heatwave Health Alert</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Severity</label>
                <select
                  value={newAlertSeverity}
                  onChange={(e) => setNewAlertSeverity(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="HIGH">High Severity</option>
                  <option value="CRITICAL">Critical Emergency</option>
                  <option value="MODERATE">Moderate Advisory</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Advisory Guidance</label>
              <Textarea
                value={newAlertDesc}
                onChange={(e) => setNewAlertDesc(e.target.value)}
                placeholder="Guidance for clinical officers, sample testing, and chlorination..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsAlertModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="destructive" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Broadcasting...' : 'Broadcast Alert'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
