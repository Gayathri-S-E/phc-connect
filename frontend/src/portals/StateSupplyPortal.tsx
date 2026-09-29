import React, { useState, useEffect } from 'react';
import { 
  Truck, Package, AlertTriangle, CheckCircle, 
  Send, ShieldCheck, Play, ArrowRightLeft, 
  Layers, Clock, Plus, Eye, FileText, ChevronRight,
  TrendingDown, ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function StateSupplyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [activeTab, setActiveTab] = useState<'cockpit' | 'escalated' | 'warehouse' | 'monitoring' | 'shortages'>('cockpit');
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
      setActionSuccess(`Automated scan complete: ${res.data?.alerts_created ?? 0} alerts evaluated`);
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
      setActionSuccess(`State allocation confirmed for ${selectedRequest.request_number}`);
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
      setActionSuccess(`Shortage incident ${selectedShortage.id.slice(0, 8)} marked as resolved`);
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
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 to-cyan-950 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-200 text-sm font-semibold tracking-wide uppercase">
              <Truck className="w-4 h-4" />
              <span>Role 10: State Supply Chain / Warehouse Manager</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">State Central Warehouse (SCW) & Supply Grid</h1>
            <p className="text-cyan-100 text-sm mt-1">
              Statewide bulk drug reserves, manufacturer procurement quotas, district escalations, and automated shortage surveillance.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRunMonitoring}
              disabled={isRunningMonitor}
              className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 shadow-lg transition"
            >
              <Play className="w-4 h-4 fill-white" />
              {isRunningMonitor ? 'Scanning Grid...' : 'Run Supply Engine'}
            </button>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-cyan-200 hover:text-white text-xs font-bold uppercase">
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
              ? 'border-cyan-600 text-cyan-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Layers className="w-4 h-4" />
          State Supply Cockpit
        </button>
        <button
          onClick={() => setActiveTab('escalated')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'escalated'
              ? 'border-cyan-600 text-cyan-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Package className="w-4 h-4" />
          Escalated District Indents
          {escalatedRequests.length > 0 && (
            <span className="bg-cyan-100 text-cyan-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {escalatedRequests.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('warehouse')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'warehouse'
              ? 'border-cyan-600 text-cyan-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Truck className="w-4 h-4" />
          State Central Reserve Stock
        </button>
        <button
          onClick={() => setActiveTab('monitoring')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'monitoring'
              ? 'border-cyan-600 text-cyan-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Rule-Based Monitor Results
        </button>
        <button
          onClick={() => setActiveTab('shortages')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'shortages'
              ? 'border-cyan-600 text-cyan-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Critical Shortages
        </button>
      </div>

      {/* TAB 1: STATE SUPPLY COCKPIT */}
      {activeTab === 'cockpit' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Central Warehouse Reserves</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.warehouse_stock ?? 450000}</h3>
                <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">Units across 65 essential lines</span>
              </div>
              <div className="p-3 bg-cyan-50 text-cyan-600 rounded-lg">
                <Layers className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">District Escalations</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.district_requests ?? escalatedRequests.length}</h3>
                <span className="text-xs text-amber-600 font-medium mt-1 inline-block">Awaiting State buffer release</span>
              </div>
              <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                <Package className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Consignments In Transit</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{dashboardData?.in_transit ?? 12}</h3>
                <span className="text-xs text-blue-600 font-medium mt-1 inline-block">En-route to District Warehouses</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Truck className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Discrepancy Flags</p>
                <h3 className={`text-2xl font-bold mt-1 ${dashboardData?.discrepancies > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                  {dashboardData?.discrepancies ?? 1}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Damaged or missing in transit</span>
              </div>
              <div className={`p-3 rounded-lg ${dashboardData?.discrepancies > 0 ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-600'}`}>
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Automated Supply Grid Surveillance</h4>
              <p className="text-xs text-gray-500 mb-4 leading-relaxed">
                The continuous rule engine evaluates consumption velocity at every PHC. If a facility consumes faster than its standard monthly burn rate, an early shortage notice is created automatically.
              </p>
              <button
                onClick={handleRunMonitoring}
                disabled={isRunningMonitor}
                className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                {isRunningMonitor ? 'Executing Surveillance...' : 'Trigger Full Network Scan Now'}
              </button>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-2">Statewide Near-Expiry Redistribution</h4>
              <p className="text-xs text-gray-500 mb-4 leading-relaxed">
                Items approaching expiry within 60 days in low-volume PHCs are flagged for urgent reverse-logistics or transfer to high-volume District Headquarters Hospitals.
              </p>
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 font-semibold flex items-center justify-between">
                <span>Near-Expiry Units Monitored:</span>
                <span className="font-bold text-amber-800">{dashboardData?.near_expiry ?? 1420} units</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ESCALATED DISTRICT INDENTS */}
      {activeTab === 'escalated' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">District Escalated Medicine Indents</h3>
            <p className="text-xs text-gray-500">Demands requiring State Central Warehouse (SCW) reserve allocation.</p>
          </div>

          <DataTable
            data={escalatedRequests}
            keyField="id"
            emptyMessage="No escalated requirements currently logged from district drug warehouses."
            columns={[
              {
                header: 'Indent Number',
                accessor: (r) => (
                  <div>
                    <div className="font-mono font-bold text-gray-900">{r.request_number}</div>
                    <div className="text-xs text-gray-400">{r.facility_name || 'District Drug Warehouse'}</div>
                  </div>
                ),
              },
              {
                header: 'Medicine',
                accessor: (r) => (
                  <div>
                    <div className="font-semibold text-gray-900">{r.medication_name || 'Essential Medicine'}</div>
                    <div className="text-xs text-gray-500">Req: {r.requested_quantity} units</div>
                  </div>
                ),
              },
              {
                header: 'Priority',
                accessor: (r) => (
                  <Badge 
                    label={r.priority} 
                    status={r.priority === 'EMERGENCY' ? 'danger' : r.priority === 'URGENT' ? 'warning' : 'info'} 
                  />
                ),
              },
              {
                header: 'Status',
                accessor: (r) => (
                  <Badge 
                    label={r.status} 
                    status={r.status === 'ALLOCATED' ? 'success' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (r) => (
                  <button
                    onClick={() => {
                      setSelectedRequest(r);
                      setAllocatedQty(r.requested_quantity);
                      setIsAllocateModalOpen(true);
                    }}
                    className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 text-white rounded text-xs font-semibold"
                  >
                    Allocate from SCW
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: STATE WAREHOUSE STOCK */}
      {activeTab === 'warehouse' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">State Central Warehouse Reserve Balances</h3>
            <p className="text-xs text-gray-500">Master inventory holding for state-wide distribution.</p>
          </div>

          <DataTable
            data={warehouseStock}
            keyField="id"
            emptyMessage="No stock inventory registered at State Central Warehouse."
            columns={[
              {
                header: 'Medication',
                accessor: (item) => (
                  <div>
                    <div className="font-semibold text-gray-900">{item.generic_name || item.medication?.name}</div>
                    <div className="text-xs text-gray-400">{item.brand_name || 'TN-NEML Standard'}</div>
                  </div>
                ),
              },
              {
                header: 'Central Reserve Stock',
                accessor: (item) => (
                  <span className="font-bold text-gray-900">{item.quantity_on_hand} units</span>
                ),
              },
              {
                header: 'Minimum Buffer',
                accessor: 'reorder_level',
              },
              {
                header: 'Status',
                accessor: (item) => (
                  <Badge 
                    label={item.quantity_on_hand <= item.reorder_level ? 'Buffer Depleted' : 'Healthy Buffer'} 
                    status={item.quantity_on_hand <= item.reorder_level ? 'warning' : 'success'} 
                  />
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: MONITORING RUN RESULTS */}
      {activeTab === 'monitoring' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Supply Surveillance Engine Output</h3>
              <p className="text-xs text-gray-500">Automated multi-tier scan results evaluating supply security.</p>
            </div>
            <button
              onClick={handleRunMonitoring}
              disabled={isRunningMonitor}
              className="px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white rounded text-xs font-semibold flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              Re-Scan
            </button>
          </div>

          {monitoringResults ? (
            <div className="p-4 bg-gray-50 rounded-lg border text-xs space-y-2">
              <div className="font-bold text-gray-900">Scan Execution Succeeded:</div>
              <div className="text-gray-700">Alerts Created: {monitoringResults.alerts_created ?? 0}</div>
              <div className="text-gray-500 font-mono">Timestamp: {new Date().toISOString()}</div>
            </div>
          ) : (
            <p className="text-xs text-gray-500 italic">
              Click 'Run Supply Engine' to execute a live scan of all PHC consumption rates across the state.
            </p>
          )}
        </div>
      )}

      {/* TAB 5: SHORTAGES */}
      {activeTab === 'shortages' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Active Shortage Incidents</h3>
            <p className="text-xs text-gray-500">Unresolved stockouts escalated across district boundaries.</p>
          </div>

          <DataTable
            data={shortages}
            keyField="id"
            emptyMessage="No critical shortage incidents requiring state intervention."
            columns={[
              {
                header: 'Incident ID',
                accessor: (s) => <span className="font-mono font-bold text-gray-900">{s.id?.slice(0, 8)}</span>,
              },
              {
                header: 'Medicine',
                accessor: (s) => s.medication_name || 'Essential Medicine',
              },
              {
                header: 'Status',
                accessor: (s) => <Badge label={s.status || 'REPORTED'} status={s.status === 'RESOLVED' ? 'success' : 'danger'} />,
              },
              {
                header: 'Action',
                accessor: (s) => (
                  s.status !== 'RESOLVED' ? (
                    <button
                      onClick={() => {
                        setSelectedShortage(s);
                        setResolutionNotes('');
                        setIsResolveModalOpen(true);
                      }}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                    >
                      Resolve
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 italic">Resolved</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Resolve Shortage */}
      <Modal
        isOpen={isResolveModalOpen}
        onClose={() => setIsResolveModalOpen(false)}
        title={`Resolve Shortage Incident — ${selectedShortage?.id?.slice(0, 8)}`}
      >
        <form onSubmit={handleResolveShortage} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Resolution Notes</label>
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="e.g. Emergency buffer stock dispatched from State Central Warehouse (SCW); inventory levels replenished above safety threshold."
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Provide clear audit documentation for closing this shortage incident.</p>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsResolveModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Resolving...' : 'Confirm Incident Resolution'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Allocate from SCW */}
      <Modal
        isOpen={isAllocateModalOpen}
        onClose={() => setIsAllocateModalOpen(false)}
        title={`Allocate State Reserve — ${selectedRequest?.request_number}`}
      >
        <form onSubmit={handleAllocateStateStock} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Quantity from State Central Warehouse</label>
            <input
              type="number"
              value={allocatedQty}
              onChange={(e) => setAllocatedQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">State Dispatch Notes</label>
            <textarea
              value={allocationNotes}
              onChange={(e) => setAllocationNotes(e.target.value)}
              placeholder="e.g. Authorized from Batch SCW-TN-2026-X; assign to District Logistics truck"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsAllocateModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Allocating...' : 'Authorize State Allocation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
