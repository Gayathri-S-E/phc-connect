import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Truck, Package, AlertTriangle, CheckCircle, 
  Send, ShieldCheck, Play, ArrowRightLeft, 
  Layers, Clock, Plus, Eye, FileText, ChevronRight,
  TrendingDown, ShieldAlert, RefreshCw, Warehouse,
  Info, Box, Sparkles, Building2
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

export default function StateSupplyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'cockpit' | 'escalated' | 'warehouse' | 'monitoring' | 'shortages' => {
    if (path.includes('/escalated')) return 'escalated';
    if (path.includes('/warehouse')) return 'warehouse';
    if (path.includes('/monitoring')) return 'monitoring';
    if (path.includes('/shortages')) return 'shortages';
    return 'cockpit';
  };

  const [activeTab, setActiveTab] = useState<'cockpit' | 'escalated' | 'warehouse' | 'monitoring' | 'shortages'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'cockpit' | 'escalated' | 'warehouse' | 'monitoring' | 'shortages') => {
    setActiveTab(tab);
    if (tab === 'cockpit') navigate('/supply');
    else navigate(`/supply/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State Supply Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);

  // Escalated Requests State
  const [escalatedRequests, setEscalatedRequests] = useState<any[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<any>(null);
  const [isAllocateModalOpen, setIsAllocateModalOpen] = useState(false);
  const [allocatedQty, setAllocatedQty] = useState(0);
  const [allocationNotes, setAllocationNotes] = useState('');

  // Warehouse Stock
  const [warehouseStock, setWarehouseStock] = useState<any[]>([]);

  // Monitoring Run State
  const [monitoringResults, setMonitoringResults] = useState<any>(null);
  const [isRunningMonitor, setIsRunningMonitor] = useState(false);

  // Shortage Incidents State
  const [shortages, setShortages] = useState<any[]>([]);
  const [selectedShortage, setSelectedShortage] = useState<any>(null);
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchStateSupplyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, reqRes, stockRes, shortagesRes] = await Promise.all([
        api.get<any>('/supply/state-dashboard').catch(() => ({ data: null })),
        api.get<any>('/supply-requests?level=STATE&page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/inventory?page_size=100').catch(() => ({ data: [] })),
        api.get<any[]>('/shortages').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (reqRes?.data) {
        setEscalatedRequests(Array.isArray(reqRes.data) ? reqRes.data : reqRes.data.items || []);
      }
      if (stockRes?.data) {
        setWarehouseStock(Array.isArray(stockRes.data) ? stockRes.data : stockRes.data.items || []);
      }
      if (shortagesRes?.data) setShortages(shortagesRes.data);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load state supply management data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStateSupplyData();
  }, []);

  // Run Rule-Based Supply Chain Monitoring Engine
  const handleRunMonitoring = async () => {
    setIsRunningMonitor(true);
    try {
      const res = await api.post<any>('/supply/monitoring/run', {});
      setMonitoringResults(res.data);
      setActionSuccess(`Automated surveillance scan completed: ${res.data?.alerts_created ?? 0} stockout warning alerts generated.`);
      fetchStateSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to run monitoring scan');
    } finally {
      setIsRunningMonitor(false);
    }
  };

  // Allocate State Warehouse Stock to District
  const handleAllocateStateStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;
    setIsSubmitting(true);
    try {
      await api.post(`/supply-requests/${selectedRequest.id}/allocate`, {
        allocated_quantity: Number(allocatedQty),
        notes: allocationNotes || 'Authorized dispatch from State Central Warehouse (SCW)',
      });
      setActionSuccess(`State allocation of ${allocatedQty} units approved for indent ${selectedRequest.request_number}`);
      setIsAllocateModalOpen(false);
      fetchStateSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to allocate stock');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Resolve Critical Shortage Incident
  const handleResolveShortage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedShortage) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/shortages/${selectedShortage.id}/resolve`, {
        resolution_notes: resolutionNotes || 'Resolved via State Central Warehouse buffer stock allocation.',
      });
      setActionSuccess(`Shortage incident ${selectedShortage.id.slice(0, 8)} successfully resolved`);
      setIsResolveModalOpen(false);
      setResolutionNotes('');
      fetchStateSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to resolve shortage incident');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading State Central Warehouse & Supply Command..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchStateSupplyData} />;

  return (
    <div className="space-y-6">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'State Directorate', href: '/state' },
          { label: 'State Supply Chain Command' }
        ]}
        scopeBadge={{ label: 'Tamil Nadu Central Medical Stores', variant: 'teal' }}
        roleBadge={{ label: 'Role 10: State Supply Manager', variant: 'info' }}
        title="State Central Warehouse (SCW) & Supply Grid"
        description="Oversee statewide strategic medicine buffers, manufacturer delivery pipelines, district warehouse replenishment, and automated stockout surveillance."
        actions={
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchStateSupplyData}
              className="gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh Grid
            </Button>
            <Button
              onClick={handleRunMonitoring}
              disabled={isRunningMonitor}
              variant="teal"
              size="sm"
              className="gap-2"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isRunningMonitor ? 'Evaluating Grid...' : 'Run Supply Engine'}
            </Button>
          </div>
        }
      />

      {/* Success Notification Alert */}
      {actionSuccess && (
        <Alert variant="default" className="border-emerald-200 bg-emerald-50 text-emerald-900">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <div className="flex-1">
            <AlertTitle className="text-emerald-900 font-semibold">Supply Command Action Executed</AlertTitle>
            <AlertDescription className="text-emerald-700 text-xs mt-0.5">{actionSuccess}</AlertDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900 h-7 text-xs">
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Executive Supply Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border shadow-xs hover:border-teal-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Central Warehouse Reserves</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{(dashboardData?.warehouse_stock ?? 450000).toLocaleString()}</h3>
              <p className="text-xs text-teal-600 font-medium mt-1">Units across 65 essential lines</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
              <Warehouse className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-amber-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">District Escalations</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{dashboardData?.district_requests ?? escalatedRequests.length}</h3>
              <p className="text-xs text-amber-600 font-medium mt-1">Pending SCW buffer authorization</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
              <Package className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-sky-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Consignments En-Route</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{dashboardData?.in_transit ?? 12}</h3>
              <p className="text-xs text-sky-600 font-medium mt-1">Transit to District Headquarters</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <Truck className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-rose-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Discrepancy Flags</p>
              <h3 className={`text-2xl font-bold mt-1 ${dashboardData?.discrepancies > 0 ? 'text-rose-600' : 'text-foreground'}`}>
                {dashboardData?.discrepancies ?? 1}
              </h3>
              <p className="text-xs text-muted-foreground mt-1">Transit breakage or quantity variance</p>
            </div>
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
              dashboardData?.discrepancies > 0 ? 'bg-rose-50 text-rose-700 border-rose-100' : 'bg-slate-50 text-slate-700 border-slate-100'
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
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Layers className="w-4 h-4" />
          State Supply Cockpit
        </button>
        <button
          onClick={() => handleTabChange('escalated')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'escalated'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Package className="w-4 h-4" />
          Escalated District Indents
          {escalatedRequests.length > 0 && (
            <Badge variant="warning" className="px-1.5 py-0 text-[10px] ml-1">
              {escalatedRequests.length}
            </Badge>
          )}
        </button>
        <button
          onClick={() => handleTabChange('warehouse')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'warehouse'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Warehouse className="w-4 h-4" />
          Central Reserve Inventory
        </button>
        <button
          onClick={() => handleTabChange('monitoring')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'monitoring'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Rule-Based Engine Surveillance
        </button>
        <button
          onClick={() => handleTabChange('shortages')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'shortages'
              ? 'border-teal-600 text-teal-700 font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Critical Shortages
          {shortages.filter(s => s.status !== 'RESOLVED').length > 0 && (
            <Badge variant="destructive" className="px-1.5 py-0 text-[10px] ml-1">
              {shortages.filter(s => s.status !== 'RESOLVED').length}
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
                  <Play className="w-4 h-4 text-teal-600 fill-teal-600" />
                  Automated Supply Grid Surveillance Engine
                </CardTitle>
                <CardDescription>
                  Continuous velocity tracking detects abnormal consumption surges at any PHC or Sub-Centre across all 38 districts.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2 text-slate-700">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">Detection Frequency:</span>
                    <Badge variant="outline">Every 30 Mins (Cron)</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">Surveillance Threshold:</span>
                    <span className="font-mono text-teal-700 font-medium">Burn Velocity &gt; 1.4x Normal</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">Lead Time Buffer:</span>
                    <span>14 Days Minimum Safety Reserve</span>
                  </div>
                </div>

                <Button
                  onClick={handleRunMonitoring}
                  disabled={isRunningMonitor}
                  variant="teal"
                  className="w-full gap-2 text-xs"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  {isRunningMonitor ? 'Executing Real-Time Grid Scan...' : 'Trigger Statewide Stockout Scan Now'}
                </Button>
              </CardContent>
            </Card>

            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <ArrowRightLeft className="w-4 h-4 text-amber-600" />
                  Statewide Near-Expiry Redistribution
                </CardTitle>
                <CardDescription>
                  Identifies batches expiring within 60 days in rural PHCs and generates automated reverse transfer orders to high-volume Taluk hospitals.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-amber-50/70 border border-amber-200/80 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-amber-900 uppercase tracking-wide">Near-Expiry Units Monitored</p>
                    <h4 className="text-xl font-bold text-amber-950 mt-0.5">
                      {(dashboardData?.near_expiry ?? 1420).toLocaleString()} units
                    </h4>
                    <p className="text-[11px] text-amber-800 mt-1">Eligible for inter-facility redistribution</p>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleTabChange('warehouse')}
                    className="border-amber-300 text-amber-900 hover:bg-amber-100 text-xs"
                  >
                    View Batches
                  </Button>
                </div>

                <div className="text-xs text-muted-foreground leading-relaxed flex items-start gap-2">
                  <Info className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                  <span>
                    Zero-wastage policy automatically prioritizes dispatching oldest batches to Government Medical College Hospitals before procuring supplementary stock.
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: ESCALATED DISTRICT INDENTS */}
      {activeTab === 'escalated' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <CardTitle className="text-base text-foreground">District Escalated Medicine Indents</CardTitle>
                <CardDescription>
                  Demands requiring State Central Warehouse (SCW) reserve allocation and direct logistics dispatch.
                </CardDescription>
              </div>
              <Badge variant="warning">{escalatedRequests.length} Pending Actions</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {escalatedRequests.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No escalated requirements currently logged from district drug warehouses.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Indent Ref & Origin</TableHead>
                      <TableHead>Medication Required</TableHead>
                      <TableHead>Requested Qty</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {escalatedRequests.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell>
                          <div className="font-mono font-bold text-foreground text-xs">{r.request_number}</div>
                          <div className="text-xs text-muted-foreground">{r.facility_name || 'District Drug Warehouse'}</div>
                        </TableCell>
                        <TableCell>
                          <div className="font-semibold text-foreground text-xs">{r.medication_name || 'Essential Medicine'}</div>
                          <div className="text-[11px] text-muted-foreground">Standard TN-NEML Formulary</div>
                        </TableCell>
                        <TableCell className="font-bold text-foreground text-xs">
                          {Number(r.requested_quantity).toLocaleString()} units
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={
                              r.priority === 'EMERGENCY' ? 'destructive' :
                              r.priority === 'URGENT' ? 'warning' : 'info'
                            }
                          >
                            {r.priority}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={r.status === 'ALLOCATED' ? 'success' : 'outline'}>
                            {r.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="teal"
                            onClick={() => {
                              setSelectedRequest(r);
                              setAllocatedQty(r.requested_quantity);
                              setIsAllocateModalOpen(true);
                            }}
                            className="text-xs h-7"
                          >
                            Allocate from SCW
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

      {/* TAB 3: STATE WAREHOUSE STOCK */}
      {activeTab === 'warehouse' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">State Central Warehouse Reserve Balances</CardTitle>
            <CardDescription>
              Master Tamil Nadu Medical Services Corporation (TNMSC) buffer inventory holding for statewide emergency replenishment.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {warehouseStock.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No stock inventory registered at State Central Warehouse.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Medication & Brand</TableHead>
                      <TableHead>Central Reserve Stock</TableHead>
                      <TableHead>Minimum Buffer</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {warehouseStock.map((item) => {
                      const isLow = item.quantity_on_hand <= item.reorder_level;
                      return (
                        <TableRow key={item.id}>
                          <TableCell>
                            <div className="font-semibold text-foreground text-xs">
                              {item.generic_name || item.medication?.name || 'Formulary Drug'}
                            </div>
                            <div className="text-[11px] text-muted-foreground">
                              {item.brand_name || 'TN-NEML Standard'}
                            </div>
                          </TableCell>
                          <TableCell className="font-mono font-bold text-foreground text-xs">
                            {Number(item.quantity_on_hand).toLocaleString()} units
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {Number(item.reorder_level || 0).toLocaleString()} units
                          </TableCell>
                          <TableCell>
                            <Badge variant={isLow ? 'warning' : 'success'}>
                              {isLow ? 'Buffer Depleted' : 'Healthy Buffer'}
                            </Badge>
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

      {/* TAB 4: MONITORING RUN RESULTS */}
      {activeTab === 'monitoring' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-foreground">Supply Surveillance Engine Output</CardTitle>
                <CardDescription>
                  Automated multi-tier scan results evaluating supply security across primary healthcare centers.
                </CardDescription>
              </div>
              <Button
                onClick={handleRunMonitoring}
                disabled={isRunningMonitor}
                variant="outline"
                size="sm"
                className="gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRunningMonitor ? 'animate-spin' : ''}`} />
                Re-Scan Grid
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {monitoringResults ? (
              <div className="p-4 bg-muted/50 rounded-lg border border-border text-xs space-y-2">
                <div className="font-bold text-foreground flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  Surveillance Scan Completed Successfully
                </div>
                <div className="text-muted-foreground">
                  Alerts & Potential Shortages Created: <span className="font-bold text-foreground">{monitoringResults.alerts_created ?? 0}</span>
                </div>
                <div className="text-muted-foreground font-mono text-[11px]">
                  Execution Timestamp: {new Date().toLocaleString()}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground text-sm border rounded-lg border-dashed">
                <Play className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
                <p className="font-medium text-foreground">No recent manual scan in memory</p>
                <p className="text-xs mt-1">Click 'Run Supply Engine' to execute a live scan of all PHC consumption rates across the state.</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 5: SHORTAGES */}
      {activeTab === 'shortages' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">Active Shortage Incidents</CardTitle>
            <CardDescription>
              Unresolved stockouts escalated across district boundaries requiring state intervention.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {shortages.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No critical shortage incidents requiring state intervention.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Incident Ref</TableHead>
                      <TableHead>Medicine Name</TableHead>
                      <TableHead>Current Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {shortages.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell className="font-mono font-bold text-foreground text-xs">
                          {s.id?.slice(0, 8)}
                        </TableCell>
                        <TableCell className="font-semibold text-foreground text-xs">
                          {s.medication_name || 'Essential Medicine'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={s.status === 'RESOLVED' ? 'success' : 'destructive'}>
                            {s.status || 'REPORTED'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {s.status !== 'RESOLVED' ? (
                            <Button
                              onClick={() => {
                                setSelectedShortage(s);
                                setResolutionNotes('');
                                setIsResolveModalOpen(true);
                              }}
                              variant="emerald"
                              size="sm"
                              className="text-xs h-7"
                            >
                              Resolve
                            </Button>
                          ) : (
                            <span className="text-xs text-muted-foreground italic">Closed</span>
                          )}
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

      {/* DIALOG: Allocate from SCW */}
      <Dialog open={isAllocateModalOpen} onOpenChange={setIsAllocateModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Allocate State Central Reserve Stock</DialogTitle>
            <DialogDescription>
              Dispatch emergency buffer stock for Indent #{selectedRequest?.request_number}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAllocateStateStock} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">
                Quantity from State Central Warehouse
              </label>
              <Input
                type="number"
                value={allocatedQty}
                onChange={(e) => setAllocatedQty(Number(e.target.value))}
                className="font-mono font-bold text-sm"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">
                State Dispatch & Logistics Notes
              </label>
              <Textarea
                value={allocationNotes}
                onChange={(e) => setAllocationNotes(e.target.value)}
                placeholder="e.g. Authorized from Batch SCW-TN-2026-X; assign to District Logistics truck"
                className="text-xs h-20"
                required
              />
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsAllocateModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="teal"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Allocating...' : 'Authorize State Allocation'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Resolve Shortage Incident */}
      <Dialog open={isResolveModalOpen} onOpenChange={setIsResolveModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resolve Shortage Incident</DialogTitle>
            <DialogDescription>
              Incident Ref #{selectedShortage?.id?.slice(0, 8)}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleResolveShortage} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">
                Resolution Action Documentation
              </label>
              <Textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="e.g. Emergency buffer stock dispatched from State Central Warehouse; inventory replenished above safety threshold."
                className="text-xs h-24"
                required
              />
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsResolveModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="emerald"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Resolving...' : 'Confirm Incident Resolution'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
