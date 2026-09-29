import React, { useState, useEffect } from 'react';
import { 
  Truck, Package, AlertTriangle, CheckCircle, 
  Send, ShieldCheck, ArrowRightLeft, Clock, 
  Plus, Eye, FileText, ChevronRight, Layers, 
  AlertCircle, ShieldAlert, Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function DistrictSupplyPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [activeTab, setActiveTab] = useState<'requests' | 'transfers' | 'warehouse' | 'impacts' | 'receipts'>('requests');
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
  const [isShareImpactModalOpen, setIsShareImpactModalOpen] = useState(false);
  const [impactTitle, setImpactTitle] = useState('');
  const [impactClinicalConsequence, setImpactClinicalConsequence] = useState('');
  const [impactAlternative, setImpactAlternative] = useState('');
  const [impactFacilityId, setImpactFacilityId] = useState('');

  // Receipts / Discrepancies
  const [receipts, setReceipts] = useState<any[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchSupplyData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [reqRes, transfersRes, stockRes, impactsRes, receiptsRes, medsRes] = await Promise.all([
        api.get<any>('/supply-requests?page_size=50').catch(() => ({ data: [] })),
        api.get<any[]>('/transfers').catch(() => ({ data: [] })),
        api.get<any>('/inventory?page_size=100').catch(() => ({ data: { items: [] } })),
        api.get<any>('/supply-impacts?page_size=50').catch(() => ({ data: [] })),
        api.get<any>('/supply-receipts?page_size=50').catch(() => ({ data: [] })),
        api.get<any[]>('/medications').catch(() => ({ data: [] })),
      ]);

      if (reqRes?.data) {
        setRequests(Array.isArray(reqRes.data) ? reqRes.data : reqRes.data.items || []);
      }
      if (transfersRes?.data) setTransfers(transfersRes.data);
      if (stockRes?.data) {
        setWarehouseStock(Array.isArray(stockRes.data) ? stockRes.data : stockRes.data.items || []);
      }
      if (impactsRes?.data) {
        setSupplyImpacts(Array.isArray(impactsRes.data) ? impactsRes.data : impactsRes.data.items || []);
      }
      if (receiptsRes?.data) {
        setReceipts(Array.isArray(receiptsRes.data) ? receiptsRes.data : receiptsRes.data.items || []);
      }
      if (medsRes?.data) {
        setMedications(medsRes.data);
        if (medsRes.data.length > 0 && !newTransferMedId) {
          setNewTransferMedId(medsRes.data[0].id);
        }
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load district supply chain data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSupplyData();
  }, []);

  // Submit Decision on PHC Request
  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;
    setIsSubmitting(true);
    try {
      await api.post(`/supply-requests/${selectedRequest.id}/decision`, {
        action: decisionOutcome,
        approved_quantity: decisionOutcome === 'APPROVED' ? (approvedQuantity || selectedRequest.requested_quantity) : undefined,
        reason: decisionReason || 'Reviewed and adjudicated by DSCO',
      });
      setActionSuccess(`Request ${selectedRequest.request_number} updated to ${decisionOutcome}`);
      setIsDecisionModalOpen(false);
      fetchSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to submit decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Human-Authorized Stock Allocation
  const handleAllocateStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;
    setIsSubmitting(true);
    try {
      await api.post(`/supply-requests/${selectedRequest.id}/allocate`, {
        allocated_quantity: Number(allocatedQty),
        notes: allocationNotes || 'Stock allocated from District Drug Warehouse (DDW)',
      });
      setActionSuccess(`Stock allocated for ${selectedRequest.request_number}`);
      setIsAllocateModalOpen(false);
      fetchSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to allocate stock');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Escalate to State Warehouse
  const handleEscalateToState = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequest) return;
    setIsSubmitting(true);
    try {
      await api.post(`/supply-requests/${selectedRequest.id}/escalate`, {
        reason: escalationReason,
        requested_quantity: Number(escalationQty || selectedRequest.requested_quantity),
      });
      setActionSuccess(`Request escalated to State Central Warehouse`);
      setIsEscalateModalOpen(false);
      fetchSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to escalate request');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Dispatch Stock Transfer
  const handleDispatchTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransferForDispatch) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/transfers/${selectedTransferForDispatch.id}/dispatch`, {
        dispatched_quantity: Number(dispatchQty),
        notes: dispatchNotes || 'Consignment dispatched via district medical transport',
      });
      setActionSuccess(`Transfer ${selectedTransferForDispatch.transfer_number} dispatched`);
      setIsDispatchModalOpen(false);
      fetchSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to dispatch transfer');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Share Clinical Health Impact Notice with DHO
  const handleShareImpact = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/supply-impacts', {
        title: impactTitle,
        clinical_consequence: impactClinicalConsequence,
        recommended_alternative: impactAlternative,
        facility_id: impactFacilityId || undefined,
      });
      setActionSuccess('Clinical health impact notice communicated to District Health Officer');
      setIsShareImpactModalOpen(false);
      setImpactTitle('');
      setImpactClinicalConsequence('');
      setImpactAlternative('');
      fetchSupplyData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to share health impact notice');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading District Supply Chain & Resilience Dashboard..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchSupplyData} />;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-sky-800 to-cyan-950 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sky-200 text-sm font-semibold tracking-wide uppercase">
              <Truck className="w-4 h-4" />
              <span>Role 07: District Supply Chain Officer (DSCO)</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">District Supply Chain & Medicine Redistribution</h1>
            <p className="text-sky-100 text-sm mt-1">
              Adjudicate PHC medicine indents, execute inter-facility stock rebalancing, and mitigate stockouts across the district.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-3 rounded-lg border border-white/20">
            <Package className="w-5 h-5 text-sky-200" />
            <div>
              <div className="text-xs text-sky-200 uppercase font-bold">Open PHC Indents</div>
              <div className="text-xl font-black">
                {requests.filter(r => r.status === 'SUBMITTED' || r.status === 'PENDING_REVIEW').length}
              </div>
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
          onClick={() => setActiveTab('requests')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'requests'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Package className="w-4 h-4" />
          PHC Medicine Indents
          {requests.filter(r => r.status === 'SUBMITTED' || r.status === 'PENDING_REVIEW').length > 0 && (
            <span className="bg-sky-100 text-sky-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {requests.filter(r => r.status === 'SUBMITTED' || r.status === 'PENDING_REVIEW').length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('transfers')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'transfers'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ArrowRightLeft className="w-4 h-4" />
          Stock Transfers & Dispatch
        </button>
        <button
          onClick={() => setActiveTab('warehouse')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'warehouse'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Layers className="w-4 h-4" />
          District Warehouse Stock
        </button>
        <button
          onClick={() => setActiveTab('impacts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'impacts'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Clinical Shortage Notices
        </button>
        <button
          onClick={() => setActiveTab('receipts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'receipts'
              ? 'border-sky-600 text-sky-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          Transit Receipts & Discrepancies
        </button>
      </div>

      {/* TAB 1: PHC MEDICINE INDENTS */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">PHC Supply Indents Review Queue</h3>
              <p className="text-xs text-gray-500">Approve, allocate from warehouse buffer, or escalate to State Central Warehouse.</p>
            </div>
            <button
              onClick={fetchSupplyData}
              className="text-xs font-semibold text-sky-700 hover:text-sky-800 px-3 py-1.5 bg-sky-50 rounded-lg"
            >
              Refresh Indents
            </button>
          </div>

          <DataTable
            data={requests}
            keyField="id"
            emptyMessage="No pending supply indents from primary health centres."
            columns={[
              {
                header: 'Indent Number',
                accessor: (r) => (
                  <div>
                    <div className="font-mono font-bold text-gray-900">{r.request_number}</div>
                    <div className="text-xs text-gray-400">{r.facility_name || 'Primary Health Centre'}</div>
                  </div>
                ),
              },
              {
                header: 'Medicine Required',
                accessor: (r) => (
                  <div>
                    <div className="font-semibold text-gray-900">{r.medication_name || 'Standard Consignment'}</div>
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
                    status={r.status === 'ALLOCATED' || r.status === 'FULFILLED' ? 'success' : r.status === 'REJECTED' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Actions',
                accessor: (r) => (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => {
                        setSelectedRequest(r);
                        setApprovedQuantity(r.requested_quantity);
                        setIsDecisionModalOpen(true);
                      }}
                      className="px-2.5 py-1 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 rounded text-xs font-semibold transition"
                    >
                      Decision
                    </button>
                    {r.status === 'APPROVED' && (
                      <button
                        onClick={() => {
                          setSelectedRequest(r);
                          setAllocatedQty(r.approved_quantity || r.requested_quantity);
                          setIsAllocateModalOpen(true);
                        }}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold transition"
                      >
                        Allocate
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setSelectedRequest(r);
                        setEscalationQty(r.requested_quantity);
                        setIsEscalateModalOpen(true);
                      }}
                      className="px-2.5 py-1 bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 rounded text-xs font-semibold transition"
                    >
                      Escalate
                    </button>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 2: STOCK TRANSFERS & DISPATCH */}
      {activeTab === 'transfers' && (
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Inter-Facility Stock Transfers & Dispatch</h3>
              <p className="text-xs text-gray-500">Rebalance surplus stocks from high-inventory PHCs to deficit centres.</p>
            </div>
            <button
              onClick={() => setIsCreateTransferModalOpen(true)}
              className="px-3.5 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition"
            >
              <Plus className="w-4 h-4" />
              New Rebalance Transfer
            </button>
          </div>

          <DataTable
            data={transfers}
            keyField="id"
            emptyMessage="No stock transfers recorded in this district."
            columns={[
              {
                header: 'Transfer Number',
                accessor: (t) => <span className="font-mono font-bold text-gray-900">{t.transfer_number}</span>,
              },
              {
                header: 'Medicine',
                accessor: (t) => t.medication?.name || 'Assigned Item',
              },
              {
                header: 'Quantity',
                accessor: (t) => `${t.requested_quantity} units`,
              },
              {
                header: 'Status',
                accessor: (t) => (
                  <Badge 
                    label={t.status} 
                    status={t.status === 'RECEIVED' ? 'success' : t.status === 'IN_TRANSIT' ? 'info' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (t) => (
                  t.status === 'APPROVED' ? (
                    <button
                      onClick={() => {
                        setSelectedTransferForDispatch(t);
                        setDispatchQty(t.requested_quantity);
                        setIsDispatchModalOpen(true);
                      }}
                      className="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-semibold"
                    >
                      Dispatch Now
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">{t.status}</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: WAREHOUSE STOCK */}
      {activeTab === 'warehouse' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">District Drug Warehouse (DDW) Stock Balances</h3>
              <p className="text-xs text-gray-500">Central buffer inventory for primary healthcare distribution.</p>
            </div>
            <div className="text-xs text-gray-500 font-medium">
              Tracked Items: {warehouseStock.length}
            </div>
          </div>

          <DataTable
            data={warehouseStock}
            keyField="id"
            emptyMessage="No stock inventory recorded in district warehouse."
            columns={[
              {
                header: 'Medication',
                accessor: (item) => (
                  <div>
                    <div className="font-semibold text-gray-900">{item.generic_name || item.medication?.name}</div>
                    <div className="text-xs text-gray-400">{item.brand_name || 'NEML'}</div>
                  </div>
                ),
              },
              {
                header: 'Quantity on Hand',
                accessor: (item) => (
                  <span className="font-bold text-gray-900">{item.quantity_on_hand} units</span>
                ),
              },
              {
                header: 'Reorder Level',
                accessor: 'reorder_level',
              },
              {
                header: 'Status',
                accessor: (item) => (
                  <Badge 
                    label={item.quantity_on_hand <= item.reorder_level ? 'Low Reserve' : 'Adequate'} 
                    status={item.quantity_on_hand <= item.reorder_level ? 'warning' : 'success'} 
                  />
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: CLINICAL SHORTAGE NOTICES */}
      {activeTab === 'impacts' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Clinical Shortage Impact Notices</h3>
              <p className="text-xs text-gray-500">
                Inform the District Health Officer (DHO) about critical shortages that affect clinical treatment.
              </p>
            </div>
            <button
              onClick={() => setIsShareImpactModalOpen(true)}
              className="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Issue Shortage Notice to DHO
            </button>
          </div>

          <DataTable
            data={supplyImpacts}
            keyField="id"
            emptyMessage="No clinical shortage notices active in this district."
            columns={[
              {
                header: 'Shortage Notice',
                accessor: (imp) => (
                  <div>
                    <div className="font-semibold text-gray-900">{imp.title}</div>
                    <div className="text-xs text-gray-600">{imp.clinical_consequence}</div>
                  </div>
                ),
              },
              {
                header: 'Recommended Alternative',
                accessor: (imp) => imp.recommended_alternative || 'Clinical consultation required',
              },
              {
                header: 'Date Shared',
                accessor: (imp) => new Date(imp.created_at).toLocaleDateString(),
              },
              {
                header: 'DHO Acknowledgement',
                accessor: (imp) => (
                  <Badge 
                    label={imp.acknowledged_by ? 'Acknowledged by DHO' : 'Awaiting DHO Review'} 
                    status={imp.acknowledged_by ? 'success' : 'warning'} 
                  />
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 5: TRANSIT RECEIPTS & DISCREPANCIES */}
      {activeTab === 'receipts' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Transit Verification & Discrepancy Audits</h3>
            <p className="text-xs text-gray-500">Reconciled consignments: physical delivery vs dispatched quantity.</p>
          </div>

          <DataTable
            data={receipts}
            keyField="id"
            emptyMessage="No receipt discrepancy logs found."
            columns={[
              {
                header: 'Receipt ID',
                accessor: (r) => <span className="font-mono font-bold text-gray-900">{r.id.slice(0, 8)}</span>,
              },
              {
                header: 'Dispatched vs Received',
                accessor: (r) => (
                  <div>
                    <span className="font-semibold text-gray-900">{r.received_quantity} received</span>
                    <span className="text-xs text-gray-500"> / {r.dispatched_quantity} dispatched</span>
                  </div>
                ),
              },
              {
                header: 'Damaged Units',
                accessor: (r) => (
                  <span className={r.damaged_quantity > 0 ? 'text-red-600 font-bold' : 'text-gray-400'}>
                    {r.damaged_quantity} units
                  </span>
                ),
              },
              {
                header: 'Verification Status',
                accessor: (r) => (
                  <Badge 
                    label={r.verification_status} 
                    status={r.verification_status === 'VERIFIED' ? 'success' : 'danger'} 
                  />
                ),
              },
              {
                header: 'Discrepancy Notes',
                accessor: (r) => r.discrepancy_reason || 'Verified 100% matched',
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Adjudicate PHC Indent */}
      <Modal
        isOpen={isDecisionModalOpen}
        onClose={() => setIsDecisionModalOpen(false)}
        title={`Adjudicate Indent — ${selectedRequest?.request_number}`}
      >
        <form onSubmit={handleSubmitDecision} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-500">Facility:</span>
              <span className="font-semibold">{selectedRequest?.facility_name || 'PHC'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Medicine:</span>
              <span className="font-semibold">{selectedRequest?.medication_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Requested:</span>
              <span className="font-bold">{selectedRequest?.requested_quantity} units</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Decision Determination</label>
            <select
              value={decisionOutcome}
              onChange={(e) => setDecisionOutcome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="APPROVED">Approve Full Requirement</option>
              <option value="PARTIALLY_APPROVED">Partially Approve (Buffer Constraint)</option>
              <option value="REJECTED">Reject Requirement</option>
              <option value="REQUEST_CLARIFICATION">Request Clinical Clarification</option>
            </select>
          </div>

          {(decisionOutcome === 'APPROVED' || decisionOutcome === 'PARTIALLY_APPROVED') && (
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Approved Quantity</label>
              <input
                type="number"
                value={approvedQuantity}
                onChange={(e) => setApprovedQuantity(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Decision Justification / Notes</label>
            <textarea
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              placeholder="State rationale for approval or partial quota"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsDecisionModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Saving...' : 'Submit Decision'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Allocate Warehouse Stock */}
      <Modal
        isOpen={isAllocateModalOpen}
        onClose={() => setIsAllocateModalOpen(false)}
        title={`Allocate Stock — ${selectedRequest?.request_number}`}
      >
        <form onSubmit={handleAllocateStock} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Allocation Quantity</label>
            <input
              type="number"
              value={allocatedQty}
              onChange={(e) => setAllocatedQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Allocation Dispatch Instructions</label>
            <textarea
              value={allocationNotes}
              onChange={(e) => setAllocationNotes(e.target.value)}
              placeholder="e.g. Allocated from Batch DDW-2026-A1; dispatch via route 4 van"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
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
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Allocating...' : 'Authorize Allocation'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Escalate to State Warehouse */}
      <Modal
        isOpen={isEscalateModalOpen}
        onClose={() => setIsEscalateModalOpen(false)}
        title={`Escalate to State Warehouse — ${selectedRequest?.request_number}`}
      >
        <form onSubmit={handleEscalateToState} className="space-y-4">
          <p className="text-xs text-gray-600">
            Transmit this medicine indent directly to the State Central Warehouse (SCW) manager when district inventory is exhausted.
          </p>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Escalated Requirement (Units)</label>
            <input
              type="number"
              value={escalationQty}
              onChange={(e) => setEscalationQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Escalation Justification</label>
            <textarea
              value={escalationReason}
              onChange={(e) => setEscalationReason(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsEscalateModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Escalating...' : 'Transmit to State Manager'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Dispatch Transfer */}
      <Modal
        isOpen={isDispatchModalOpen}
        onClose={() => setIsDispatchModalOpen(false)}
        title={`Dispatch Stock Consignment — ${selectedTransferForDispatch?.transfer_number}`}
      >
        <form onSubmit={handleDispatchTransfer} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Dispatched Quantity</label>
            <input
              type="number"
              value={dispatchQty}
              onChange={(e) => setDispatchQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Vehicle / Courier Manifest Notes</label>
            <input
              type="text"
              value={dispatchNotes}
              onChange={(e) => setDispatchNotes(e.target.value)}
              placeholder="e.g. Handed to Driver Murugan, Vehicle TN-19-G-4411"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsDispatchModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Dispatching...' : 'Mark Dispatched'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Share Clinical Impact with DHO */}
      <Modal
        isOpen={isShareImpactModalOpen}
        onClose={() => setIsShareImpactModalOpen(false)}
        title="Notify District Health Officer of Critical Shortage"
      >
        <form onSubmit={handleShareImpact} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Shortage Notice Headline</label>
            <input
              type="text"
              value={impactTitle}
              onChange={(e) => setImpactTitle(e.target.value)}
              placeholder="e.g. Critical Depletion of Anti-Rabies Vaccine (ARV) in Sector 2"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Clinical Impact on Patient Care</label>
            <textarea
              value={impactClinicalConsequence}
              onChange={(e) => setImpactClinicalConsequence(e.target.value)}
              placeholder="Describe clinical ramifications, risk of referral overload, or delayed immunization"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Recommended Therapeutic Alternative</label>
            <input
              type="text"
              value={impactAlternative}
              onChange={(e) => setImpactAlternative(e.target.value)}
              placeholder="e.g. Intradermal regimen at Sub-District Hospital or alternate brand"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsShareImpactModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Transmitting...' : 'Alert DHO'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
