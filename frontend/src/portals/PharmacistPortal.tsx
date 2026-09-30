import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Pill, AlertTriangle, CheckCircle, Clock, 
  Send, Search, ShieldCheck, ChevronRight, 
  Package, Truck, BookOpen, AlertCircle, Plus,
  Layers, Check, Sparkles, Box, ShieldAlert,
  Calendar, Eye, ArrowRight, ClipboardCheck
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

export default function PharmacistPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'dispense' | 'alerts' | 'inventory' | 'transfers' | 'druginfo' => {
    if (path.includes('/alerts')) return 'alerts';
    if (path.includes('/inventory')) return 'inventory';
    if (path.includes('/transfers') || path.includes('/receipts')) return 'transfers';
    if (path.includes('/druginfo')) return 'druginfo';
    return 'dispense';
  };

  const [activeTab, setActiveTab] = useState<'dispense' | 'alerts' | 'inventory' | 'transfers' | 'druginfo'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'dispense' | 'alerts' | 'inventory' | 'transfers' | 'druginfo') => {
    setActiveTab(tab);
    if (tab === 'transfers') navigate('/pharmacy/receipts');
    else navigate(`/pharmacy/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const facilityId = user?.facility_id || '11111111-1111-1111-1111-111111111111';

  // Dispense Queue State
  const [dispenseQueue, setDispenseQueue] = useState<any[]>([]);
  const [selectedRx, setSelectedRx] = useState<any>(null);
  const [isDispenseModalOpen, setIsDispenseModalOpen] = useState(false);
  const [dispenseNotes, setDispenseNotes] = useState('');
  const [dispenseSuccess, setDispenseSuccess] = useState<any>(null);

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

  // Drug Info State
  const [selectedMedIdForInfo, setSelectedMedIdForInfo] = useState('');
  const [drugInfoResult, setDrugInfoResult] = useState<any>(null);
  const [isQueryingDrugInfo, setIsQueryingDrugInfo] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchPharmacistData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [queueRes, alertsRes, invRes, transRes] = await Promise.all([
        api.get<any[]>('/pharmacy/queue'),
        api.get<any[]>('/pharmacy/alerts'),
        api.get<any[]>('/pharmacy/inventory'),
        api.get<any[]>('/supply/transfers'),
      ]);

      if (queueRes.data) setDispenseQueue(queueRes.data);
      if (alertsRes.data) setStockAlerts(alertsRes.data);
      if (invRes.data) setInventoryItems(invRes.data);
      if (transRes.data) setTransfers(transRes.data);

      if (queueRes.error) {
        setError(queueRes.error.detail);
      }
    } catch {
      setError('Failed to fetch pharmacist dispensary records.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPharmacistData();
  }, []);

  const handleDispensePrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRx) return;

    setIsSubmitting(true);
    try {
      const res = await api.post(`/pharmacy/prescriptions/${selectedRx.id}/dispense`, {
        notes: dispenseNotes || 'Dispensed as per physician electronic prescription',
      });

      if (res.data) {
        setActionSuccess(`Prescription for ${selectedRx.patient_name || 'Patient'} verified and dispensed!`);
        setIsDispenseModalOpen(false);
        fetchPharmacistData();
      } else {
        alert(res.error?.detail || 'Failed to dispense prescription.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateSupplyRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMedForRequest) return;

    setIsSubmitting(true);
    try {
      const res = await api.post('/supply/requests', {
        medication_id: selectedMedForRequest.id,
        quantity_requested: Number(requestedQty),
        priority: requestPriority,
        notes: requestJustification || 'Facility buffer replenishment',
      });

      if (res.data) {
        setActionSuccess(`Replenishment indent for ${selectedMedForRequest.generic_name} transmitted to District Supply Officer.`);
        setIsSupplyRequestModalOpen(false);
        fetchPharmacistData();
      } else {
        alert(res.error?.detail || 'Failed to submit indent request.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReceiveTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransfer) return;

    setIsSubmitting(true);
    try {
      const res = await api.post(`/supply/transfers/${selectedTransfer.id}/receive`, {
        received_quantity: Number(receivedQty),
        damaged_quantity: Number(damagedQty),
        batch_number: receiptBatchNo || 'BAT-2026-INB',
        expiry_date: receiptExpiry || '2027-12-31',
        notes: discrepancyReason || 'Stock goods received note (GRN) verified',
      });

      if (res.data) {
        setActionSuccess('Stock Goods Receipt Note (GRN) recorded and stock balance credited.');
        setIsReceiveModalOpen(false);
        fetchPharmacistData();
      } else {
        alert(res.error?.detail || 'Failed to confirm receipt.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading dispensary queue and medicine stock..." />;
  }

  const criticalShortages = stockAlerts.filter((a) => a.severity === 'CRITICAL' || a.alert_type === 'STOCKOUT');
  const pendingTransfers = transfers.filter((t) => t.status === 'IN_TRANSIT' || t.status === 'APPROVED');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Dispensary Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Dispensary Services' },
          { label: 'Pharmacy Dispensary Desk' },
        ]}
        facilityContext="Thirukalukundram PHC • Chengalpattu"
        title="Dispensary &amp; Formulary Counter"
        description="Electronic prescription verification and dispensing, real-time buffer threshold tracking, batch expiry surveillance, and district supply indents."
        actions={
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              if (inventoryItems.length > 0) {
                setSelectedMedForRequest(inventoryItems[0]);
                setIsSupplyRequestModalOpen(true);
              }
            }}
            className="gap-1.5 shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Supply Indent</span>
          </Button>
        }
        metrics={[
          {
            label: 'Prescriptions in Queue',
            value: dispenseQueue.length,
            hint: 'Awaiting patient pickup',
            variant: dispenseQueue.length > 0 ? 'sky' : 'default',
            icon: <Pill className="w-4 h-4" />,
          },
          {
            label: 'Formulary Stock',
            value: `${inventoryItems.length} Drugs`,
            hint: 'Active batches',
            variant: 'default',
            icon: <Box className="w-4 h-4" />,
          },
          {
            label: 'Stock Alerts',
            value: stockAlerts.length,
            hint: `${criticalShortages.length} critical stockouts`,
            variant: criticalShortages.length > 0 ? 'destructive' : 'warning',
            icon: <AlertTriangle className="w-4 h-4" />,
          },
          {
            label: 'Inbound Receipts',
            value: pendingTransfers.length,
            hint: 'From District Medical Store',
            variant: pendingTransfers.length > 0 ? 'sky' : 'default',
            icon: <Truck className="w-4 h-4" />,
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
          { key: 'dispense', label: `Dispense Queue (${dispenseQueue.length})`, icon: <Pill className="w-4 h-4" /> },
          { key: 'alerts', label: `Stock Alerts (${stockAlerts.length})`, icon: <AlertTriangle className="w-4 h-4" /> },
          { key: 'inventory', label: `Medicine Stock (${inventoryItems.length})`, icon: <Box className="w-4 h-4" /> },
          { key: 'transfers', label: `Inbound GRN Receipts (${transfers.length})`, icon: <Truck className="w-4 h-4" /> },
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

      {/* TAB 1: DISPENSE QUEUE */}
      {activeTab === 'dispense' && (
        <Card>
          <CardHeader>
            <CardTitle>Prescriptions Waiting for Verification &amp; Dispensing</CardTitle>
            <CardDescription>
              Electronic doctor orders generated during OPD consultation. Verify medicines, instruct citizen, and confirm dispense.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={dispenseQueue}
              keyExtractor={(rx) => rx.id}
              searchFilter={(rx, q) =>
                (rx.patient_name || '').toLowerCase().includes(q) ||
                (rx.patient_identifier || '').toLowerCase().includes(q) ||
                (rx.doctor_name || '').toLowerCase().includes(q)
              }
              emptyTitle="No Prescriptions Waiting"
              emptyMessage="All outpatient doctor prescriptions have been dispensed."
              columns={[
                {
                  key: 'id',
                  header: 'Prescription Ref',
                  render: (rx) => <span className="font-mono text-xs text-slate-700 font-bold">Rx-{rx.id.slice(0, 8)}</span>,
                },
                {
                  key: 'patient',
                  header: 'Patient Details',
                  render: (rx) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{rx.patient_name || 'Citizen'}</span>
                      <span className="text-[11px] text-slate-500 font-mono">{rx.patient_identifier || 'DEMO-PAT-0001'}</span>
                    </div>
                  ),
                },
                {
                  key: 'doctor',
                  header: 'Prescribing Doctor',
                  render: (rx) => <span className="text-xs font-semibold text-slate-700">{rx.doctor_name || 'Dr. Ramesh'}</span>,
                },
                {
                  key: 'items',
                  header: 'Prescribed Items',
                  render: (rx) => (
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {rx.items?.map((it: any, idx: number) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-100 text-[11px] font-medium">
                          {it.medication_name} ({it.dosage})
                        </span>
                      )) || <span className="text-xs text-slate-400">Standard Pack</span>}
                    </div>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (rx) => <Badge status={rx.status || 'PENDING_DISPENSING'} size="sm" />,
                },
                {
                  key: 'action',
                  header: 'Action',
                  render: (rx) => (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedRx(rx);
                        setDispenseNotes('');
                        setIsDispenseModalOpen(true);
                      }}
                      className="h-7 text-xs px-2.5 gap-1 shadow-xs"
                    >
                      <ClipboardCheck className="w-3.5 h-3.5" />
                      <span>Verify &amp; Dispense</span>
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 2: STOCK ALERTS */}
      {activeTab === 'alerts' && (
        <Card>
          <CardHeader>
            <CardTitle>Dispensary Medicine Stockout &amp; Expiry Alerts</CardTitle>
            <CardDescription>
              Inventory items breached below minimum buffer threshold or expiring within 60 days.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={stockAlerts}
              keyExtractor={(a) => a.id || a.medication_id}
              emptyTitle="No Active Stock Alerts"
              emptyMessage="All formulary items are safely above buffer thresholds with no near-term expiries."
              columns={[
                {
                  key: 'med',
                  header: 'Medication',
                  render: (a) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{a.medication_name || a.generic_name}</span>
                      <span className="text-[11px] text-slate-400">{a.dosage_form || 'Tablets'}</span>
                    </div>
                  ),
                },
                {
                  key: 'alert_type',
                  header: 'Alert Type',
                  render: (a) => (
                    <span className="text-xs font-bold text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                      {a.alert_type || 'LOW_STOCK'}
                    </span>
                  ),
                },
                {
                  key: 'balance',
                  header: 'Current Stock',
                  render: (a) => <span className="font-mono text-xs font-bold text-slate-800">{a.current_stock ?? a.current_balance ?? 0} units</span>,
                },
                {
                  key: 'buffer',
                  header: 'Buffer Target',
                  render: (a) => <span className="font-mono text-xs text-slate-500">{a.buffer_target ?? a.reorder_level ?? 200} units</span>,
                },
                {
                  key: 'action',
                  header: 'Indent Requisition',
                  render: (a) => (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedMedForRequest({
                          id: a.medication_id || a.id,
                          generic_name: a.medication_name || a.generic_name,
                        });
                        setIsSupplyRequestModalOpen(true);
                      }}
                      className="h-7 text-xs px-2.5 text-sky-700"
                    >
                      Request Indent
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: INVENTORY ITEMS */}
      {activeTab === 'inventory' && (
        <Card>
          <CardHeader>
            <CardTitle>PHC Formulary Medicine Stock Ledger</CardTitle>
            <CardDescription>
              Complete dispensary stock balance, batch numbers, storage requirements, and expiry schedule.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={inventoryItems}
              keyExtractor={(m) => m.id}
              searchFilter={(m, q) =>
                (m.generic_name || '').toLowerCase().includes(q) ||
                (m.brand_name || '').toLowerCase().includes(q) ||
                (m.category || '').toLowerCase().includes(q)
              }
              emptyTitle="Formulary Empty"
              emptyMessage="No medicines registered in dispensary inventory."
              columns={[
                {
                  key: 'generic',
                  header: 'Generic Name',
                  render: (m) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{m.generic_name}</span>
                      <span className="text-[11px] text-slate-400">{m.brand_name || m.dosage_form}</span>
                    </div>
                  ),
                },
                { key: 'strength', header: 'Strength', render: (m) => <span className="font-mono text-xs">{m.strength}</span> },
                {
                  key: 'category',
                  header: 'Category',
                  render: (m) => <span className="text-xs text-slate-600">{m.category || 'Essential Drug'}</span>,
                },
                {
                  key: 'balance',
                  header: 'Stock Units',
                  render: (m) => {
                    const bal = m.current_balance ?? m.stock_quantity ?? 0;
                    const buf = m.reorder_level ?? 100;
                    return (
                      <span className={`font-mono text-xs font-bold ${bal <= buf ? 'text-red-600' : 'text-slate-800'}`}>
                        {bal} units
                      </span>
                    );
                  },
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (m) => {
                    const bal = m.current_balance ?? m.stock_quantity ?? 0;
                    const buf = m.reorder_level ?? 100;
                    return <Badge status={bal <= 0 ? 'STOCKOUT' : bal <= buf ? 'LOW_STOCK' : 'AVAILABLE'} size="sm" />;
                  },
                },
                {
                  key: 'action',
                  header: 'Indent',
                  render: (m) => (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedMedForRequest(m);
                        setIsSupplyRequestModalOpen(true);
                      }}
                      className="h-7 text-xs px-2"
                    >
                      Indent
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: INBOUND GOODS RECEIPTS (GRN) */}
      {activeTab === 'transfers' && (
        <Card>
          <CardHeader>
            <CardTitle>Inbound Shipments &amp; Goods Receipt Notes (GRN)</CardTitle>
            <CardDescription>
              Dispatches from District Medical Store or neighboring PHC inter-facility rebalancing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={transfers}
              keyExtractor={(t) => t.id}
              emptyTitle="No Inbound Shipments"
              emptyMessage="No stock dispatches currently en route to this facility."
              columns={[
                {
                  key: 'id',
                  header: 'Transfer Ref',
                  render: (t) => <span className="font-mono text-xs text-slate-700 font-bold">TRF-{t.id.slice(0, 8)}</span>,
                },
                {
                  key: 'med',
                  header: 'Medication',
                  render: (t) => <span className="font-bold text-slate-900">{t.medication_name || 'Essential Medicine'}</span>,
                },
                {
                  key: 'qty',
                  header: 'Quantity Sent',
                  render: (t) => <span className="font-mono text-xs font-bold text-slate-800">{t.quantity_sent || t.quantity || 500} units</span>,
                },
                {
                  key: 'origin',
                  header: 'Origin Facility',
                  render: (t) => <span className="text-xs text-slate-600">{t.origin_facility_name || 'District Central Medical Store'}</span>,
                },
                {
                  key: 'status',
                  header: 'Shipment Status',
                  render: (t) => <Badge status={t.status || 'IN_TRANSIT'} size="sm" />,
                },
                {
                  key: 'action',
                  header: 'Receive Stock',
                  render: (t) =>
                    t.status === 'IN_TRANSIT' || t.status === 'APPROVED' ? (
                      <Button
                        variant="emerald"
                        size="sm"
                        onClick={() => {
                          setSelectedTransfer(t);
                          setReceivedQty(t.quantity_sent || t.quantity || 500);
                          setDamagedQty(0);
                          setReceiptBatchNo('BAT-2026-INB');
                          setIsReceiveModalOpen(true);
                        }}
                        className="h-7 text-xs px-2.5 gap-1"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Log GRN</span>
                      </Button>
                    ) : (
                      <span className="text-xs text-slate-400">Completed</span>
                    ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Modal: Dispense Verification */}
      <Dialog open={isDispenseModalOpen} onOpenChange={setIsDispenseModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Verify &amp; Dispense Prescription</DialogTitle>
          <DialogDescription>
            Confirm physical medicine batches issued to {selectedRx?.patient_name || 'patient'}.
          </DialogDescription>
          <DialogClose onClose={() => setIsDispenseModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          {selectedRx && (
            <form onSubmit={handleDispensePrescription} className="space-y-4">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-xs">
                <div>Patient: <strong>{selectedRx.patient_name}</strong> (UHID: {selectedRx.patient_identifier})</div>
                <div>Doctor: <strong>{selectedRx.doctor_name || 'Medical Officer'}</strong></div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Prescribed Medicines</label>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {selectedRx.items?.map((it: any, idx: number) => (
                    <div key={idx} className="p-2 rounded-lg border border-slate-200 text-xs flex justify-between">
                      <span className="font-semibold text-slate-900">{it.medication_name} ({it.dosage})</span>
                      <span className="text-slate-500 font-mono">Qty: {it.quantity_prescribed || it.duration_days * 3}</span>
                    </div>
                  )) || <div className="text-xs text-slate-500">Standard pack verification.</div>}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Pharmacist Dispensing Remarks</label>
                <Input
                  type="text"
                  value={dispenseNotes}
                  onChange={(e) => setDispenseNotes(e.target.value)}
                  placeholder="Patient counselled in Tamil on dosage schedule"
                />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" size="sm" onClick={() => setIsDispenseModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                  {isSubmitting ? 'Confirming Dispense...' : 'Confirm & Mark Dispensed'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal: Create Supply Request Indent */}
      <Dialog open={isSupplyRequestModalOpen} onOpenChange={setIsSupplyRequestModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Create District Supply Requisition</DialogTitle>
          <DialogDescription>Submit medicine stock indent to District Medical Store.</DialogDescription>
          <DialogClose onClose={() => setIsSupplyRequestModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateSupplyRequest} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Medication Item</label>
              <select
                value={selectedMedForRequest?.id || ''}
                onChange={(e) => {
                  const found = inventoryItems.find((m) => m.id === e.target.value);
                  setSelectedMedForRequest(found);
                }}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
              >
                {inventoryItems.map((m) => (
                  <option key={m.id} value={m.id}>{m.generic_name} ({m.strength})</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Quantity (Units)</label>
                <Input
                  type="number"
                  value={requestedQty}
                  onChange={(e) => setRequestedQty(Number(e.target.value))}
                  min={10}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Indent Priority</label>
                <select
                  value={requestPriority}
                  onChange={(e) => setRequestPriority(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="ROUTINE">Routine Replenishment</option>
                  <option value="URGENT">Urgent (Buffer Breached)</option>
                  <option value="EMERGENCY">Emergency (Stockout Imminent)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Justification / Reason</label>
              <Input
                type="text"
                value={requestJustification}
                onChange={(e) => setRequestJustification(e.target.value)}
                placeholder="High OPD consumption due to seasonal viral fever surge"
                required
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsSupplyRequestModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Transmitting Indent...' : 'Transmit Requisition'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Receive Stock GRN */}
      <Dialog open={isReceiveModalOpen} onOpenChange={setIsReceiveModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Log Goods Receipt Note (GRN)</DialogTitle>
          <DialogDescription>Credit received physical shipment into facility inventory balance.</DialogDescription>
          <DialogClose onClose={() => setIsReceiveModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleReceiveTransfer} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Received Qty</label>
                <Input
                  type="number"
                  value={receivedQty}
                  onChange={(e) => setReceivedQty(Number(e.target.value))}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Damaged Qty</label>
                <Input
                  type="number"
                  value={damagedQty}
                  onChange={(e) => setDamagedQty(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Batch Number</label>
                <Input
                  type="text"
                  value={receiptBatchNo}
                  onChange={(e) => setReceiptBatchNo(e.target.value)}
                  placeholder="BAT-2026-X"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Expiry Date</label>
                <Input
                  type="date"
                  value={receiptExpiry}
                  onChange={(e) => setReceiptExpiry(e.target.value)}
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsReceiveModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="emerald" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Logging GRN...' : 'Commit & Credit Stock'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
