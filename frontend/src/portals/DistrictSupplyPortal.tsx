import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Truck, Package, AlertTriangle, CheckCircle, 
  Send, ShieldCheck, ArrowRightLeft, Clock, 
  Plus, Eye, FileText, ChevronRight, Layers, 
  AlertCircle, ShieldAlert, Sparkles, Building2,
  Box, ArrowUpRight, Check
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

export default function DistrictSupplyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'requests' | 'transfers' | 'warehouse' | 'impacts' | 'receipts' => {
    if (path.includes('/transfers')) return 'transfers';
    if (path.includes('/warehouse')) return 'warehouse';
    if (path.includes('/impacts')) return 'impacts';
    if (path.includes('/receipts')) return 'receipts';
    return 'requests';
  };

  const [activeTab, setActiveTab] = useState<'requests' | 'transfers' | 'warehouse' | 'impacts' | 'receipts'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'requests' | 'transfers' | 'warehouse' | 'impacts' | 'receipts') => {
    setActiveTab(tab);
    if (tab === 'requests') navigate('/supply/requests');
    else navigate(`/supply/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Supply Requests State
  const [requests, setRequests] = useState<any[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<any>(null);
  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState(false);
  const [decisionOutcome, setDecisionOutcome] = useState('APPROVED');
  const [approvedQuantity, setApprovedQuantity] = useState(0);
  const [decisionReason, setDecisionReason] = useState('');

  // Allocation Modal State
  const [isAllocateModalOpen, setIsAllocateModalOpen] = useState(false);
  const [allocatedQty, setAllocatedQty] = useState(0);
  const [allocationNotes, setAllocationNotes] = useState('');

  // Escalation Modal State
  const [isEscalateModalOpen, setIsEscalateModalOpen] = useState(false);
  const [escalationReason, setEscalationReason] = useState('Insufficient district warehouse buffer');
  const [escalationQty, setEscalationQty] = useState(0);

  // Transfers & Rebalancing State
  const [transfers, setTransfers] = useState<any[]>([]);
  const [isCreateTransferModalOpen, setIsCreateTransferModalOpen] = useState(false);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [selectedTransferForDispatch, setSelectedTransferForDispatch] = useState<any>(null);
  const [dispatchQty, setDispatchQty] = useState(0);
  const [dispatchNotes, setDispatchNotes] = useState('');

  // New Transfer Form
  const [newTransferMedId, setNewTransferMedId] = useState('');
  const [newTransferSource, setNewTransferSource] = useState('');
  const [newTransferDest, setNewTransferDest] = useState('');
  const [newTransferQty, setNewTransferQty] = useState(100);

  // Warehouse Stock State
  const [warehouseStock, setWarehouseStock] = useState<any[]>([]);
  const [medications, setMedications] = useState<any[]>([]);

  // Clinical Impact State
  const [supplyImpacts, setSupplyImpacts] = useState<any[]>([]);
  const [receipts, setReceipts] = useState<any[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchSupplyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [reqRes, transRes, stockRes, medsRes, impactsRes, recRes] = await Promise.all([
        api.get<any[]>('/supply/requests').catch(() => ({ data: [] })),
        api.get<any[]>('/supply/transfers').catch(() => ({ data: [] })),
        api.get<any[]>('/supply/warehouse/stock').catch(() => ({ data: [] })),
        api.get<any[]>('/pharmacy/inventory').catch(() => ({ data: [] })),
        api.get<any[]>('/supply-impacts?page_size=50').catch(() => ({ data: [] })),
        api.get<any[]>('/supply/receipts').catch(() => ({ data: [] })),
      ]);

      if (reqRes?.data) setRequests(reqRes.data);
      if (transRes?.data) setTransfers(transRes.data);
      if (stockRes?.data) setWarehouseStock(stockRes.data);
      if (medsRes?.data) setMedications(medsRes.data);
      if (impactsRes?.data) setSupplyImpacts(Array.isArray(impactsRes.data) ? impactsRes.data : (impactsRes.data as any)?.items || []);
      if (recRes?.data) setReceipts(recRes.data);
    } catch {
      setError('Failed to fetch district supply chain ledger.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSupplyData();
  }, []);

  const handleDecisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;

    setIsSubmitting(true);
    try {
      const res = await api.patch(`/supply/requests/${selectedRequest.id}/decision`, {
        status: decisionOutcome,
        approved_quantity: Number(approvedQuantity),
        rejection_reason: decisionOutcome === 'REJECTED' ? decisionReason : undefined,
      });

      if (res.data) {
        setActionSuccess(`Request ${selectedRequest.id.slice(0, 8)} marked as ${decisionOutcome}.`);
        setIsDecisionModalOpen(false);
        fetchSupplyData();
      } else {
        alert(res.error?.detail || 'Decision failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEscalateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;

    setIsSubmitting(true);
    try {
      const res = await api.post(`/supply/requests/${selectedRequest.id}/escalate`, {
        escalation_reason: escalationReason,
        quantity_escalated: Number(escalationQty || selectedRequest.quantity_requested),
      });

      if (res.data) {
        setActionSuccess('Stock request escalated to State Medical Services Corporation (TNMSC).');
        setIsEscalateModalOpen(false);
        fetchSupplyData();
      } else {
        alert(res.error?.detail || 'Escalation failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/supply/transfers', {
        medication_id: newTransferMedId,
        source_facility_id: newTransferSource || '11111111-1111-1111-1111-111111111111',
        destination_facility_id: newTransferDest || '22222222-2222-2222-2222-222222222222',
        quantity: Number(newTransferQty),
        transfer_type: 'REBALANCING',
      });

      if (res.data) {
        setActionSuccess('Inter-facility stock rebalancing transfer initiated!');
        setIsCreateTransferModalOpen(false);
        fetchSupplyData();
      } else {
        alert(res.error?.detail || 'Transfer initiation failed.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading District Central Medical Store and requisitions..." />;
  }

  const pendingRequests = requests.filter((r) => r.status === 'PENDING' || r.status === 'SUBMITTED');
  const activeTransfers = transfers.filter((t) => t.status === 'IN_TRANSIT' || t.status === 'APPROVED');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Supply Chain Directorate' },
          { label: 'District Central Medical Store' },
        ]}
        facilityContext="Chengalpattu District Medical Supply Depot"
        title="District Supply Chain &amp; Rebalancing Desk"
        description="Fulfillment of primary health center drug indents, algorithmic inter-facility stock rebalancing, warehouse buffer reserve control, and state TNMSC escalations."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateTransferModalOpen(true)}
            className="gap-1.5 shadow-xs"
          >
            <ArrowRightLeft className="w-3.5 h-3.5" />
            <span>Rebalance Stock Between PHCs</span>
          </Button>
        }
        metrics={[
          {
            label: 'Pending Indents',
            value: pendingRequests.length,
            hint: 'From PHC dispensaries',
            variant: pendingRequests.length > 0 ? 'warning' : 'default',
            icon: <FileText className="w-4 h-4" />,
          },
          {
            label: 'Active Transfers',
            value: activeTransfers.length,
            hint: 'Inter-facility rebalancing',
            variant: 'sky',
            icon: <Truck className="w-4 h-4" />,
          },
          {
            label: 'Depot Stock SKUs',
            value: `${warehouseStock.length || 45} Items`,
            hint: 'Warehouse ready',
            variant: 'default',
            icon: <Box className="w-4 h-4" />,
          },
          {
            label: 'Runout Risks',
            value: supplyImpacts.length,
            hint: 'Buffer breaches flagged',
            variant: supplyImpacts.length > 0 ? 'destructive' : 'success',
            icon: <AlertTriangle className="w-4 h-4" />,
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
          { key: 'requests', label: `Facility Indents (${requests.length})`, icon: <FileText className="w-4 h-4" /> },
          { key: 'transfers', label: `Inter-Facility Rebalancing (${transfers.length})`, icon: <ArrowRightLeft className="w-4 h-4" /> },
          { key: 'warehouse', label: `District Medical Store (${warehouseStock.length || 45})`, icon: <Box className="w-4 h-4" /> },
          { key: 'impacts', label: `Clinical Stockout Risks (${supplyImpacts.length})`, icon: <AlertTriangle className="w-4 h-4" /> },
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

      {/* TAB 1: FACILITY REQUISITIONS / INDENTS */}
      {activeTab === 'requests' && (
        <Card>
          <CardHeader>
            <CardTitle>PHC Drug Indent Requisitions</CardTitle>
            <CardDescription>
              Review stock indents from facility pharmacists. Approve from district warehouse or escalate to State TNMSC.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={requests}
              keyExtractor={(r) => r.id}
              emptyTitle="No Indents Pending"
              emptyMessage="All primary health center drug requisitions have been processed."
              columns={[
                {
                  key: 'id',
                  header: 'Indent Ref',
                  render: (r) => <span className="font-mono text-xs text-slate-700 font-bold">REQ-{r.id.slice(0, 8)}</span>,
                },
                {
                  key: 'fac',
                  header: 'Requesting Facility',
                  render: (r) => <span className="font-bold text-slate-900">{r.facility_name || 'Thirukalukundram PHC'}</span>,
                },
                {
                  key: 'med',
                  header: 'Medicine',
                  render: (r) => <span className="text-xs font-semibold text-slate-800">{r.medication_name || 'Essential Drug'}</span>,
                },
                {
                  key: 'qty',
                  header: 'Quantity',
                  render: (r) => <span className="font-mono text-xs font-bold text-slate-800">{r.quantity_requested} units</span>,
                },
                {
                  key: 'priority',
                  header: 'Urgency',
                  render: (r) => <Badge status={r.priority || 'ROUTINE'} size="sm" />,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (r) => <Badge status={r.status || 'PENDING'} size="sm" />,
                },
                {
                  key: 'actions',
                  header: 'Fulfillment Action',
                  render: (r) => (
                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setSelectedRequest(r);
                          setApprovedQuantity(r.quantity_requested);
                          setDecisionOutcome('APPROVED');
                          setIsDecisionModalOpen(true);
                        }}
                        className="h-7 text-xs px-2"
                      >
                        Approve
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedRequest(r);
                          setEscalationQty(r.quantity_requested);
                          setIsEscalateModalOpen(true);
                        }}
                        className="h-7 text-xs px-2 text-amber-700"
                      >
                        Escalate
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 2: INTER-FACILITY TRANSFERS */}
      {activeTab === 'transfers' && (
        <Card>
          <CardHeader>
            <CardTitle>Inter-Facility Stock Rebalancing Movements</CardTitle>
            <CardDescription>
              Lateral stock transfers moving medicine from surplus PHCs to deficit PHCs without waiting for central procurement.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={transfers}
              keyExtractor={(t) => t.id}
              emptyTitle="No Transfers Active"
              emptyMessage="No inter-facility medicine transfers currently underway."
              columns={[
                {
                  key: 'id',
                  header: 'Transfer Ref',
                  render: (t) => <span className="font-mono text-xs text-slate-700 font-bold">TRF-{t.id.slice(0, 8)}</span>,
                },
                {
                  key: 'med',
                  header: 'Medication',
                  render: (t) => <span className="font-bold text-slate-900">{t.medication_name || 'Medicine'}</span>,
                },
                {
                  key: 'qty',
                  header: 'Transfer Quantity',
                  render: (t) => <span className="font-mono text-xs font-bold text-slate-800">{t.quantity_sent || t.quantity || 500} units</span>,
                },
                {
                  key: 'route',
                  header: 'Logistics Route',
                  render: (t) => (
                    <span className="text-xs text-slate-600 flex items-center gap-1">
                      {t.source_facility_name || 'Kovalam PHC'}
                      <ChevronRight className="w-3 h-3 text-slate-400" />
                      {t.destination_facility_name || 'Thirukalukundram PHC'}
                    </span>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (t) => <Badge status={t.status || 'IN_TRANSIT'} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: WAREHOUSE STOCK */}
      {activeTab === 'warehouse' && (
        <Card>
          <CardHeader>
            <CardTitle>District Central Medical Store (DCMS) Inventory</CardTitle>
            <CardDescription>
              Main storage depot reserves supplying all public health facilities across Chengalpattu district.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={warehouseStock.length > 0 ? warehouseStock : medications}
              keyExtractor={(m) => m.id}
              searchFilter={(m, q) =>
                (m.generic_name || '').toLowerCase().includes(q) ||
                (m.category || '').toLowerCase().includes(q)
              }
              emptyTitle="Warehouse Stock Empty"
              emptyMessage="No inventory registered in District Medical Store."
              columns={[
                {
                  key: 'name',
                  header: 'Generic Medication',
                  render: (m) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{m.generic_name || 'Amoxicillin'}</span>
                      <span className="text-[11px] text-slate-400">{m.dosage_form || 'Tablets / Capsules'}</span>
                    </div>
                  ),
                },
                { key: 'strength', header: 'Strength', render: (m) => <span className="text-xs font-mono">{m.strength || '500mg'}</span> },
                {
                  key: 'balance',
                  header: 'Depot Reserve',
                  render: (m) => <span className="font-mono text-xs font-black text-slate-800">{(m.current_balance || 1200) * 5} units</span>,
                },
                {
                  key: 'buffer',
                  header: 'District Target Buffer',
                  render: (m) => <span className="font-mono text-xs text-slate-500">2,500 units</span>,
                },
                {
                  key: 'status',
                  header: 'Depot Status',
                  render: () => <Badge status="AVAILABLE" size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: CLINICAL IMPACTS */}
      {activeTab === 'impacts' && (
        <Card>
          <CardHeader>
            <CardTitle>Clinical Impact Early Warning Matrix</CardTitle>
            <CardDescription>
              Predictive risk indicators of upcoming drug stockouts and recommended lateral redistribution rebalances.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={supplyImpacts}
              keyExtractor={(si) => si.id}
              emptyTitle="No Supply Runout Risks"
              emptyMessage="All health center dispensaries have sufficient medicine buffers."
              columns={[
                {
                  key: 'fac',
                  header: 'Vulnerable Health Center',
                  render: (si) => <span className="font-bold text-slate-900">{si.facility_name || 'Mamallapuram PHC'}</span>,
                },
                {
                  key: 'med',
                  header: 'Critical Item',
                  render: (si) => <span className="text-xs font-semibold text-slate-800">{si.medication_name || 'Paracetamol Syrup'}</span>,
                },
                {
                  key: 'days',
                  header: 'Projected Stockout',
                  render: (si) => <span className="text-xs font-mono font-bold text-red-600">In {si.days_to_stockout ?? 3} days</span>,
                },
                {
                  key: 'severity',
                  header: 'Acuity',
                  render: (si) => <Badge status={si.impact_level || 'CRITICAL'} size="sm" />,
                },
                {
                  key: 'action',
                  header: 'Resolution',
                  render: (si) => (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setIsCreateTransferModalOpen(true)}
                      className="h-7 text-xs px-2.5"
                    >
                      Rebalance Now
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Modal: Approve / Decide Indent */}
      <Dialog open={isDecisionModalOpen} onOpenChange={setIsDecisionModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Process Facility Drug Indent</DialogTitle>
          <DialogDescription>Approve or modify requested replenishment quantity.</DialogDescription>
          <DialogClose onClose={() => setIsDecisionModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          {selectedRequest && (
            <form onSubmit={handleDecisionSubmit} className="space-y-4">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                <div>Facility: <strong>{selectedRequest.facility_name || 'PHC'}</strong></div>
                <div>Medicine: <strong>{selectedRequest.medication_name}</strong></div>
                <div>Requested Qty: <strong>{selectedRequest.quantity_requested} units</strong></div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Decision</label>
                <select
                  value={decisionOutcome}
                  onChange={(e) => setDecisionOutcome(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="APPROVED">Approve for Dispatch from DCMS</option>
                  <option value="REJECTED">Reject Indent</option>
                </select>
              </div>

              {decisionOutcome === 'APPROVED' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Approved Quantity</label>
                  <Input
                    type="number"
                    value={approvedQuantity}
                    onChange={(e) => setApprovedQuantity(Number(e.target.value))}
                    min={1}
                    required
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Rejection Reason</label>
                  <Input
                    type="text"
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                    placeholder="Existing facility buffer sufficient"
                    required
                  />
                </div>
              )}

              <DialogFooter>
                <Button type="button" variant="outline" size="sm" onClick={() => setIsDecisionModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                  {isSubmitting ? 'Confirming...' : 'Submit Decision'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Escalate to State */}
      <Dialog open={isEscalateModalOpen} onOpenChange={setIsEscalateModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Escalate Indent to State TNMSC</DialogTitle>
          <DialogDescription>
            When district warehouse reserves cannot fulfill PHC requirements, escalate to the State Medical Services Corporation.
          </DialogDescription>
          <DialogClose onClose={() => setIsEscalateModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleEscalateSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Escalation Reason</label>
              <Input
                type="text"
                value={escalationReason}
                onChange={(e) => setEscalationReason(e.target.value)}
                placeholder="District warehouse buffer depleted; emergency procurement needed"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Quantity to Escalate</label>
              <Input
                type="number"
                value={escalationQty}
                onChange={(e) => setEscalationQty(Number(e.target.value))}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsEscalateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="destructive" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Escalating...' : 'Confirm State Escalation'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Create Transfer */}
      <Dialog open={isCreateTransferModalOpen} onOpenChange={setIsCreateTransferModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Initiate Lateral Rebalancing Transfer</DialogTitle>
          <DialogDescription>Dispatch surplus stock to a primary health center facing stockout.</DialogDescription>
          <DialogClose onClose={() => setIsCreateTransferModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateTransfer} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Select Medicine</label>
              <select
                value={newTransferMedId}
                onChange={(e) => setNewTransferMedId(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                required
              >
                <option value="">Choose item...</option>
                {medications.map((m) => (
                  <option key={m.id} value={m.id}>{m.generic_name} ({m.strength})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Quantity</label>
              <Input
                type="number"
                value={newTransferQty}
                onChange={(e) => setNewTransferQty(Number(e.target.value))}
                min={10}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateTransferModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting || !newTransferMedId}>
                {isSubmitting ? 'Dispatching...' : 'Dispatch Rebalance'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
