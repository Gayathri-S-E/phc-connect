import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Users, UserCheck, Stethoscope, AlertTriangle, 
  Clock, Plus, CheckCircle, FileText, Pill, 
  Send, ShieldAlert, Activity, ChevronRight, Check,
  Search, FlaskConical, Box, Filter, Eye, Trash2,
  Calendar, Building2, UserX, AlertOctagon, HeartPulse,
  LogOut, LogIn, ShieldCheck, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
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

export default function DoctorPortal() {
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  // Primary Data States
  const [queue, setQueue] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<any>(null);
  const [medications, setMedications] = useState<any[]>([]);
  const [allPatients, setAllPatients] = useState<any[]>([]);
  const [labOrdersList, setLabOrdersList] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sub-Navigation Route Syncing
  const getTabFromPath = (path: string): 'queue' | 'patients' | 'labs' | 'inventory' => {
    if (path.includes('/patients')) return 'patients';
    if (path.includes('/labs')) return 'labs';
    if (path.includes('/inventory') || path.includes('/pharmacy/inventory')) return 'inventory';
    return 'queue';
  };

  const [activeTab, setActiveTab] = useState<'queue' | 'patients' | 'labs' | 'inventory'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'queue' | 'patients' | 'labs' | 'inventory') => {
    setActiveTab(tab);
    switch (tab) {
      case 'queue': navigate('/clinical/queue'); break;
      case 'patients': navigate('/clinical/patients'); break;
      case 'labs': navigate('/clinical/labs'); break;
      case 'inventory': navigate('/clinical/inventory'); break;
    }
  };

  // Selected Consultation Workspace State
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [activeConsultation, setActiveConsultation] = useState<any>(null);
  const [chiefComplaints, setChiefComplaints] = useState('');
  const [examinationNotes, setExaminationNotes] = useState('');
  const [selectedDiagnosis, setSelectedDiagnosis] = useState('J18.9');

  // Patients Directory Search State
  const [patientSearchQuery, setPatientSearchQuery] = useState('');
  const [inspectedPatientHistory, setInspectedPatientHistory] = useState<any>(null);
  const [isPatientHistoryModalOpen, setIsPatientHistoryModalOpen] = useState(false);

  // Prescription items state
  const [prescriptionItems, setPrescriptionItems] = useState<Array<{
    medication_id: string;
    medication_name: string;
    dosage: string;
    frequency: string;
    duration_days: number;
    instructions: string;
  }>>([]);
  const [selectedMedId, setSelectedMedId] = useState('');
  const [itemDosage, setItemDosage] = useState('500mg');
  const [itemFrequency, setItemFrequency] = useState('TDS (3 times a day)');
  const [itemDuration, setItemDuration] = useState(5);
  const [itemInstructions, setItemInstructions] = useState('After meals');

  // Lab order state
  const [selectedLabTest, setSelectedLabTest] = useState('Complete Blood Count (CBC)');
  const [labPriority, setLabPriority] = useState<'ROUTINE' | 'URGENT'>('ROUTINE');
  const [orderedLabs, setOrderedLabs] = useState<string[]>([]);

  // Referral state
  const [referralFacility, setReferralFacility] = useState('District Hospital Chengalpattu');
  const [referralSpecialty, setReferralSpecialty] = useState('Pulmonology');
  const [referralReason, setReferralReason] = useState('');

  // Emergency incident modal state
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  const [emergencyTitle, setEmergencyTitle] = useState('');
  const [emergencyCategory, setEmergencyCategory] = useState('DISEASE_CLUSTER');
  const [emergencyDescription, setEmergencyDescription] = useState('');
  const [emergencySuccess, setEmergencySuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [finalizeNotification, setFinalizeNotification] = useState<string | null>(null);

  const fetchDoctorData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [queueRes, attendRes, medsRes, patsRes, labsRes] = await Promise.all([
        api.get<any[]>('/doctor/queue'),
        api.get<any>('/doctor/attendance/today'),
        api.get<any[]>('/pharmacy/inventory'),
        api.get<any[]>('/patients'),
        api.get<any[]>('/doctor/labs'),
      ]);

      if (queueRes.data) setQueue(queueRes.data);
      if (attendRes.data) setAttendance(attendRes.data);
      if (medsRes.data) setMedications(medsRes.data);
      if (patsRes.data) setAllPatients(patsRes.data);
      if (labsRes.data) setLabOrdersList(labsRes.data);

      if (queueRes.error) {
        setError(queueRes.error.detail);
      }
    } catch {
      setError('Failed to fetch doctor portal data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctorData();
  }, []);

  const handleCheckIn = async () => {
    const res = await api.post('/doctor/attendance/check-in', { shift: 'GENERAL' });
    if (res.data) {
      fetchDoctorData();
    } else {
      alert(res.error?.detail || 'Failed to record check-in.');
    }
  };

  const handleCheckOut = async () => {
    const res = await api.post('/doctor/attendance/check-out', { notes: 'Shift completed' });
    if (res.data) {
      fetchDoctorData();
    } else {
      alert(res.error?.detail || 'Failed to record check-out.');
    }
  };

  const handleSelectPatient = async (patientItem: any) => {
    setSelectedPatient(patientItem);
    const symptoms = patientItem.reason || patientItem.reason_for_visit || 'Fever, Cough';
    setChiefComplaints(symptoms);
    setExaminationNotes('');
    setPrescriptionItems([]);
    setOrderedLabs([]);
    setFinalizeNotification(null);

    try {
      const res = await api.post<any>('/doctor/consultations', {
        patient_id: patientItem.patient_id,
        appointment_id: patientItem.appointment_id,
        chief_complaint: symptoms,
      });
      if (res.data) {
        setActiveConsultation(res.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddPrescriptionItem = () => {
    if (!selectedMedId) return;
    const med = medications.find((m) => m.id === selectedMedId);
    setPrescriptionItems([
      ...prescriptionItems,
      {
        medication_id: selectedMedId,
        medication_name: med ? `${med.generic_name} (${med.strength})` : 'Medicine',
        dosage: itemDosage,
        frequency: itemFrequency,
        duration_days: Number(itemDuration),
        instructions: itemInstructions,
      },
    ]);
  };

  const handleRemovePrescriptionItem = (idx: number) => {
    setPrescriptionItems(prescriptionItems.filter((_, i) => i !== idx));
  };

  const handleAddLabOrder = () => {
    if (!orderedLabs.includes(selectedLabTest)) {
      setOrderedLabs([...orderedLabs, selectedLabTest]);
    }
  };

  const DIAGNOSIS_NAMES: Record<string, string> = {
    'J18.9': 'Pneumonia, unspecified organism',
    'J00': 'Acute nasopharyngitis (Common Cold)',
    'A09': 'Infectious gastroenteritis and colitis',
    'I10': 'Essential (primary) hypertension',
    'E11': 'Type 2 diabetes mellitus',
    'A90': 'Dengue fever',
    'B34.9': 'Viral infection, unspecified',
    'R50.9': 'Fever, unspecified',
  };

  const handleFinalizeConsultation = async () => {
    if (!activeConsultation?.id) return;
    setIsSubmitting(true);

    try {
      const conditionName = DIAGNOSIS_NAMES[selectedDiagnosis] || 'Primary condition';
      const finalizeRes = await api.post(`/doctor/consultations/${activeConsultation.id}/finalize`, {
        clinical_notes: chiefComplaints || 'General consultation encounter',
        examination_findings: examinationNotes || 'Patient examined. Symptoms recorded.',
        diagnoses: [
          {
            icd10_code: selectedDiagnosis,
            condition_name: conditionName,
            diagnosis_type: 'PRIMARY',
            notes: examinationNotes || undefined,
          },
        ],
      });

      if (finalizeRes.error) {
        alert(finalizeRes.error.detail || 'Failed to finalize consultation encounter.');
        return;
      }

      if (prescriptionItems.length > 0) {
        await api.post('/doctor/prescriptions', {
          consultation_id: activeConsultation.id,
          notes: 'Standard PHC outpatient electronic prescription',
          items: prescriptionItems.map((item) => ({
            medication_id: item.medication_id,
            medication_name: item.medication_name || 'Prescribed Medicine',
            dosage: item.dosage,
            frequency: item.frequency,
            duration_days: item.duration_days,
            instructions: item.instructions,
            quantity_prescribed: item.duration_days * 3,
          })),
        });
      }

      if (orderedLabs.length > 0) {
        for (const testName of orderedLabs) {
          await api.post('/doctor/labs', {
            consultation_id: activeConsultation.id,
            test_category: testName,
            clinical_notes: chiefComplaints || 'Routine diagnostic evaluation',
          });
        }
      }

      if (referralReason.trim()) {
        await api.post('/doctor/referrals', {
          consultation_id: activeConsultation.id,
          to_facility_name: referralFacility,
          referral_reason: referralReason,
          urgency: 'ROUTINE',
          clinical_summary: `Referred for ${referralSpecialty}. Chief complaint: ${chiefComplaints}`,
        });
      }

      setFinalizeNotification('Consultation finalized successfully! Prescriptions and lab orders routed to dispensary and laboratory.');
      setSelectedPatient(null);
      setActiveConsultation(null);
      fetchDoctorData();
    } catch (e: any) {
      alert(e.message || 'Error finalizing encounter.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReportEmergency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emergencyTitle.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await api.post('/emergencies', {
        emergency_type: emergencyCategory || 'DISEASE_CLUSTER',
        title: emergencyTitle,
        description: emergencyDescription || emergencyTitle,
        affected_area: 'Facility Primary Catchment Area',
        source: 'Doctor Clinical OPD Encounter',
        affected_facility_ids: [],
      });

      if (res.data) {
        setEmergencySuccess(true);
      } else {
        alert(res.error?.detail || 'Failed to submit emergency report.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInspectHistory = async (patientId: string) => {
    try {
      const res = await api.get<any>(`/patients/${patientId}/history`);
      if (res.data) {
        setInspectedPatientHistory(res.data);
        setIsPatientHistoryModalOpen(true);
      }
    } catch (e) {
      alert('Failed to retrieve patient medical history.');
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading Medical Officer clinical queue and records..." />;
  }

  if (error && queue.length === 0) {
    return <StateView state="error" message={error} onRetry={fetchDoctorData} />;
  }

  const urgentPatients = queue.filter(
    (p) => p.triage_category === 'IMMEDIATE' || p.triage_category === 'EMERGENCY' || p.priority === 'EMERGENCY' || p.triage_category === 'URGENT'
  );

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Clinical Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Clinical Services' },
          { label: 'Outpatient Department (OPD)' },
        ]}
        facilityContext="Thirukalukundram PHC • Chengalpattu"
        title="Physician OPD Consultation Desk"
        description="Active patient queue triage, electronic clinical consultation notes, ICD-10 diagnostic coding, and digital dispensary prescription routing."
        actions={
          <div className="flex items-center gap-2">
            {attendance?.status === 'CHECKED_IN' ? (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCheckOut}
                className="gap-1.5 text-slate-700 hover:text-red-700"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Duty Check-Out</span>
              </Button>
            ) : (
              <Button
                variant="emerald"
                size="sm"
                onClick={handleCheckIn}
                className="gap-1.5 shadow-xs"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Record Duty Check-In</span>
              </Button>
            )}

            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                setEmergencySuccess(false);
                setIsEmergencyModalOpen(true);
              }}
              className="gap-1.5 shadow-xs"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Flag Outbreak Alert</span>
            </Button>
          </div>
        }
        metrics={[
          {
            label: 'Waiting in OPD',
            value: queue.length,
            hint: `${urgentPatients.length} triage priority flagged`,
            variant: urgentPatients.length > 0 ? 'warning' : 'sky',
            icon: <Users className="w-4 h-4" />,
          },
          {
            label: 'Shift Status',
            value: attendance?.status === 'CHECKED_IN' ? 'On Duty' : 'Off Duty',
            hint: attendance?.check_in_time ? `Since ${attendance.check_in_time.slice(0, 5)}` : 'Shift ready',
            variant: attendance?.status === 'CHECKED_IN' ? 'success' : 'default',
            icon: <Stethoscope className="w-4 h-4" />,
          },
          {
            label: 'Lab Orders Active',
            value: labOrdersList.length,
            hint: 'Processing in PHC lab',
            variant: 'default',
            icon: <FlaskConical className="w-4 h-4" />,
          },
          {
            label: 'Formulary Stock',
            value: `${medications.length} Meds`,
            hint: 'Dispensary linked',
            variant: 'default',
            icon: <Pill className="w-4 h-4" />,
          },
        ]}
      />

      {finalizeNotification && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 animate-fade-in shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{finalizeNotification}</span>
          </div>
          <button
            onClick={() => setFinalizeNotification(null)}
            className="text-emerald-700 hover:text-emerald-950 underline text-xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200/80 rounded-xl overflow-x-auto no-scrollbar max-w-full">
        {[
          { key: 'queue', label: `OPD Queue (${queue.length})`, icon: <Users className="w-4 h-4" /> },
          { key: 'patients', label: `Patient Directory (${allPatients.length})`, icon: <Search className="w-4 h-4" /> },
          { key: 'labs', label: `Diagnostic Orders (${labOrdersList.length})`, icon: <FlaskConical className="w-4 h-4" /> },
          { key: 'inventory', label: `Dispensary Stock (${medications.length})`, icon: <Box className="w-4 h-4" /> },
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

      {/* TAB 1: CONSULTATION WORKSPACE OR OPD QUEUE */}
      {activeTab === 'queue' && (
        <div className="space-y-6">
          {/* Active Consultation Workspace */}
          {selectedPatient ? (
            <Card className="border-sky-300 shadow-md">
              <CardHeader className="bg-sky-50/70 border-b border-sky-100 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-600 text-white font-bold flex items-center justify-center shadow-xs">
                      #{selectedPatient.token_number || '1'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base">
                          {selectedPatient.patient_name || 'Patient'}
                        </CardTitle>
                        <Badge status={selectedPatient.triage_category || selectedPatient.priority || 'ROUTINE'} size="sm" />
                      </div>
                      <span className="text-xs text-slate-500 font-mono">
                        UHID: {selectedPatient.patient_identifier || 'DEMO-PAT-0001'} • Age: {selectedPatient.age || 38} Y / {selectedPatient.gender || 'M'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleInspectHistory(selectedPatient.patient_id)}
                      className="text-sky-700 hover:bg-sky-100/70"
                    >
                      <Eye className="w-3.5 h-3.5 mr-1.5" />
                      View Past History
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedPatient(null)}
                    >
                      Close Desk
                    </Button>
                  </div>
                </div>

                {/* Triage Vitals Banner */}
                {selectedPatient.vitals && (
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 mt-3 pt-3 border-t border-sky-100">
                    <div className="bg-white p-2 rounded-lg border border-sky-200/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">BP</span>
                      <div className="text-xs font-black text-slate-800">
                        {selectedPatient.vitals.systolic_bp}/{selectedPatient.vitals.diastolic_bp} mmHg
                      </div>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-sky-200/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">SpO2</span>
                      <div className={`text-xs font-black ${selectedPatient.vitals.spo2 < 95 ? 'text-red-600' : 'text-slate-800'}`}>
                        {selectedPatient.vitals.spo2}%
                      </div>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-sky-200/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Heart Rate</span>
                      <div className="text-xs font-black text-slate-800">
                        {selectedPatient.vitals.heart_rate} bpm
                      </div>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-sky-200/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Temp</span>
                      <div className="text-xs font-black text-slate-800">
                        {selectedPatient.vitals.temperature}°F
                      </div>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-sky-200/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Resp Rate</span>
                      <div className="text-xs font-black text-slate-800">
                        {selectedPatient.vitals.respiratory_rate || 18} /min
                      </div>
                    </div>
                  </div>
                )}
              </CardHeader>

              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column: Clinical Notes & Diagnosis */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Chief Complaints &amp; Symptom History
                      </label>
                      <Textarea
                        value={chiefComplaints}
                        onChange={(e) => setChiefComplaints(e.target.value)}
                        placeholder="Patient symptoms, onset, duration..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Physical Examination &amp; Systemic Findings
                      </label>
                      <Textarea
                        value={examinationNotes}
                        onChange={(e) => setExaminationNotes(e.target.value)}
                        placeholder="Chest auscultation, abdominal tenderness, throat exam..."
                        rows={3}
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        ICD-10 Primary Clinical Diagnosis
                      </label>
                      <select
                        value={selectedDiagnosis}
                        onChange={(e) => setSelectedDiagnosis(e.target.value)}
                        className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500 font-semibold"
                      >
                        {Object.entries(DIAGNOSIS_NAMES).map(([code, name]) => (
                          <option key={code} value={code}>
                            {code} — {name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Referral Section */}
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5">
                      <span className="text-xs font-bold text-slate-700 uppercase flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-sky-600" />
                        Optional Inter-Facility Referral
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <Input
                          type="text"
                          value={referralFacility}
                          onChange={(e) => setReferralFacility(e.target.value)}
                          placeholder="Referral Facility"
                          className="h-8 text-xs"
                        />
                        <Input
                          type="text"
                          value={referralSpecialty}
                          onChange={(e) => setReferralSpecialty(e.target.value)}
                          placeholder="Specialty (e.g. Pulmonology)"
                          className="h-8 text-xs"
                        />
                      </div>
                      <Input
                        type="text"
                        value={referralReason}
                        onChange={(e) => setReferralReason(e.target.value)}
                        placeholder="Clinical rationale for specialist referral..."
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>

                  {/* Right Column: Rx Builder & Lab Orders */}
                  <div className="space-y-4">
                    {/* Electronic Rx Builder */}
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800 uppercase flex items-center gap-1.5">
                          <Pill className="w-3.5 h-3.5 text-sky-600" />
                          Electronic Prescription (Rx) Builder
                        </span>
                        <span className="text-[11px] text-slate-500 font-medium">
                          {medications.length} facility medicines available
                        </span>
                      </div>

                      <div className="space-y-2">
                        <select
                          value={selectedMedId}
                          onChange={(e) => setSelectedMedId(e.target.value)}
                          className="w-full h-8 px-2.5 text-xs bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                        >
                          <option value="">Select Formulary Drug...</option>
                          {medications.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.generic_name} ({m.strength}) • Stock: {m.current_balance ?? m.stock_quantity ?? 50}
                            </option>
                          ))}
                        </select>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          <Input
                            type="text"
                            value={itemDosage}
                            onChange={(e) => setItemDosage(e.target.value)}
                            placeholder="Dosage (500mg)"
                            className="h-8 text-xs"
                          />
                          <Input
                            type="text"
                            value={itemFrequency}
                            onChange={(e) => setItemFrequency(e.target.value)}
                            placeholder="Frequency (TDS)"
                            className="h-8 text-xs"
                          />
                          <Input
                            type="number"
                            value={itemDuration}
                            onChange={(e) => setItemDuration(Number(e.target.value))}
                            placeholder="Days"
                            className="h-8 text-xs"
                          />
                        </div>

                        <div className="flex gap-2">
                          <Input
                            type="text"
                            value={itemInstructions}
                            onChange={(e) => setItemInstructions(e.target.value)}
                            placeholder="Diet instructions (e.g. After meals)"
                            className="h-8 text-xs flex-1"
                          />
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            onClick={handleAddPrescriptionItem}
                            disabled={!selectedMedId}
                            className="h-8 px-3 text-xs"
                          >
                            <Plus className="w-3.5 h-3.5 mr-1" />
                            Add Rx
                          </Button>
                        </div>
                      </div>

                      {/* Prescribed Items Table */}
                      <div className="space-y-1.5 pt-2">
                        {prescriptionItems.length === 0 ? (
                          <div className="text-[11px] text-slate-400 text-center py-2 bg-white rounded-lg border border-dashed border-slate-200">
                            No drugs added to this prescription yet.
                          </div>
                        ) : (
                          prescriptionItems.map((item, idx) => (
                            <div
                              key={idx}
                              className="p-2 bg-white rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                            >
                              <div>
                                <span className="font-bold text-slate-900">{item.medication_name}</span>
                                <span className="text-slate-500 text-[11px] block">
                                  {item.dosage} • {item.frequency} • {item.duration_days} days • {item.instructions}
                                </span>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleRemovePrescriptionItem(idx)}
                                className="text-slate-400 hover:text-red-600"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Diagnostic Lab Orders */}
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                      <span className="text-xs font-bold text-slate-800 uppercase flex items-center gap-1.5">
                        <FlaskConical className="w-3.5 h-3.5 text-sky-600" />
                        Diagnostic Laboratory Requisitions
                      </span>

                      <div className="flex gap-2">
                        <select
                          value={selectedLabTest}
                          onChange={(e) => setSelectedLabTest(e.target.value)}
                          className="flex-1 h-8 px-2.5 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                        >
                          <option value="Complete Blood Count (CBC)">Complete Blood Count (CBC)</option>
                          <option value="Fasting Blood Sugar (FBS)">Fasting Blood Sugar (FBS)</option>
                          <option value="Dengue NS1 Antigen Rapid">Dengue NS1 Antigen Rapid</option>
                          <option value="Urine Routine & Microscopic">Urine Routine &amp; Microscopic</option>
                          <option value="Serum Creatinine & Urea">Serum Creatinine &amp; Urea</option>
                          <option value="Malaria Rapid Diagnostic Test">Malaria Rapid Diagnostic Test</option>
                          <option value="Widal Slide Agglutination">Widal Slide Agglutination</option>
                        </select>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={handleAddLabOrder}
                          className="h-8 px-3 text-xs"
                        >
                          <Plus className="w-3.5 h-3.5 mr-1" />
                          Order Test
                        </Button>
                      </div>

                      <div className="flex flex-wrap gap-1.5">
                        {orderedLabs.map((test, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 text-xs font-medium text-slate-700 shadow-2xs"
                          >
                            <FlaskConical className="w-3 h-3 text-sky-600" />
                            {test}
                            <button
                              type="button"
                              onClick={() => setOrderedLabs(orderedLabs.filter((t) => t !== test))}
                              className="text-slate-400 hover:text-red-600 ml-1"
                            >
                              ✕
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Finalize Action Bar */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <span className="text-xs text-slate-500">
                    Signing will lock encounter notes and route digital orders to PHC Pharmacy &amp; Lab.
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedPatient(null)}
                    >
                      Suspend Encounter
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={isSubmitting}
                      onClick={handleFinalizeConsultation}
                      className="gap-2 shadow-xs"
                    >
                      <Check className="w-4 h-4" />
                      <span>{isSubmitting ? 'Signing Encounter...' : 'Finalize & Sign Electronic Rx'}</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : null}

          {/* OPD Queue Table */}
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <CardTitle>Active OPD Consultation Queue</CardTitle>
                  <CardDescription>
                    Live patient tokens registered by triage nurse. Priority cases require immediate examination.
                  </CardDescription>
                </div>
                <span className="text-xs text-slate-500 font-medium">
                  {queue.length} patients in queue
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <DataTable
                data={queue}
                keyExtractor={(p) => p.id || p.appointment_id || String(p.token_number)}
                searchFilter={(p, q) =>
                  (p.patient_name || '').toLowerCase().includes(q) ||
                  (p.patient_identifier || '').toLowerCase().includes(q) ||
                  (p.triage_category || '').toLowerCase().includes(q) ||
                  (p.reason || '').toLowerCase().includes(q)
                }
                emptyTitle="OPD Queue Empty"
                emptyMessage="All registered patients have been examined or no patients are currently waiting."
                columns={[
                  {
                    key: 'token',
                    header: 'Token #',
                    render: (p) => (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-sky-50 text-sky-800 font-mono font-bold text-xs border border-sky-200/80">
                        #{p.token_number || '1'}
                      </span>
                    ),
                  },
                  {
                    key: 'patient',
                    header: 'Patient Details',
                    render: (p) => (
                      <div>
                        <span className="font-bold text-slate-900 block text-xs sm:text-sm">
                          {p.patient_name || 'Citizen'}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          {p.patient_identifier || 'DEMO-PAT-0001'} • {p.age || 38} Y / {p.gender || 'M'}
                        </span>
                      </div>
                    ),
                  },
                  {
                    key: 'triage',
                    header: 'Triage Priority',
                    render: (p) => <Badge status={p.triage_category || p.priority || 'ROUTINE'} size="sm" />,
                  },
                  {
                    key: 'complaint',
                    header: 'Chief Complaint',
                    render: (p) => (
                      <span className="text-xs text-slate-700 font-medium">
                        {p.reason || p.reason_for_visit || 'General Consultation'}
                      </span>
                    ),
                  },
                  {
                    key: 'wait',
                    header: 'Wait Time',
                    render: (p) => (
                      <span className="text-xs text-slate-500 font-mono">
                        {p.wait_time_minutes ? `${p.wait_time_minutes} mins` : '10 mins'}
                      </span>
                    ),
                  },
                  {
                    key: 'action',
                    header: 'Consultation Desk',
                    render: (p) => (
                      <Button
                        variant={p.triage_category === 'IMMEDIATE' || p.triage_category === 'EMERGENCY' ? 'destructive' : 'primary'}
                        size="sm"
                        onClick={() => handleSelectPatient(p)}
                        className="h-7 text-xs px-2.5 gap-1.5"
                      >
                        <Stethoscope className="w-3.5 h-3.5" />
                        <span>Call Patient</span>
                      </Button>
                    ),
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: PATIENT DIRECTORY */}
      {activeTab === 'patients' && (
        <Card>
          <CardHeader>
            <CardTitle>Facility Patient Master Directory</CardTitle>
            <CardDescription>
              Search longitudinal clinical records, previous diagnoses, and digital prescriptions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={allPatients}
              keyExtractor={(p) => p.id}
              searchFilter={(p, q) =>
                (p.first_name || '').toLowerCase().includes(q) ||
                (p.last_name || '').toLowerCase().includes(q) ||
                (p.patient_identifier || '').toLowerCase().includes(q) ||
                (p.phone || '').toLowerCase().includes(q)
              }
              emptyTitle="No Patients Found"
              emptyMessage="No patient records match the directory query."
              columns={[
                {
                  key: 'uhid',
                  header: 'UHID / ID',
                  render: (p) => <span className="font-mono text-xs text-slate-600 font-semibold">{p.patient_identifier}</span>,
                },
                {
                  key: 'name',
                  header: 'Full Name',
                  render: (p) => <span className="font-bold text-slate-900">{p.first_name} {p.last_name || ''}</span>,
                },
                {
                  key: 'demographics',
                  header: 'Age / Gender',
                  render: (p) => <span className="text-xs text-slate-600">{p.age || '—'} Y • {p.gender || '—'}</span>,
                },
                {
                  key: 'contact',
                  header: 'Phone / Contact',
                  render: (p) => <span className="text-xs font-mono text-slate-600">{p.phone || '+91 98401 23456'}</span>,
                },
                {
                  key: 'actions',
                  header: 'History',
                  render: (p) => (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleInspectHistory(p.id)}
                      className="h-7 text-xs px-2.5 gap-1 text-sky-700"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View History</span>
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: DIAGNOSTIC LAB ORDERS */}
      {activeTab === 'labs' && (
        <Card>
          <CardHeader>
            <CardTitle>Laboratory Orders &amp; Results</CardTitle>
            <CardDescription>
              Clinical diagnostic investigations ordered from doctor consultation desk.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={labOrdersList}
              keyExtractor={(l) => l.id}
              emptyTitle="No Lab Orders"
              emptyMessage="No active laboratory investigations ordered."
              columns={[
                {
                  key: 'order_id',
                  header: 'Order Ref',
                  render: (l) => <span className="font-mono text-xs text-slate-600">LAB-{l.id.slice(0, 8)}</span>,
                },
                {
                  key: 'patient',
                  header: 'Patient Name',
                  render: (l) => <span className="font-bold text-slate-900">{l.patient_name || 'Citizen'}</span>,
                },
                {
                  key: 'test',
                  header: 'Test Investigation',
                  render: (l) => <span className="font-semibold text-slate-800">{l.test_category || l.test_name}</span>,
                },
                {
                  key: 'date',
                  header: 'Ordered Date',
                  render: (l) => (l.created_at ? new Date(l.created_at).toLocaleDateString() : 'Today'),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (l) => <Badge status={l.status} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: DISPENSARY INVENTORY STOCK */}
      {activeTab === 'inventory' && (
        <Card>
          <CardHeader>
            <CardTitle>Facility Dispensary Medicine Stock Balance</CardTitle>
            <CardDescription>
              Real-time stock balance in PHC pharmacy. Items below buffer trigger district replenishment.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={medications}
              keyExtractor={(m) => m.id}
              searchFilter={(m, q) =>
                (m.generic_name || '').toLowerCase().includes(q) ||
                (m.brand_name || '').toLowerCase().includes(q) ||
                (m.category || '').toLowerCase().includes(q)
              }
              emptyTitle="Formulary Stock Empty"
              emptyMessage="No medication items available in the dispensary stock register."
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
                { key: 'strength', header: 'Strength', render: (m) => <span className="text-xs font-mono">{m.strength}</span> },
                {
                  key: 'category',
                  header: 'Therapeutic Category',
                  render: (m) => <span className="text-xs text-slate-600">{m.category || 'Essential Medicine'}</span>,
                },
                {
                  key: 'balance',
                  header: 'Stock Balance',
                  render: (m) => {
                    const bal = m.current_balance ?? m.stock_quantity ?? 0;
                    const buf = m.reorder_level ?? m.minimum_buffer ?? 100;
                    const isLow = bal <= buf;
                    return (
                      <span className={`font-mono font-bold text-xs ${isLow ? 'text-red-600' : 'text-slate-800'}`}>
                        {bal} units {isLow && '⚠️ Low'}
                      </span>
                    );
                  },
                },
                {
                  key: 'status',
                  header: 'Stock Status',
                  render: (m) => {
                    const bal = m.current_balance ?? m.stock_quantity ?? 0;
                    const buf = m.reorder_level ?? m.minimum_buffer ?? 100;
                    return <Badge status={bal <= 0 ? 'STOCKOUT' : bal <= buf ? 'LOW_STOCK' : 'AVAILABLE'} size="sm" />;
                  },
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Patient History Modal */}
      <Dialog
        open={isPatientHistoryModalOpen}
        onOpenChange={setIsPatientHistoryModalOpen}
        maxWidth="max-w-2xl"
      >
        <DialogHeader>
          <DialogTitle>Longitudinal Patient Health History</DialogTitle>
          <DialogDescription>
            Historical consultations, past prescriptions, and lab records on file.
          </DialogDescription>
          <DialogClose onClose={() => setIsPatientHistoryModalOpen(false)} />
        </DialogHeader>
        <DialogContent className="max-h-[70vh] overflow-y-auto space-y-4">
          {inspectedPatientHistory ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-slate-900 block">{inspectedPatientHistory.patient?.first_name} {inspectedPatientHistory.patient?.last_name}</span>
                  <span className="text-slate-500 font-mono">UHID: {inspectedPatientHistory.patient?.patient_identifier}</span>
                </div>
                <Badge status="VERIFIED" size="sm" />
              </div>

              <div>
                <h5 className="text-xs font-bold text-slate-800 uppercase mb-2">Previous Encounters</h5>
                <div className="space-y-2">
                  {inspectedPatientHistory.consultations?.map((c: any) => (
                    <div key={c.id} className="p-3 border border-slate-200 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between font-bold text-slate-900">
                        <span>{c.chief_complaints}</span>
                        <span className="text-slate-400 font-normal">{new Date(c.created_at).toLocaleDateString()}</span>
                      </div>
                      {c.examination_notes && <p className="text-slate-600">{c.examination_notes}</p>}
                    </div>
                  )) || <div className="text-xs text-slate-400">No past clinical visits recorded.</div>}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 text-center py-6">No historical records available.</div>
          )}
        </DialogContent>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => setIsPatientHistoryModalOpen(false)}>
            Close History
          </Button>
        </DialogFooter>
      </Dialog>

      {/* Outbreak / Emergency Modal */}
      <Dialog
        open={isEmergencyModalOpen}
        onOpenChange={setIsEmergencyModalOpen}
        maxWidth="max-w-md"
      >
        <DialogHeader>
          <DialogTitle>Report Public Health Crisis / Outbreak</DialogTitle>
          <DialogDescription>
            Flagging will trigger an urgent notification to the District Health Officer and Emergency Coordinator.
          </DialogDescription>
          <DialogClose onClose={() => setIsEmergencyModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          {emergencySuccess ? (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
              <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto" />
              <h4 className="text-base font-bold text-emerald-950">Emergency Incident Broadcasted</h4>
              <p className="text-xs text-emerald-800">
                District Disaster Management and State Epidemic Cell alerted.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsEmergencyModalOpen(false)}
                className="mt-3 w-full"
              >
                Close
              </Button>
            </div>
          ) : (
            <form onSubmit={handleReportEmergency} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Incident Category
                </label>
                <select
                  value={emergencyCategory}
                  onChange={(e) => setEmergencyCategory(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                >
                  <option value="DISEASE_CLUSTER">Disease Cluster / Epidemic Spike (Dengue, Cholera, etc.)</option>
                  <option value="MASS_CASUALTY">Mass Casualty / Industrial Accident</option>
                  <option value="FACILITY_DISRUPTION">Critical PHC Infrastructure Failure (Power/Oxygen)</option>
                  <option value="CRITICAL_STOCKOUT">Critical Life-Saving Drug Stockout</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Incident Title
                </label>
                <Input
                  type="text"
                  value={emergencyTitle}
                  onChange={(e) => setEmergencyTitle(e.target.value)}
                  placeholder="e.g. Cluster of 12 Acute Diarrheal cases in Kovalam village"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Clinical Summary &amp; Urgent Requirements
                </label>
                <Textarea
                  value={emergencyDescription}
                  onChange={(e) => setEmergencyDescription(e.target.value)}
                  placeholder="Describe patient count, clinical severity, urgent medicine or ambulance needs..."
                  rows={3}
                  required
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEmergencyModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="destructive"
                  size="sm"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Transmitting Alert...' : 'Broadcast Urgent Alert'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
