import React, { useState, useEffect } from 'react';
import { 
  Pill, AlertTriangle, CheckCircle, Clock, 
  Send, Search, ShieldCheck, ChevronRight, 
  Package, Truck, BookOpen, AlertCircle, Plus,
  Layers, Check, Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

export default function PharmacistPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [activeTab, setActiveTab] = useState<'dispense' | 'alerts' | 'inventory' | 'transfers' | 'druginfo'>('dispense');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const facilityId = user?.facility_id || '11111111-1111-1111-1111-111111111111';

  // Dispense Queue State
  const [dispenseQueue, setDispenseQueue] = useState<any[]>([]);
  const [selectedRx, setSelectedRx] = useState<any>(null);
  const [isDispenseModalOpen, setIsDispenseModalOpen] = useState(false);
  const [dispenseNotes, setDispenseNotes] = useState('');
  const [dispenseSuccess, setDispenseSuccess] = useState<any>(null);

  // Counselling Note State
  const [isCounsellingModalOpen, setIsCounsellingModalOpen] = useState(false);
  const [counsellingSummary, setCounsellingSummary] = useState('');
  const [counsellingLang, setCounsellingLang] = useState('TAMIL');
  const [patientUnderstood, setPatientUnderstood] = useState(true);
  const [followUpRecommended, setFollowUpRecommended] = useState(false);
  const [followUpNotes, setFollowUpNotes] = useState('');

  // Stock Alerts State
  const [stockAlerts, setStockAlerts] = useState<any[]>([]);

  // Inventory Items State
  const [inventoryItems, setInventoryItems] = useState<any[]>([]);

  // Transfers & Inbound Receipts
  const [transfers, setTransfers] = useState<any[]>([]);
  const [selectedTransfer, setSelectedTransfer] = useState<any>(null);
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
  const [receivedQty, setReceivedQty] = useState(0);
  const [damagedQty, setDamagedQty] = useState(0);
  const [receiptBatchNo, setReceiptBatchNo] = useState('');
  const [receiptExpiry, setReceiptExpiry] = useState('');
  const [discrepancyReason, setDiscrepancyReason] = useState('');

  // Supply Request Modal
  const [isSupplyRequestModalOpen, setIsSupplyRequestModalOpen] = useState(false);
  const [selectedMedForRequest, setSelectedMedForRequest] = useState<any>(null);
  const [requestedQty, setRequestedQty] = useState(500);
  const [requestPriority, setRequestPriority] = useState('ROUTINE');
  const [requestJustification, setRequestJustification] = useState('');

  // Drug Info AI State
  const [medicationsList, setMedicationsList] = useState<any[]>([]);
  const [selectedMedIdForInfo, setSelectedMedIdForInfo] = useState('');
  const [drugQueryType, setDrugQueryType] = useState('general');
  const [drugInfoResult, setDrugInfoResult] = useState<any>(null);
  const [isQueryingDrugInfo, setIsQueryingDrugInfo] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchPharmacistData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [queueRes, alertsRes, invRes, transfersRes, medsRes] = await Promise.all([
        api.get<any[]>(`/pharmacist/prescriptions/pending?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any[]>(`/pharmacist/stock-alerts?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any>(`/inventory?facility_id=${facilityId}&page_size=100`).catch(() => ({ data: { items: [] } })),
        api.get<any[]>(`/transfers?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any[]>('/medications').catch(() => ({ data: [] })),
      ]);

      if (queueRes?.data) setDispenseQueue(queueRes.data);
      if (alertsRes?.data) setStockAlerts(alertsRes.data);
      if (invRes?.data) {
        setInventoryItems(Array.isArray(invRes.data) ? invRes.data : invRes.data.items || []);
      }
      if (transfersRes?.data) setTransfers(transfersRes.data);
      if (medsRes?.data) {
        setMedicationsList(medsRes.data);
        if (medsRes.data.length > 0 && !selectedMedIdForInfo) {
          setSelectedMedIdForInfo(medsRes.data[0].id);
        }
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load pharmacy data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPharmacistData();
  }, [facilityId]);

  // Execute Atomic FEFO Dispensing
  const handleDispenseFEFO = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRx) return;
    setIsSubmitting(true);
    try {
      const payload = {
        items: selectedRx.items.map((item: any) => ({
          prescription_item_id: item.prescription_item_id,
          quantity: item.quantity_remaining > 0 ? item.quantity_remaining : item.quantity_prescribed,
        })),
        notes: dispenseNotes || 'Dispensed via FEFO protocol at primary dispensary',
      };

      const res = await api.post(`/prescriptions/${selectedRx.prescription_id}/dispense-fefo`, payload);
      setDispenseSuccess(res.data);
      setActionSuccess(`Prescription dispensed successfully for ${selectedRx.patient_name}`);
      setIsDispenseModalOpen(false);

      // Offer patient counselling note recording
      setCounsellingSummary(`Patient counseled on dosages for ${selectedRx.items.map((i: any) => i.medication_name).join(', ')}. Warned about side effects.`);
      setIsCounsellingModalOpen(true);

      fetchPharmacistData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to dispense prescription. Check stock availability.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Counselling Note
  const handleSubmitCounselling = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRx) return;
    setIsSubmitting(true);
    try {
      await api.post('/pharmacist/patient-counselling', {
        prescription_id: selectedRx.prescription_id,
        patient_id: selectedRx.patient_id || '00000000-0000-0000-0000-000000000000',
        counselling_summary: counsellingSummary,
        language_used: counsellingLang,
        patient_understood: patientUnderstood,
        follow_up_recommended: followUpRecommended,
        follow_up_notes: followUpNotes || undefined,
      });
      setActionSuccess('Counselling audit trail saved');
      setIsCounsellingModalOpen(false);
      setSelectedRx(null);
    } catch (err: any) {
      alert(err?.detail || 'Failed to save counselling note');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Receive Transfer with Discrepancy Verification
  const handleReceiveTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransfer) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/transfers/${selectedTransfer.id}/receive`, {
        received_quantity: Number(receivedQty),
        damaged_quantity: Number(damagedQty),
        batch_number: receiptBatchNo || undefined,
        expiry_date: receiptExpiry || undefined,
        discrepancy_reason: discrepancyReason || undefined,
        notes: 'Verified and received by PHC Pharmacist',
      });
      setActionSuccess(`Stock transfer ${selectedTransfer.transfer_number} received & stock updated`);
      setIsReceiveModalOpen(false);
      setSelectedTransfer(null);
      fetchPharmacistData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to receive transfer');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Raise Supply Request to District Warehouse
  const handleRaiseSupplyRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMedForRequest) return;
    setIsSubmitting(true);
    try {
      await api.post('/supply-requests', {
        medication_id: selectedMedForRequest.medication_id || selectedMedForRequest.id,
        requested_quantity: Number(requestedQty),
        priority: requestPriority,
        clinical_justification: requestJustification || 'Replenishment for depleted dispensary stock buffer',
      });
      setActionSuccess(`Indent raised for ${selectedMedForRequest.medication_name || selectedMedForRequest.name}`);
      setIsSupplyRequestModalOpen(false);
      setSelectedMedForRequest(null);
      setRequestJustification('');
      fetchPharmacistData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to raise supply request');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Query Drug Info AI
  const handleQueryDrugInfo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMedIdForInfo) return;
    setIsQueryingDrugInfo(true);
    try {
      const res = await api.post<any>('/pharmacist/drug-info', {
        medication_id: selectedMedIdForInfo,
        query_type: drugQueryType,
      });
      if (res.data) setDrugInfoResult(res.data);
    } catch (err: any) {
      alert(err?.detail || 'Failed to fetch drug information');
    } finally {
      setIsQueryingDrugInfo(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading dispensary pharmacy portal..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchPharmacistData} />;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-800 to-indigo-900 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-blue-200 text-sm font-semibold tracking-wide uppercase">
              <Pill className="w-4 h-4" />
              <span>Role 05: Dispensary Pharmacist</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">Dispensary Stock & Prescription Dispenser</h1>
            <p className="text-blue-100 text-sm mt-1">
              Zero-leakage FEFO batch fulfillment, low-stock reorder automation, and bilingual Tamil Nadu drug formulary.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-3 rounded-lg border border-white/20">
            <Package className="w-5 h-5 text-blue-200" />
            <div>
              <div className="text-xs text-blue-200 uppercase font-bold">Pending Dispense</div>
              <div className="text-lg font-black">{dispenseQueue.length} Prescriptions</div>
            </div>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-blue-200 hover:text-white text-xs font-bold uppercase">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-4 rounded-lg shadow-sm overflow-x-auto">
        <button
          onClick={() => setActiveTab('dispense')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'dispense'
              ? 'border-blue-600 text-blue-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Clock className="w-4 h-4" />
          Pending Dispense Queue
          {dispenseQueue.length > 0 && (
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {dispenseQueue.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'alerts'
              ? 'border-blue-600 text-blue-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          Stock Shortage & Expiry Alerts
          {stockAlerts.length > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {stockAlerts.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('inventory')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'inventory'
              ? 'border-blue-600 text-blue-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Layers className="w-4 h-4" />
          Stock-On-Hand Registry
        </button>
        <button
          onClick={() => setActiveTab('transfers')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'transfers'
              ? 'border-blue-600 text-blue-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Truck className="w-4 h-4" />
          Inbound Transfers & Receipts
        </button>
        <button
          onClick={() => setActiveTab('druginfo')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'druginfo'
              ? 'border-blue-600 text-blue-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Drug Formulary AI (Tamil / EN)
        </button>
      </div>

      {/* TAB 1: PENDING DISPENSE QUEUE */}
      {activeTab === 'dispense' && (
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Physician Prescriptions Awaiting Fulfillment</h3>
              <p className="text-xs text-gray-500">Atomic stock deduction using First-Expire-First-Out (FEFO) batch priority.</p>
            </div>
            <button
              onClick={fetchPharmacistData}
              className="text-xs font-semibold text-blue-700 hover:text-blue-800 px-3 py-1.5 bg-blue-50 rounded-lg"
            >
              Refresh Queue
            </button>
          </div>

          <DataTable
            data={dispenseQueue}
            keyField="prescription_id"
            emptyMessage="No pending prescriptions in the dispensary queue."
            columns={[
              {
                header: 'Patient',
                accessor: (rx) => (
                  <div>
                    <div className="font-semibold text-gray-900">{rx.patient_name}</div>
                    <div className="text-xs text-gray-400 font-mono">{rx.patient_identifier || 'ID: Assigned'}</div>
                  </div>
                ),
              },
              {
                header: 'Doctor',
                accessor: (rx) => (
                  <span className="text-sm font-medium text-gray-700">{rx.doctor_name}</span>
                ),
              },
              {
                header: 'Issued At',
                accessor: (rx) => new Date(rx.issued_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              },
              {
                header: 'Prescribed Items',
                accessor: (rx) => (
                  <div className="space-y-1">
                    {rx.items?.map((item: any, idx: number) => (
                      <div key={idx} className="text-xs flex items-center gap-1.5 text-gray-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                        <span className="font-medium">{item.medication_name}</span>
                        <span className="text-gray-500">({item.quantity_prescribed} units)</span>
                      </div>
                    ))}
                  </div>
                ),
              },
              {
                header: 'Action',
                accessor: (rx) => (
                  <button
                    onClick={() => {
                      setSelectedRx(rx);
                      setIsDispenseModalOpen(true);
                    }}
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                  >
                    <Pill className="w-3.5 h-3.5" />
                    Dispense FEFO
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 2: STOCK ALERTS & SHORTAGES */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Critical Medicine Stock & Expiry Watchlist</h3>
              <p className="text-xs text-gray-500">Items below minimum stock levels or expiring within 30 days.</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-800 rounded-lg border border-amber-200">
              Auto-monitored by Rule Engine
            </span>
          </div>

          <DataTable
            data={stockAlerts}
            keyField="inventory_item_id"
            emptyMessage="All medicines are above reorder threshold. No immediate shortage risks."
            columns={[
              {
                header: 'Medication',
                accessor: (alert) => (
                  <div>
                    <div className="font-semibold text-gray-900">{alert.medication_name}</div>
                    <div className="text-xs text-gray-400">Reorder Level: {alert.reorder_level} units</div>
                  </div>
                ),
              },
              {
                header: 'Current Stock',
                accessor: (alert) => (
                  <span className={`font-black text-sm ${alert.quantity_on_hand === 0 ? 'text-red-600' : 'text-amber-600'}`}>
                    {alert.quantity_on_hand} units
                  </span>
                ),
              },
              {
                header: 'Risk Classification',
                accessor: (alert) => (
                  <Badge 
                    label={alert.stock_status} 
                    status={alert.stock_status === 'OUT_OF_STOCK' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Near-Expiry (≤30 Days)',
                accessor: (alert) => (
                  <span className={alert.near_expiry_quantity > 0 ? 'text-red-600 font-bold text-xs' : 'text-gray-400 text-xs'}>
                    {alert.near_expiry_quantity > 0 ? `${alert.near_expiry_quantity} units expiring!` : 'None'}
                  </span>
                ),
              },
              {
                header: 'Replenishment Action',
                accessor: (alert) => (
                  <button
                    onClick={() => {
                      setSelectedMedForRequest(alert);
                      setIsSupplyRequestModalOpen(true);
                    }}
                    className="px-3 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded text-xs font-semibold flex items-center gap-1 transition"
                  >
                    <Send className="w-3 h-3" />
                    Raise Indent
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: INVENTORY STOCK-ON-HAND */}
      {activeTab === 'inventory' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-gray-900">Dispensary Stock-On-Hand</h3>
              <p className="text-xs text-gray-500">Live physical stock balances at this facility.</p>
            </div>
            <div className="text-xs text-gray-500 font-medium">
              Total Catalog Items: {inventoryItems.length}
            </div>
          </div>

          <DataTable
            data={inventoryItems}
            keyField="id"
            emptyMessage="No stock inventory registered at this facility."
            columns={[
              {
                header: 'Medication',
                accessor: (item) => (
                  <div>
                    <div className="font-semibold text-gray-900">{item.generic_name || item.medication?.name}</div>
                    <div className="text-xs text-gray-400">{item.brand_name || 'Generic NEML'}</div>
                  </div>
                ),
              },
              {
                header: 'Dosage Form',
                accessor: (item) => `${item.dosage_form || 'Tablet'} ${item.strength || ''}`,
              },
              {
                header: 'Quantity on Hand',
                accessor: (item) => (
                  <span className="font-bold text-gray-900">{item.quantity_on_hand}</span>
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
                    label={item.quantity_on_hand <= item.reorder_level ? 'Low Stock' : 'Adequate'} 
                    status={item.quantity_on_hand <= item.reorder_level ? 'warning' : 'success'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (item) => (
                  <button
                    onClick={() => {
                      setSelectedMedForRequest({
                        medication_id: item.medication_id,
                        medication_name: item.generic_name || item.medication?.name,
                      });
                      setIsSupplyRequestModalOpen(true);
                    }}
                    className="text-xs font-semibold text-blue-700 hover:text-blue-800"
                  >
                    Request Stock +
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 4: INBOUND TRANSFERS & RECEIPTS */}
      {activeTab === 'transfers' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Inbound Stock Shipments & Physical Receipts</h3>
            <p className="text-xs text-gray-500">Reconcile dispatched quantities against actual physical delivery.</p>
          </div>

          <DataTable
            data={transfers}
            keyField="id"
            emptyMessage="No inbound stock transfers recorded for this facility."
            columns={[
              {
                header: 'Transfer Number',
                accessor: (t) => <span className="font-mono font-bold text-gray-900">{t.transfer_number}</span>,
              },
              {
                header: 'Medicine',
                accessor: (t) => t.medication?.name || 'General Batch Consignment',
              },
              {
                header: 'Dispatched Qty',
                accessor: (t) => `${t.dispatched_quantity || t.requested_quantity} units`,
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
                  t.status === 'IN_TRANSIT' ? (
                    <button
                      onClick={() => {
                        setSelectedTransfer(t);
                        setReceivedQty(t.dispatched_quantity || t.requested_quantity);
                        setDamagedQty(0);
                        setIsReceiveModalOpen(true);
                      }}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold"
                    >
                      Verify Receipt
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 font-medium">Reconciled</span>
                  )
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 5: DRUG INFORMATION AI (TAMIL / EN) */}
      {activeTab === 'druginfo' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Tamil Nadu State Essential Medicines Formulary & Drug Information AI
            </h3>
            <p className="text-xs text-gray-500 mb-4">
              Access bilingual clinical pharmacology, drug-drug interaction warnings, storage criteria, and Tamil patient counselling points.
            </p>

            <form onSubmit={handleQueryDrugInfo} className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Select Medicine</label>
                <select
                  value={selectedMedIdForInfo}
                  onChange={(e) => setSelectedMedIdForInfo(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                  required
                >
                  {medicationsList.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.strength})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Query Focus</label>
                <select
                  value={drugQueryType}
                  onChange={(e) => setDrugQueryType(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                >
                  <option value="general">General Clinical Profile</option>
                  <option value="interactions">Drug-Drug Interactions</option>
                  <option value="storage">Storage & Cold Chain Protocol</option>
                  <option value="counselling_points">Patient Counselling Points</option>
                  <option value="substitution">TN-NEML Generic Substitution</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={isQueryingDrugInfo}
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition"
                >
                  <Sparkles className="w-4 h-4 text-blue-200" />
                  {isQueryingDrugInfo ? 'Consulting Knowledge Base...' : 'Query Formulary AI'}
                </button>
              </div>
            </form>
          </div>

          {/* Drug Info Result Display */}
          {drugInfoResult && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5 animate-fade-in">
              <div className="flex items-start justify-between border-b pb-4">
                <div>
                  <h4 className="text-xl font-bold text-gray-900">{drugInfoResult.medication_name}</h4>
                  <span className="text-xs uppercase tracking-wider font-semibold text-blue-600">
                    Topic: {drugInfoResult.query_type}
                  </span>
                </div>
                <div className="text-xs font-bold px-3 py-1 bg-blue-50 text-blue-800 rounded-full border border-blue-200">
                  TN-NEML Certified
                </div>
              </div>

              {/* Warnings alert if any */}
              {drugInfoResult.warnings?.length > 0 && (
                <div className="p-4 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-sm">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Clinical Safety Warnings & Contraindications:
                  </div>
                  <ul className="list-disc list-inside text-xs pl-2 space-y-1">
                    {drugInfoResult.warnings.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Bilingual Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h5 className="font-bold text-gray-900 text-sm mb-2 flex items-center gap-1.5">
                    English Clinical Information
                  </h5>
                  <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                    {drugInfoResult.information_en}
                  </p>
                  {drugInfoResult.counselling_points_en?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-xs font-bold text-gray-800 mb-1">Counselling Guidance:</div>
                      <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                        {drugInfoResult.counselling_points_en.map((p: string, i: number) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="p-4 bg-blue-50/50 rounded-lg border border-blue-200">
                  <h5 className="font-bold text-blue-900 text-sm mb-2 flex items-center gap-1.5">
                    தமிழ் நோயாளி ஆலோசனை வழிகாட்டுதல் (Tamil Translation)
                  </h5>
                  <p className="text-xs text-gray-800 leading-relaxed whitespace-pre-line font-tamil">
                    {drugInfoResult.information_ta}
                  </p>
                  {drugInfoResult.counselling_points_ta?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <div className="text-xs font-bold text-blue-900 mb-1">நோயாளிக்கு விளக்க வேண்டியவை:</div>
                      <ul className="list-disc list-inside text-xs text-gray-700 space-y-1 font-tamil">
                        {drugInfoResult.counselling_points_ta.map((p: string, i: number) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* MODAL: FEFO Dispensing Confirmation */}
      <Modal
        isOpen={isDispenseModalOpen}
        onClose={() => setIsDispenseModalOpen(false)}
        title={`Dispense Prescription — ${selectedRx?.patient_name}`}
      >
        <form onSubmit={handleDispenseFEFO} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-xs space-y-1.5 border">
            <div className="flex justify-between">
              <span className="text-gray-500">Patient Identifier:</span>
              <span className="font-mono font-bold">{selectedRx?.patient_identifier || 'Auto-generated'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Prescribing Doctor:</span>
              <span className="font-semibold">{selectedRx?.doctor_name}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2">FEFO Allocation Preview</label>
            <div className="space-y-3">
              {selectedRx?.items?.map((item: any, i: number) => (
                <div key={i} className="p-3 bg-blue-50/40 border border-blue-100 rounded-lg text-xs">
                  <div className="flex justify-between font-bold text-gray-900 mb-1">
                    <span>{item.medication_name} ({item.dosage})</span>
                    <span>Prescribed: {item.quantity_prescribed} units</span>
                  </div>
                  {item.fefo_batches?.length > 0 ? (
                    <div className="text-gray-600 mt-1">
                      <span className="font-medium text-emerald-700">Allocated Batch:</span> {item.fefo_batches[0].batch_number} (Exp: {item.fefo_batches[0].expiry_date}, Avail: {item.fefo_batches[0].available_quantity})
                    </div>
                  ) : (
                    <span className="text-amber-600 font-medium">⚠️ No batch detected. Will auto-allocate from facility FEFO pool.</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Dispensing Notes</label>
            <input
              type="text"
              value={dispenseNotes}
              onChange={(e) => setDispenseNotes(e.target.value)}
              placeholder="e.g. Dispensed complete 5-day course"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsDispenseModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Dispensing...' : 'Confirm & Deduct Stock'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Record Medication Counselling Note */}
      <Modal
        isOpen={isCounsellingModalOpen}
        onClose={() => setIsCounsellingModalOpen(false)}
        title="Record Medication Counselling Note"
      >
        <form onSubmit={handleSubmitCounselling} className="space-y-4">
          <p className="text-xs text-gray-600">
            Confirm that patient or attendant received dosage, timing, and storage instructions.
          </p>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Counselling Language</label>
            <select
              value={counsellingLang}
              onChange={(e) => setCounsellingLang(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2 text-sm"
            >
              <option value="TAMIL">Tamil (தமிழ்)</option>
              <option value="ENGLISH">English</option>
              <option value="BILINGUAL">Bilingual (Tamil + English)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Summary of Advice Given</label>
            <textarea
              value={counsellingSummary}
              onChange={(e) => setCounsellingSummary(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="patientUnderstood"
              checked={patientUnderstood}
              onChange={(e) => setPatientUnderstood(e.target.checked)}
              className="rounded text-blue-600"
            />
            <label htmlFor="patientUnderstood" className="text-xs font-medium text-gray-700">
              Patient/attendant clearly understood dosage schedule and administration instructions
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsCounsellingModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Skip
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Saving...' : 'Save Counselling Audit'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Verify Inbound Stock Receipt */}
      <Modal
        isOpen={isReceiveModalOpen}
        onClose={() => setIsReceiveModalOpen(false)}
        title={`Verify Inbound Receipt — ${selectedTransfer?.transfer_number}`}
      >
        <form onSubmit={handleReceiveTransfer} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Dispatched Quantity</label>
              <input
                type="text"
                disabled
                value={`${selectedTransfer?.dispatched_quantity || selectedTransfer?.requested_quantity} units`}
                className="w-full bg-gray-100 border border-gray-300 rounded-lg p-2 text-sm font-bold text-gray-600"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Physically Received Qty</label>
              <input
                type="number"
                value={receivedQty}
                onChange={(e) => setReceivedQty(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2 text-sm font-bold"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Damaged Units (If Any)</label>
              <input
                type="number"
                value={damagedQty}
                onChange={(e) => setDamagedQty(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2 text-sm font-bold text-red-600"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Batch Number on Package</label>
              <input
                type="text"
                value={receiptBatchNo}
                onChange={(e) => setReceiptBatchNo(e.target.value)}
                placeholder="e.g. BATCH-2026-X1"
                className="w-full border border-gray-300 rounded-lg p-2 text-sm"
              />
            </div>
          </div>

          {receivedQty + damagedQty < (selectedTransfer?.dispatched_quantity || selectedTransfer?.requested_quantity) && (
            <div>
              <label className="block text-xs font-bold text-red-700 uppercase mb-1">
                Discrepancy Explanation (Shortage in transit)
              </label>
              <textarea
                value={discrepancyReason}
                onChange={(e) => setDiscrepancyReason(e.target.value)}
                placeholder="State reasons for missing units"
                className="w-full border border-red-300 rounded-lg p-2 text-sm h-16 bg-red-50/30"
                required
              />
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsReceiveModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Verifying...' : 'Confirm Receipt'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Raise Supply Request / Indent */}
      <Modal
        isOpen={isSupplyRequestModalOpen}
        onClose={() => setIsSupplyRequestModalOpen(false)}
        title={`Raise Replenishment Indent — ${selectedMedForRequest?.medication_name}`}
      >
        <form onSubmit={handleRaiseSupplyRequest} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Requested Quantity (Units)</label>
            <input
              type="number"
              value={requestedQty}
              onChange={(e) => setRequestedQty(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Indent Urgency</label>
            <select
              value={requestPriority}
              onChange={(e) => setRequestPriority(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="ROUTINE">ROUTINE (Standard monthly replenishment)</option>
              <option value="URGENT">URGENT (Stockout impending within 7 days)</option>
              <option value="EMERGENCY">EMERGENCY (Immediate critical stockout)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Clinical Justification</label>
            <textarea
              value={requestJustification}
              onChange={(e) => setRequestJustification(e.target.value)}
              placeholder="e.g. Higher monsoon fever surge, stock depleted faster than historical run-rate"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsSupplyRequestModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Raising Indent...' : 'Transmit to District Warehouse'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
