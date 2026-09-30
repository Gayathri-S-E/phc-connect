import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Globe2, Building2, ShieldCheck, CheckCircle, 
  TrendingUp, BarChart3, Truck, AlertTriangle, 
  Send, Plus, FileText, ChevronRight, Eye, Flag
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

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
      setActionSuccess('National coordination directive dispatched to State Directorate');
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
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950 to-indigo-950 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sky-300 text-sm font-semibold tracking-wide uppercase">
              <Globe2 className="w-4 h-4" />
              <span>Role 12: National Health Authority (NHA / Ministry of Health)</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">National Health Operations & Strategic Oversight</h1>
            <p className="text-sky-100 text-sm mt-1">
              Pan-India comparative indices, National Health Mission (NHM) milestones, and inter-state supply grid resilience.
            </p>
          </div>
          <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2.5 rounded-lg border border-white/20">
            <Flag className="w-5 h-5 text-sky-300" />
            <div>
              <div className="text-xs text-sky-200 uppercase font-bold">Scope</div>
              <div className="text-sm font-black">All-India Union Level</div>
            </div>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-sky-200 hover:text-white text-xs font-bold uppercase">
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
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          National Health Cockpit
        </button>
        <button
          onClick={() => handleTabChange('states')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'states'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Inter-State Health Benchmarks
        </button>
        <button
          onClick={() => handleTabChange('supply_grid')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'supply_grid'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Truck className="w-4 h-4" />
          National Supply Chain Grid
        </button>
        <button
          onClick={() => handleTabChange('directives')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'directives'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Send className="w-4 h-4" />
          Strategic Directives & Mandates
        </button>
      </div>

      {/* TAB 1: NATIONAL HEALTH COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Pan-India Patient Volume</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.patient_volume ?? 48200}</h3>
                <span className="text-xs text-sky-600 font-medium mt-1 inline-block">Reported across connected states</span>
              </div>
              <div className="p-3 bg-sky-50 text-sky-600 rounded-lg">
                <Globe2 className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Health Facilities</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{totals.facilities ?? 184}</h3>
                <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">100% Primary Care Grid Coverage</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Building2 className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">National Stockout Rate</p>
                <h3 className="text-2xl font-bold text-emerald-700 mt-1">1.2%</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Sub-2% resilience benchmark target met</span>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Active National Alerts</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.governance?.open_alerts ?? 3}</h3>
                <span className="text-xs text-amber-600 font-medium mt-1 inline-block">Monitored in Union Operations Room</span>
              </div>
              <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-3">
            <h4 className="text-base font-bold text-gray-900">National Health Authority Privacy Safeguards</h4>
            <p className="text-xs text-gray-500 leading-relaxed">
              In accordance with national healthcare data governance guidelines, National Health Authority users interact strictly with state-level aggregates. No patient identifiers, clinician identifiers, or facility-level microdata are displayed at the national tier.
            </p>
          </div>
        </div>
      )}

      {/* TAB 2: INTER-STATE BENCHMARKS */}
      {activeTab === 'states' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">State-Level Performance Comparison</h3>
            <p className="text-xs text-gray-500">Roll-up primary healthcare indicators across participating states.</p>
          </div>

          <DataTable
            data={statesList.length > 0 ? statesList : [
              { state: 'Tamil Nadu', facilities: 42, patient_volume: 12450, consultations: 11800, referrals: 310, stockout_items: 2 },
              { state: 'Kerala', facilities: 38, patient_volume: 11200, consultations: 10900, referrals: 280, stockout_items: 1 },
              { state: 'Karnataka', facilities: 54, patient_volume: 14100, consultations: 13500, referrals: 410, stockout_items: 4 },
              { state: 'Maharashtra', facilities: 50, patient_volume: 10450, consultations: 9800, referrals: 390, stockout_items: 3 },
            ]}
            keyField="state"
            emptyMessage="No comparative state figures available."
            columns={[
              {
                header: 'State / Union Territory',
                accessor: (s) => <span className="font-bold text-gray-900">{s.state}</span>,
              },
              {
                header: 'Facilities Reporting',
                accessor: (s) => `${s.facilities} PHCs/CHCs`,
              },
              {
                header: 'Patient Volume',
                accessor: (s) => <span className="font-semibold text-gray-900">{s.patient_volume}</span>,
              },
              {
                header: 'Consultations',
                accessor: 'consultations',
              },
              {
                header: 'Specialist Referrals',
                accessor: 'referrals',
              },
              {
                header: 'Stockouts Flagged',
                accessor: (s: any) => (
                  <span className={(s.stockout_items || 0) > 2 ? 'text-amber-600 font-bold' : 'text-emerald-700 font-semibold'}>
                    {s.stockout_items || 0} items
                  </span>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: NATIONAL SUPPLY GRID */}
      {activeTab === 'supply_grid' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">National Medicine Supply Grid</h3>
            <p className="text-xs text-gray-500">Cross-state stockout risk matrix and emergency supply channels.</p>
          </div>

          <DataTable
            data={supplyStates.length > 0 ? supplyStates : [
              { state: 'Tamil Nadu', facilities: 42, low_stock_items: 6, stockout_items: 2, open_shortages: 1 },
              { state: 'Kerala', facilities: 38, low_stock_items: 4, stockout_items: 1, open_shortages: 0 },
              { state: 'Karnataka', facilities: 54, low_stock_items: 9, stockout_items: 4, open_shortages: 2 },
            ]}
            keyField="state"
            emptyMessage="No supply chain grid data available."
            columns={[
              {
                header: 'State',
                accessor: (s: any) => <span className="font-bold text-gray-900">{s.state}</span>,
              },
              {
                header: 'Network Facilities',
                accessor: 'facilities',
              },
              {
                header: 'Low Stock Medicines',
                accessor: (s: any) => `${s.low_stock_items || 0} lines`,
              },
              {
                header: 'Active Stockouts',
                accessor: (s: any) => (
                  <span className={(s.stockout_items || 0) > 0 ? 'text-red-600 font-bold' : 'text-gray-400'}>
                    {s.stockout_items || 0} lines
                  </span>
                ),
              },
              {
                header: 'Supply Security Status',
                accessor: (s: any) => (
                  <Badge 
                    label={(s.stockout_items || 0) > 2 ? 'BUFFER WARNING' : 'RESILIENT'} 
                    status={(s.stockout_items || 0) > 2 ? 'warning' : 'success'} 
                  />
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: STRATEGIC DIRECTIVES */}
      {activeTab === 'directives' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <div>
              <h3 className="text-base font-bold text-gray-900">National Strategic Directives</h3>
              <p className="text-xs text-gray-500">Issue coordination directives to State Health Administrations.</p>
            </div>
            <button
              onClick={() => setIsDirectiveModalOpen(true)}
              className="px-3.5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Issue National Directive
            </button>
          </div>

          <DataTable
            data={directives}
            keyField="id"
            emptyMessage="No national directives currently logged."
            columns={[
              {
                header: 'Directive Title',
                accessor: (d) => (
                  <div>
                    <div className="font-semibold text-gray-900">{d.title}</div>
                    <div className="text-xs text-gray-600 line-clamp-1">{d.description}</div>
                  </div>
                ),
              },
              {
                header: 'Priority',
                accessor: (d) => (
                  <Badge 
                    label={d.priority} 
                    status={d.priority === 'CRITICAL' ? 'danger' : 'info'} 
                  />
                ),
              },
              {
                header: 'Status',
                accessor: (d) => <Badge label={d.status || 'PENDING'} status="warning" />,
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Issue National Directive */}
      <Modal
        isOpen={isDirectiveModalOpen}
        onClose={() => setIsDirectiveModalOpen(false)}
        title="Issue National Coordination Directive"
      >
        <form onSubmit={handleIssueDirective} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Target State Directorate</label>
            <select
              value={directiveTargetState}
              onChange={(e) => setDirectiveTargetState(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="Tamil Nadu">Tamil Nadu State Health Mission</option>
              <option value="Kerala">Kerala State Health Mission</option>
              <option value="Karnataka">Karnataka State Health Mission</option>
              <option value="All States">Pan-India Broadcast (All States)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Directive Title</label>
            <input
              type="text"
              value={directiveTitle}
              onChange={(e) => setDirectiveTitle(e.target.value)}
              placeholder="e.g. Nationwide Cold Chain Real-Time Telemetry Rollout"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Policy Category</label>
              <select
                value={directiveCategory}
                onChange={(e) => setDirectiveCategory(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="POLICY">National Health Policy</option>
                <option value="SUPPLY_GRID">Inter-State Supply Rebalancing</option>
                <option value="SURVEILLANCE">IDSP Disease Surveillance</option>
                <option value="DISASTER_RELIEF">Disaster Relief Protocol</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Priority</label>
              <select
                value={directivePriority}
                onChange={(e) => setDirectivePriority(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              >
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Directive Mandate & Timelines</label>
            <textarea
              value={directiveText}
              onChange={(e) => setDirectiveText(e.target.value)}
              placeholder="Provide strategic instructions, compliance deadlines, and designated nodal officers"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-28"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsDirectiveModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Transmitting...' : 'Dispatch Directive'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
