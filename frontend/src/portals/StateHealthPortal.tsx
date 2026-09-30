import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Building2, Users, ShieldCheck, CheckCircle, 
  FileText, Activity, BarChart3, TrendingUp, 
  Plus, Eye, Download, Award, AlertTriangle, 
  Sparkles, Check, X, Clock, Layers
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

export default function StateHealthPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports' => {
    if (path.includes('/districts')) return 'districts';
    if (path.includes('/approvals')) return 'approvals';
    if (path.includes('/schemes')) return 'schemes';
    if (path.includes('/reports')) return 'reports';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'districts' | 'approvals' | 'schemes' | 'reports') => {
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchStateData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, distRes, appRes, schemesRes, repRes] = await Promise.all([
        api.get<any>('/state/dashboard').catch(() => ({ data: null })),
        api.get<any>('/state/districts').catch(() => ({ data: { districts: [] } })),
        api.get<any>('/governance/approvals?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/governance/schemes').catch(() => ({ data: [] })),
        api.get<any>('/governance/reports?page_size=50').catch(() => ({ data: [] })),
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
    } catch {
      setError('Failed to fetch state health administration records.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStateData();
  }, []);

  const handleProcessApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;

    setIsSubmitting(true);
    try {
      const res = await api.patch(`/governance/approvals/${selectedApproval.id}/decision`, {
        status: approvalDecision,
        comments: approvalNotes || 'Reviewed and authorized by State Health Secretariat',
      });

      if (res.data) {
        setActionSuccess(`Governance approval decision logged as ${approvalDecision}.`);
        setIsApprovalModalOpen(false);
        fetchStateData();
      } else {
        alert(res.error?.detail || 'Approval failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/governance/schemes', {
        name: newSchemeName,
        code: newSchemeCode || newSchemeName.toUpperCase().replace(/\s+/g, '_').slice(0, 10),
        description: newSchemeDesc,
      });

      if (res.data) {
        setActionSuccess('New state public health initiative created successfully.');
        setIsSchemeModalOpen(false);
        setNewSchemeName('');
        setNewSchemeCode('');
        setNewSchemeDesc('');
        fetchStateData();
      } else {
        alert(res.error?.detail || 'Scheme creation failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading State Health Secretariat dashboard..." />;
  }

  const defaultDistricts = [
    { id: '1', name: 'Chengalpattu', phc_count: 18, total_beds: 320, opd_monthly: 42000, compliance: '98%', status: 'EXCELLENT' },
    { id: '2', name: 'Kanchipuram', phc_count: 22, total_beds: 410, opd_monthly: 51000, compliance: '95%', status: 'GOOD' },
    { id: '3', name: 'Tiruvallur', phc_count: 25, total_beds: 480, opd_monthly: 58000, compliance: '94%', status: 'GOOD' },
    { id: '4', name: 'Vellore', phc_count: 20, total_beds: 390, opd_monthly: 46000, compliance: '91%', status: 'SATISFACTORY' },
    { id: '5', name: 'Villupuram', phc_count: 28, total_beds: 520, opd_monthly: 62000, compliance: '89%', status: 'NEEDS_ATTENTION' },
  ];

  const displayedDistricts = districtsList.length > 0 ? districtsList : defaultDistricts;
  const pendingApprovals = approvals.filter((a) => a.status === 'PENDING');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First State Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'State Governance' },
          { label: 'Health & Family Welfare Secretariat' },
        ]}
        facilityContext="Government of Tamil Nadu • State Headquarters"
        title="State Health Administrator Command Portal"
        description="Statewide public health oversight across all 38 revenue districts: district performance benchmarking, health mission schemes, and strategic policy approvals."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsSchemeModalOpen(true)}
            className="gap-1.5 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Launch Health Scheme</span>
          </Button>
        }
        metrics={[
          {
            label: 'Districts Monitored',
            value: '38 Districts',
            hint: 'Tamil Nadu Statewide',
            variant: 'sky',
            icon: <Building2 className="w-4 h-4" />,
          },
          {
            label: 'Public PHCs & CHCs',
            value: '2,284 Facilities',
            hint: 'Integrated healthcare grid',
            variant: 'default',
            icon: <Activity className="w-4 h-4" />,
          },
          {
            label: 'Pending State Approvals',
            value: pendingApprovals.length,
            hint: 'Budget & scheme indents',
            variant: pendingApprovals.length > 0 ? 'warning' : 'success',
            icon: <Clock className="w-4 h-4" />,
          },
          {
            label: 'Active State Schemes',
            value: `${schemes.length || 6} Programs`,
            hint: 'Makkalai Thedi Maruthuvam',
            variant: 'success',
            icon: <Award className="w-4 h-4" />,
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
          { key: 'cockpit', label: 'State Cockpit', icon: <BarChart3 className="w-4 h-4" /> },
          { key: 'districts', label: `District Benchmarks (${displayedDistricts.length})`, icon: <Building2 className="w-4 h-4" /> },
          { key: 'approvals', label: `State Approvals (${approvals.length})`, icon: <CheckCircle className="w-4 h-4" /> },
          { key: 'schemes', label: `Public Schemes (${schemes.length || 6})`, icon: <Award className="w-4 h-4" /> },
          { key: 'reports', label: `HMIS Audits (${reports.length})`, icon: <FileText className="w-4 h-4" /> },
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
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Maternal Mortality Ratio (MMR)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-emerald-700">54 / 100k</div>
                <span className="text-[11px] text-emerald-600 font-medium">Achieved SDG Target (&lt;70)</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Infant Mortality Rate (IMR)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-emerald-700">13 / 1,000</div>
                <span className="text-[11px] text-emerald-600 font-medium">Lowest among major Indian states</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Health Budget Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-sky-700">89.4%</div>
                <span className="text-[11px] text-slate-500">FY 2025–26 NHM Allocation</span>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>District Health Benchmarks &amp; Rankings</CardTitle>
              <CardDescription>
                Comparative assessment across key operational indicators and health mission compliance.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                data={displayedDistricts}
                keyExtractor={(d) => d.id || d.name}
                columns={[
                  {
                    key: 'name',
                    header: 'District Name',
                    render: (d) => <span className="font-bold text-slate-900">{d.name}</span>,
                  },
                  {
                    key: 'phc',
                    header: 'PHC Facilities',
                    render: (d) => <span className="font-mono text-xs">{d.phc_count || 20}</span>,
                  },
                  {
                    key: 'beds',
                    header: 'Total Beds',
                    render: (d) => <span className="font-mono text-xs font-semibold">{d.total_beds || 350}</span>,
                  },
                  {
                    key: 'comp',
                    header: 'Protocol Compliance',
                    render: (d) => <span className="font-mono text-xs font-bold text-emerald-700">{d.compliance || '94%'}</span>,
                  },
                  {
                    key: 'status',
                    header: 'Rating',
                    render: (d) => <Badge status={d.status || 'NORMAL'} size="sm" />,
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: DISTRICTS */}
      {activeTab === 'districts' && (
        <Card>
          <CardHeader>
            <CardTitle>Tamil Nadu 38 Revenue Districts Roster</CardTitle>
            <CardDescription>
              Real-time synchronization of primary and secondary care indicators across districts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={displayedDistricts}
              keyExtractor={(d) => d.id || d.name}
              columns={[
                {
                  key: 'name',
                  header: 'District',
                  render: (d) => <span className="font-bold text-slate-900">{d.name}</span>,
                },
                {
                  key: 'phc',
                  header: 'PHCs',
                  render: (d) => <span className="font-mono text-xs">{d.phc_count || 18}</span>,
                },
                {
                  key: 'opd',
                  header: 'Monthly Footfall',
                  render: (d) => <span className="font-mono text-xs font-bold text-slate-800">{d.opd_monthly ? d.opd_monthly.toLocaleString() : '45,000'}</span>,
                },
                {
                  key: 'status',
                  header: 'Superintendence',
                  render: (d) => <Badge status={d.status || 'GOOD'} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: APPROVALS */}
      {activeTab === 'approvals' && (
        <Card>
          <CardHeader>
            <CardTitle>State Administrative Approvals Docket</CardTitle>
            <CardDescription>
              District health requisitions requiring state ministerial sanction.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={approvals}
              keyExtractor={(a) => a.id}
              emptyTitle="No Approvals Pending"
              emptyMessage="All district requisitions have been processed."
              columns={[
                {
                  key: 'title',
                  header: 'Requisition Title',
                  render: (a) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{a.title}</span>
                      <span className="text-[11px] text-slate-400">{a.district_name || 'District Request'}</span>
                    </div>
                  ),
                },
                {
                  key: 'type',
                  header: 'Approval Type',
                  render: (a) => <span className="text-xs text-slate-700 font-semibold">{a.approval_type || 'BUDGET_RELEASE'}</span>,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (a) => <Badge status={a.status || 'PENDING'} size="sm" />,
                },
                {
                  key: 'action',
                  header: 'Action',
                  render: (a) =>
                    a.status === 'PENDING' ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setSelectedApproval(a);
                          setApprovalDecision('APPROVED');
                          setApprovalNotes('');
                          setIsApprovalModalOpen(true);
                        }}
                        className="h-7 text-xs px-2.5"
                      >
                        Review
                      </Button>
                    ) : (
                      <span className="text-xs text-slate-400">Processed</span>
                    ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: SCHEMES */}
      {activeTab === 'schemes' && (
        <Card>
          <CardHeader>
            <CardTitle>Government of Tamil Nadu Flagship Health Schemes</CardTitle>
            <CardDescription>
              State public healthcare initiatives implemented across primary and secondary networks.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'Makkalai Thedi Maruthuvam (Healthcare at Doorstep)', code: 'MTM', desc: 'Doorstep screening and free medicine delivery for hypertension & diabetes.' },
                { name: 'Innuyir Kaappom — Nammai Kaakkum 48', code: 'NK48', desc: 'Free acute trauma treatment up to ₹1 Lakh in the first 48 hours for road accident victims.' },
                { name: 'Kalaignar Kapitu Thittam (Chief Minister Health Insurance)', code: 'CMCHIS', desc: 'Comprehensive cashless hospitalization coverage up to ₹5 Lakhs for vulnerable families.' },
                { name: 'Dr. Muthulakshmi Reddy Maternity Benefit Scheme', code: 'MRMBS', desc: 'Financial assistance of ₹18,000 and nutrition kit for pregnant mothers.' },
              ].map((s, i) => (
                <div key={i} className="p-4 rounded-xl border border-slate-200 bg-white space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{s.name}</span>
                    <Badge status="ACTIVE" size="sm" />
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 5: REPORTS */}
      {activeTab === 'reports' && (
        <Card>
          <CardHeader>
            <CardTitle>HMIS Monthly Compliance Audits</CardTitle>
            <CardDescription>
              Certified monthly clinical logs submitted by District Health Officers.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={reports}
              keyExtractor={(r) => r.id}
              emptyTitle="No Reports Pending Audit"
              emptyMessage="All district monthly health statements are audited."
              columns={[
                {
                  key: 'title',
                  header: 'Report Ref',
                  render: (r) => <span className="font-bold text-slate-900">{r.title || 'Monthly HMIS Return'}</span>,
                },
                {
                  key: 'dist',
                  header: 'Reporting District',
                  render: (r) => <span className="text-xs text-slate-700">{r.district_name || 'Chengalpattu'}</span>,
                },
                {
                  key: 'status',
                  header: 'Audit Status',
                  render: (r) => <Badge status={r.status || 'APPROVED'} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Modal: Process Approval */}
      <Dialog open={isApprovalModalOpen} onOpenChange={setIsApprovalModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>State Ministerial Sanction</DialogTitle>
          <DialogDescription>Approve or decline district health requisition.</DialogDescription>
          <DialogClose onClose={() => setIsApprovalModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleProcessApproval} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Decision</label>
              <select
                value={approvalDecision}
                onChange={(e) => setApprovalDecision(e.target.value as any)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
              >
                <option value="APPROVED">Grant State Sanction (Approve)</option>
                <option value="REJECTED">Decline Requisition (Reject)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Secretariat Remarks</label>
              <Textarea
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="State sanction order reference or rationale..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsApprovalModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Recording...' : 'Commit Sanction'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Launch Scheme */}
      <Dialog open={isSchemeModalOpen} onOpenChange={setIsSchemeModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Launch State Health Mission Scheme</DialogTitle>
          <DialogDescription>Create public health scheme directive.</DialogDescription>
          <DialogClose onClose={() => setIsSchemeModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateScheme} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Scheme Name</label>
              <Input
                type="text"
                value={newSchemeName}
                onChange={(e) => setNewSchemeName(e.target.value)}
                placeholder="e.g. Makkalai Thedi Maruthuvam Expansion"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Scheme Acronym / Code</label>
              <Input
                type="text"
                value={newSchemeCode}
                onChange={(e) => setNewSchemeCode(e.target.value)}
                placeholder="e.g. MTM-2026"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Scheme Objective</label>
              <Textarea
                value={newSchemeDesc}
                onChange={(e) => setNewSchemeDesc(e.target.value)}
                placeholder="Define clinical guidelines and target population..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsSchemeModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Launching...' : 'Promulgate Scheme'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
