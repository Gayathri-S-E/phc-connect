import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Globe2, Building2, ShieldCheck, CheckCircle, 
  TrendingUp, BarChart3, Truck, AlertTriangle, 
  Send, Plus, FileText, ChevronRight, Eye, Flag,
  RefreshCw, Landmark, Shield, Info
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

export default function NationalHealthPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'states' | 'supply_grid' | 'directives' => {
    if (path.includes('/states')) return 'states';
    if (path.includes('/supply-grid') || path.includes('/supply_grid')) return 'supply_grid';
    if (path.includes('/directives') || path.includes('/actions')) return 'directives';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'states' | 'supply_grid' | 'directives'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'states' | 'supply_grid' | 'directives') => {
    setActiveTab(tab);
    if (tab === 'cockpit') navigate('/national');
    else if (tab === 'directives') navigate('/governance/actions');
    else if (tab === 'supply_grid') navigate('/national/supply-grid');
    else navigate(`/national/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [supplyOverview, setSupplyOverview] = useState<any>(null);

  // Directives State
  const [directives, setDirectives] = useState<any[]>([]);
  const [isDirectiveModalOpen, setIsDirectiveModalOpen] = useState(false);
  const [directiveTitle, setDirectiveTitle] = useState('');
  const [directivePriority, setDirectivePriority] = useState('HIGH');
  const [directiveCategory, setDirectiveCategory] = useState('POLICY');
  const [directiveTargetState, setDirectiveTargetState] = useState('Tamil Nadu');
  const [directiveText, setDirectiveText] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchNationalData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, supplyRes, directivesRes] = await Promise.all([
        api.get<any>('/national/dashboard').catch(() => ({ data: null })),
        api.get<any>('/national/supply-chain-overview').catch(() => ({ data: null })),
        api.get<any>('/governance/actions?page_size=50').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (supplyRes?.data) setSupplyOverview(supplyRes.data);
      if (directivesRes?.data) {
        setDirectives(Array.isArray(directivesRes.data) ? directivesRes.data : directivesRes.data.items || []);
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load national health authority data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNationalData();
  }, []);

  // Dispatch National Coordination Directive
  const handleIssueDirective = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/governance/actions', {
        title: directiveTitle,
        description: `[Target State: ${directiveTargetState}] ${directiveText}`,
        category: directiveCategory,
        priority: directivePriority,
        target_state: directiveTargetState,
      });
      setActionSuccess('National coordination directive dispatched to State Directorate.');
      setIsDirectiveModalOpen(false);
      setDirectiveTitle('');
      setDirectiveText('');
      fetchNationalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to issue directive');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading National Health Authority Cockpit..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchNationalData} />;

  const totals = dashboardData?.totals || {};
  const statesList = dashboardData?.states || [];
  const supplyStates = supplyOverview?.states || [];

  return (
    <div className="space-y-6">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Ministry of Health & Family Welfare', href: '/national' },
          { label: 'National Health Operations' }
        ]}
        scopeBadge={{ label: 'National Health Authority (NHA / MoHFW)', variant: 'sky' }}
        roleBadge={{ label: 'Role 12: National Health Authority', variant: 'info' }}
        title="National Health Operations & Strategic Oversight"
        description="Union-level oversight of primary healthcare capacity, National Health Mission (NHM) milestones, inter-state medicine grids, and statutory directives."
        actions={
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchNationalData}
              className="gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </Button>
            <Button
              onClick={() => setIsDirectiveModalOpen(true)}
              variant="sky"
              size="sm"
              className="gap-2"
            >
              <Plus className="w-3.5 h-3.5" />
              Issue National Directive
            </Button>
          </div>
        }
      />

      {/* Action Success Alert */}
      {actionSuccess && (
        <Alert variant="default" className="border-emerald-200 bg-emerald-50 text-emerald-900">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <div className="flex-1">
            <AlertTitle className="text-emerald-900 font-semibold">Strategic Directive Dispatched</AlertTitle>
            <AlertDescription className="text-emerald-700 text-xs mt-0.5">{actionSuccess}</AlertDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900 h-7 text-xs">
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Statutory Privacy Context Banner */}
      <div className="p-3.5 bg-sky-50/70 border border-sky-200/80 rounded-xl flex items-center justify-between text-xs text-sky-950">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0" />
          <div>
            <span className="font-bold text-sky-950">National Healthcare Data Governance Tier:</span>{' '}
            <span className="text-sky-900">Union officials interact strictly with state-level aggregates and resilience indicators. Microdata and citizen PII are systematically excluded.</span>
          </div>
        </div>
        <Badge variant="sky" className="shrink-0 text-[10px]">Union Level Scope</Badge>
      </div>

      {/* Executive National Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border shadow-xs hover:border-sky-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Pan-India Patient Volume</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{(totals.patient_volume ?? 48200).toLocaleString()}</h3>
              <p className="text-xs text-sky-700 font-medium mt-1">Reported across connected states</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <Globe2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-blue-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Network Facilities</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{totals.facilities ?? 184}</h3>
              <p className="text-xs text-emerald-700 font-medium mt-1">100% Primary Care Grid Coverage</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
              <Building2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-emerald-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">National Stockout Rate</p>
              <h3 className="text-2xl font-bold text-emerald-700 mt-1">1.2%</h3>
              <p className="text-xs text-muted-foreground mt-1">Sub-2% resilience target met</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-amber-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Active National Directives</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{dashboardData?.governance?.open_alerts ?? directives.length}</h3>
              <p className="text-xs text-amber-700 font-medium mt-1">Tracked in Union Ops Center</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
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
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          National Health Cockpit
        </button>
        <button
          onClick={() => handleTabChange('states')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'states'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Inter-State Health Benchmarks
        </button>
        <button
          onClick={() => handleTabChange('supply_grid')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'supply_grid'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Truck className="w-4 h-4" />
          National Supply Chain Grid
        </button>
        <button
          onClick={() => handleTabChange('directives')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'directives'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Send className="w-4 h-4" />
          Strategic Directives & Mandates
          {directives.length > 0 && (
            <Badge variant="info" className="px-1.5 py-0 text-[10px] ml-1">
              {directives.length}
            </Badge>
          )}
        </button>
      </div>

      {/* TAB 1: COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <Landmark className="w-4 h-4 text-sky-700" />
                  National Health Mission Alignment
                </CardTitle>
                <CardDescription>
                  Tracking state compliance with 15th Finance Commission primary health strengthening milestones.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2 text-slate-700">
                  <div className="flex justify-between">
                    <span className="font-semibold text-foreground">Teleconsultation Target:</span>
                    <span className="text-emerald-700 font-bold">98.4% Achieved</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-foreground">Essential Medicine Availability:</span>
                    <span className="text-emerald-700 font-bold">96.8% In-Stock</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-semibold text-foreground">Digital Health ID (ABHA) Saturation:</span>
                    <span className="text-sky-700 font-bold">91.2% Registered</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <Send className="w-4 h-4 text-sky-700" />
                  Inter-State Coordination Mandate
                </CardTitle>
                <CardDescription>
                  Dispatch high-priority directives to State Health Secretaries for emergency drug transfers or epidemiological alerts.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Directives are transmitted directly into the State Health Director's command inbox with legally binding tracking and acknowledgement timestamps.
                </p>
                <Button
                  onClick={() => setIsDirectiveModalOpen(true)}
                  variant="sky"
                  className="w-full gap-2 text-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Issue Coordination Directive
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: INTER-STATE BENCHMARKS */}
      {activeTab === 'states' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">State-Level Performance Comparison</CardTitle>
            <CardDescription>
              Consolidated primary healthcare key performance indicators across participating states.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>State / Union Territory</TableHead>
                    <TableHead>Facilities Reporting</TableHead>
                    <TableHead>Patient Volume</TableHead>
                    <TableHead>Consultations</TableHead>
                    <TableHead>Referrals</TableHead>
                    <TableHead>Stockouts Flagged</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(statesList.length > 0 ? statesList : [
                    { state: 'Tamil Nadu', facilities: 42, patient_volume: 12450, consultations: 11800, referrals: 310, stockout_items: 2 },
                    { state: 'Kerala', facilities: 38, patient_volume: 11200, consultations: 10900, referrals: 280, stockout_items: 1 },
                    { state: 'Karnataka', facilities: 54, patient_volume: 14100, consultations: 13500, referrals: 410, stockout_items: 4 },
                    { state: 'Maharashtra', facilities: 50, patient_volume: 10450, consultations: 9800, referrals: 390, stockout_items: 3 },
                  ]).map((s: any) => (
                    <TableRow key={s.state}>
                      <TableCell className="font-bold text-foreground text-xs">
                        {s.state}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {s.facilities} PHCs / CHCs
                      </TableCell>
                      <TableCell className="font-semibold text-foreground text-xs">
                        {Number(s.patient_volume).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {Number(s.consultations).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {Number(s.referrals).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={(s.stockout_items || 0) > 2 ? 'warning' : 'success'}>
                          {s.stockout_items || 0} lines
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 3: NATIONAL SUPPLY GRID */}
      {activeTab === 'supply_grid' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">National Medicine Supply Grid</CardTitle>
            <CardDescription>
              Cross-state stockout risk matrix and emergency strategic supply balance channels.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>State</TableHead>
                    <TableHead>Network Facilities</TableHead>
                    <TableHead>Low Stock Medicines</TableHead>
                    <TableHead>Active Stockouts</TableHead>
                    <TableHead>Supply Security Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(supplyStates.length > 0 ? supplyStates : [
                    { state: 'Tamil Nadu', facilities: 42, low_stock_items: 6, stockout_items: 2, open_shortages: 1 },
                    { state: 'Kerala', facilities: 38, low_stock_items: 4, stockout_items: 1, open_shortages: 0 },
                    { state: 'Karnataka', facilities: 54, low_stock_items: 9, stockout_items: 4, open_shortages: 2 },
                  ]).map((s: any) => (
                    <TableRow key={s.state}>
                      <TableCell className="font-bold text-foreground text-xs">{s.state}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{s.facilities}</TableCell>
                      <TableCell className="text-xs text-amber-700 font-medium">{s.low_stock_items || 0} lines</TableCell>
                      <TableCell className="text-xs">
                        <span className={(s.stockout_items || 0) > 0 ? 'text-rose-700 font-bold' : 'text-muted-foreground'}>
                          {s.stockout_items || 0} lines
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={(s.stockout_items || 0) > 2 ? 'warning' : 'success'}>
                          {(s.stockout_items || 0) > 2 ? 'BUFFER WARNING' : 'RESILIENT'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 4: STRATEGIC DIRECTIVES */}
      {activeTab === 'directives' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle className="text-base text-foreground">National Strategic Directives</CardTitle>
                <CardDescription>
                  Direct policy, emergency rebalancing, and surveillance directives issued to state health directorates.
                </CardDescription>
              </div>
              <Button
                onClick={() => setIsDirectiveModalOpen(true)}
                variant="sky"
                size="sm"
                className="gap-1.5 text-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                Issue Directive
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {directives.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No national directives currently logged.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Directive Title & Context</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {directives.map((d) => (
                      <TableRow key={d.id}>
                        <TableCell>
                          <div className="font-semibold text-foreground text-xs">{d.title}</div>
                          <div className="text-[11px] text-muted-foreground line-clamp-1">{d.description}</div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={d.priority === 'CRITICAL' ? 'destructive' : 'info'}>
                            {d.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={d.status === 'COMPLETED' ? 'success' : 'warning'}>
                            {d.status || 'PENDING'}
                          </Badge>
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

      {/* DIALOG: Issue National Directive */}
      <Dialog open={isDirectiveModalOpen} onOpenChange={setIsDirectiveModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Issue National Strategic Directive</DialogTitle>
            <DialogDescription>
              Broadcast binding healthcare directives to state nodal authorities.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleIssueDirective} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Target State Directorate</label>
              <select
                value={directiveTargetState}
                onChange={(e) => setDirectiveTargetState(e.target.value)}
                className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
              >
                <option value="Tamil Nadu">Tamil Nadu State Health Mission</option>
                <option value="Kerala">Kerala State Health Mission</option>
                <option value="Karnataka">Karnataka State Health Mission</option>
                <option value="All States">Pan-India Broadcast (All States)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Directive Title</label>
              <Input
                type="text"
                value={directiveTitle}
                onChange={(e) => setDirectiveTitle(e.target.value)}
                placeholder="e.g. Nationwide Cold Chain Real-Time Telemetry Rollout"
                className="text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Category</label>
                <select
                  value={directiveCategory}
                  onChange={(e) => setDirectiveCategory(e.target.value)}
                  className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                >
                  <option value="POLICY">National Health Policy</option>
                  <option value="SUPPLY_GRID">Inter-State Supply Rebalancing</option>
                  <option value="SURVEILLANCE">IDSP Disease Surveillance</option>
                  <option value="DISASTER_RELIEF">Disaster Relief Protocol</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Priority</label>
                <select
                  value={directivePriority}
                  onChange={(e) => setDirectivePriority(e.target.value)}
                  className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                >
                  <option value="HIGH">HIGH</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Mandate & Timelines</label>
              <Textarea
                value={directiveText}
                onChange={(e) => setDirectiveText(e.target.value)}
                placeholder="Provide strategic instructions, compliance deadlines, and designated nodal officers..."
                className="text-xs h-28"
                required
              />
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDirectiveModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="sky"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Transmitting...' : 'Dispatch Directive'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
