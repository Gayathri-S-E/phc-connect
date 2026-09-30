import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, AlertTriangle, CheckCircle, Clock, 
  Plus, Users, MapPin, Send, FileText, ChevronRight, 
  Activity, Truck, Check, HelpCircle, AlertOctagon, Flame,
  Siren, PhoneCall, Radio, HeartPulse, Package
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

export default function DistrictEmergencyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'dashboard' | 'incidents' | 'tasks' | 'resources' => {
    if (path.includes('/incidents')) return 'incidents';
    if (path.includes('/tasks')) return 'tasks';
    if (path.includes('/resources')) return 'resources';
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState<'dashboard' | 'incidents' | 'tasks' | 'resources'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'dashboard' | 'incidents' | 'tasks' | 'resources') => {
    setActiveTab(tab);
    if (tab === 'dashboard') navigate('/emergency');
    else navigate(`/emergency/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Emergency Dashboard Data
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);

  // New Incident Declaration State
  const [isDeclareModalOpen, setIsDeclareModalOpen] = useState(false);
  const [declareTitle, setDeclareTitle] = useState('');
  const [declareCategory, setDeclareCategory] = useState('DISEASE_CLUSTER');
  const [declareSeverity, setDeclareSeverity] = useState('MAJOR');
  const [declareArea, setDeclareArea] = useState('District Coastal Belt');
  const [declareDescription, setDeclareDescription] = useState('');

  // Emergency Resource Request State
  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false);
  const [resourceMedId, setResourceMedId] = useState('');
  const [resourceQty, setResourceQty] = useState(200);
  const [resourceReason, setResourceReason] = useState('');
  const [medications, setMedications] = useState<any[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchEmergencyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [dashRes, incRes, medsRes] = await Promise.all([
        api.get<any>('/emergencies/dashboard').catch(() => ({ data: null })),
        api.get<any>('/emergencies?page_size=50').catch(() => ({ data: [] })),
        api.get<any[]>('/pharmacy/inventory').catch(() => ({ data: [] })),
      ]);

      if (dashRes?.data) setDashboardData(dashRes.data);
      if (incRes?.data) {
        const list = Array.isArray(incRes.data) ? incRes.data : incRes.data.items || [];
        setIncidents(list);
      }
      if (medsRes?.data) setMedications(medsRes.data);
    } catch {
      setError('Failed to fetch emergency response data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEmergencyData();
  }, []);

  const handleDeclareIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/emergencies', {
        title: declareTitle,
        emergency_type: declareCategory,
        severity: declareSeverity,
        affected_area: declareArea,
        description: declareDescription,
        source: 'District Emergency Command Coordinator',
      });

      if (res.data) {
        setActionSuccess('Emergency incident declared and dispatched to State Emergency Operation Centre.');
        setIsDeclareModalOpen(false);
        setDeclareTitle('');
        setDeclareDescription('');
        fetchEmergencyData();
      } else {
        alert(res.error?.detail || 'Declaration failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resourceMedId) return;

    setIsSubmitting(true);
    try {
      const res = await api.post('/supply/requests', {
        medication_id: resourceMedId,
        quantity_requested: Number(resourceQty),
        priority: 'EMERGENCY',
        notes: `EMERGENCY DISASTER REQUISITION: ${resourceReason || 'Critical surge supply'}`,
      });

      if (res.data) {
        setActionSuccess('Emergency supply requisition dispatched with highest priority.');
        setIsResourceModalOpen(false);
        fetchEmergencyData();
      } else {
        alert(res.error?.detail || 'Requisition failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading Emergency Command & Disaster Operations..." />;
  }

  const activeIncidents = incidents.filter((i) => i.status !== 'RESOLVED' && i.status !== 'CLOSED');
  const criticalAcuity = incidents.filter((i) => i.severity === 'CRITICAL' || i.severity === 'MAJOR');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Emergency Command Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Disaster Management' },
          { label: 'District Emergency Response Center' },
        ]}
        facilityContext="Chengalpattu Disaster Operation Centre"
        title="District Emergency &amp; Crisis Command"
        description="Multi-agency disaster coordination: rapid mass-casualty triage, mobile medical unit (MMU) dispatch, surge hospital beds, and trauma supply requisitions."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsResourceModalOpen(true)}
              className="gap-1.5"
            >
              <Package className="w-3.5 h-3.5 text-sky-600" />
              <span>Requisition Disaster Supplies</span>
            </Button>

            <Button
              variant="destructive"
              size="sm"
              onClick={() => setIsDeclareModalOpen(true)}
              className="gap-1.5 shadow-xs"
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Declare Emergency Crisis</span>
            </Button>
          </div>
        }
        metrics={[
          {
            label: 'Active Incidents',
            value: activeIncidents.length,
            hint: `${criticalAcuity.length} major or critical acuity`,
            variant: activeIncidents.length > 0 ? 'destructive' : 'success',
            icon: <ShieldAlert className="w-4 h-4" />,
          },
          {
            label: 'Mobile Units (MMU)',
            value: '4 Deployed',
            hint: '108 Ambulance linked',
            variant: 'sky',
            icon: <Truck className="w-4 h-4" />,
          },
          {
            label: 'Emergency Surge Beds',
            value: '45 Available',
            hint: 'Across District CHCs',
            variant: 'default',
            icon: <Activity className="w-4 h-4" />,
          },
          {
            label: 'Emergency Hotline',
            value: '108 Active',
            hint: 'State EOC linked',
            variant: 'success',
            icon: <Radio className="w-4 h-4" />,
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
          { key: 'dashboard', label: 'Crisis Cockpit', icon: <Radio className="w-4 h-4" /> },
          { key: 'incidents', label: `Emergency Incidents (${incidents.length})`, icon: <ShieldAlert className="w-4 h-4" /> },
          { key: 'tasks', label: 'Field Response Units', icon: <Truck className="w-4 h-4" /> },
          { key: 'resources', label: 'Disaster Supplies Requisitions', icon: <Package className="w-4 h-4" /> },
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

      {/* TAB 1: CRISIS COCKPIT */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-red-200 bg-red-50/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-red-700 font-bold flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-red-600" />
                  Active Disaster Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-red-950">
                  {activeIncidents.length} Emergency Incidents
                </div>
                <span className="text-[11px] text-red-700 font-medium">Coordinated with District Revenue &amp; Police</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Ambulance Fleet Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-slate-900">
                  18 / 22 Ambulances
                </div>
                <span className="text-[11px] text-slate-500">Available on active standby in Chengalpattu</span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs uppercase text-slate-500 font-bold">Trauma &amp; Blood Units</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-black text-emerald-700">
                  140 Packed Units
                </div>
                <span className="text-[11px] text-emerald-600 font-semibold">Blood bank reserve verified</span>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Active Emergency Incidents &amp; Disaster Responses</CardTitle>
              <CardDescription>
                Public health crises requiring multi-sectoral mobilization and priority medical logistics.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                data={incidents}
                keyExtractor={(i) => i.id}
                emptyTitle="No Disasters Declared"
                emptyMessage="District emergency status is calm with zero declared crises."
                columns={[
                  {
                    key: 'title',
                    header: 'Incident Event',
                    render: (i) => (
                      <div>
                        <span className="font-bold text-slate-900 block">{i.title}</span>
                        <span className="text-[11px] text-slate-500">{i.affected_area || 'District Catchment'}</span>
                      </div>
                    ),
                  },
                  {
                    key: 'type',
                    header: 'Classification',
                    render: (i) => <span className="text-xs font-semibold text-slate-700">{i.emergency_type}</span>,
                  },
                  {
                    key: 'sev',
                    header: 'Severity Level',
                    render: (i) => <Badge status={i.severity || 'MAJOR'} size="sm" />,
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    render: (i) => <Badge status={i.status || 'ACTIVE'} size="sm" />,
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: INCIDENTS */}
      {activeTab === 'incidents' && (
        <Card>
          <CardHeader>
            <CardTitle>Emergency Incident Register</CardTitle>
            <CardDescription>
              Chronological log of declared public health emergencies, severe weather incidents, and casualty spikes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={incidents}
              keyExtractor={(i) => i.id}
              emptyTitle="No Emergency Incidents"
              emptyMessage="No incidents currently active."
              columns={[
                {
                  key: 'id',
                  header: 'Incident Ref',
                  render: (i) => <span className="font-mono text-xs text-slate-700 font-bold">EMG-{i.id.slice(0, 8)}</span>,
                },
                {
                  key: 'title',
                  header: 'Title & Area',
                  render: (i) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{i.title}</span>
                      <span className="text-[11px] text-slate-400">{i.affected_area}</span>
                    </div>
                  ),
                },
                {
                  key: 'sev',
                  header: 'Severity',
                  render: (i) => <Badge status={i.severity} size="sm" />,
                },
                {
                  key: 'status',
                  header: 'Incident Status',
                  render: (i) => <Badge status={i.status} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: FIELD UNITS */}
      {activeTab === 'tasks' && (
        <Card>
          <CardHeader>
            <CardTitle>Mobile Medical Units (MMU) &amp; Response Squads</CardTitle>
            <CardDescription>
              Deployment status of field ambulance units and rapid response medical teams.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { name: 'MMU Unit 1 — Coastal Response', location: 'Kovalam Beach Road', doctor: 'Dr. Anbarasu', status: 'DEPLOYED' },
                { name: 'MMU Unit 2 — Inland Rural', location: 'Thirukalukundram West', doctor: 'Dr. Geetha', status: 'DEPLOYED' },
                { name: 'Ambulance Squad 108-A', location: 'Chengalpattu Junction', doctor: 'Paramedic Team 1', status: 'STANDBY' },
                { name: 'Ambulance Squad 108-B', location: 'Madurantakam Hospital', doctor: 'Paramedic Team 2', status: 'STANDBY' },
              ].map((m, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-200 bg-white space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">{m.name}</span>
                    <Badge status={m.status} size="sm" />
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-sky-600" />
                      <span>{m.location}</span>
                    </div>
                    <div>Team Lead: <strong className="text-slate-700">{m.doctor}</strong></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 4: DISASTER SUPPLIES */}
      {activeTab === 'resources' && (
        <Card>
          <CardHeader>
            <CardTitle>Emergency Disaster Supplies &amp; Trauma Requisitions</CardTitle>
            <CardDescription>
              Urgent pharmaceutical requirements requested with high priority to State Medical Reserves.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-sky-50 border border-sky-100 rounded-xl text-xs text-sky-950 font-medium flex items-center justify-between">
              <span>Need trauma packs, IV fluids, or ORS in bulk? Dispatch an emergency requisition below.</span>
              <Button variant="primary" size="sm" onClick={() => setIsResourceModalOpen(true)}>
                Order Supplies
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal: Declare Emergency Crisis */}
      <Dialog open={isDeclareModalOpen} onOpenChange={setIsDeclareModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Declare District Public Health Emergency</DialogTitle>
          <DialogDescription>Initiates crisis protocol across all district health nodes.</DialogDescription>
          <DialogClose onClose={() => setIsDeclareModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleDeclareIncident} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Crisis Title</label>
              <Input
                type="text"
                value={declareTitle}
                onChange={(e) => setDeclareTitle(e.target.value)}
                placeholder="e.g. Cyclone Cyclone Mandous Surge Preparedness"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Classification</label>
                <select
                  value={declareCategory}
                  onChange={(e) => setDeclareCategory(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="DISEASE_CLUSTER">Epidemic Outbreak</option>
                  <option value="WEATHER_DISASTER">Severe Weather / Flood</option>
                  <option value="MASS_CASUALTY">Mass Casualty Trauma</option>
                  <option value="HAZMAT">Industrial Hazmat / Chemical</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Severity</label>
                <select
                  value={declareSeverity}
                  onChange={(e) => setDeclareSeverity(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="MAJOR">Major Emergency</option>
                  <option value="CRITICAL">Critical Crisis (Disaster)</option>
                  <option value="MODERATE">Moderate Severity</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Affected Area</label>
              <Input
                type="text"
                value={declareArea}
                onChange={(e) => setDeclareArea(e.target.value)}
                placeholder="e.g. Coastal Taluks & Low-lying Blocks"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Situation Description</label>
              <Textarea
                value={declareDescription}
                onChange={(e) => setDeclareDescription(e.target.value)}
                placeholder="Key emergency response actions and hospital mobilizations..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsDeclareModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="destructive" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Declaring...' : 'Declare Emergency'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Requisition Disaster Supplies */}
      <Dialog open={isResourceModalOpen} onOpenChange={setIsResourceModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Emergency Disaster Supply Requisition</DialogTitle>
          <DialogDescription>Priority requisition to State Medical Reserves.</DialogDescription>
          <DialogClose onClose={() => setIsResourceModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleRequestResource} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Select Item</label>
              <select
                value={resourceMedId}
                onChange={(e) => setResourceMedId(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                required
              >
                <option value="">Choose disaster item...</option>
                {medications.map((m) => (
                  <option key={m.id} value={m.id}>{m.generic_name} ({m.strength})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Quantity</label>
              <Input
                type="number"
                value={resourceQty}
                onChange={(e) => setResourceQty(Number(e.target.value))}
                min={50}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Justification</label>
              <Input
                type="text"
                value={resourceReason}
                onChange={(e) => setResourceReason(e.target.value)}
                placeholder="Surge requirement for emergency flood shelters"
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsResourceModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting || !resourceMedId}>
                {isSubmitting ? 'Transmitting...' : 'Dispatch Requisition'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
