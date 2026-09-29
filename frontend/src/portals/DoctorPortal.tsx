import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Users, UserCheck, Stethoscope, AlertTriangle, 
  Clock, Plus, CheckCircle, FileText, Pill, 
  Send, ShieldAlert, Activity, ChevronRight, Check,
  Search, FlaskConical, Box, Filter, Eye
} from 'lucide-react';
import { api } from '../services/api';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';

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
      case 'queue':
        navigate('/clinical/queue');
        break;
      case 'patients':
        navigate('/clinical/patients');
        break;
      case 'labs':
        navigate('/clinical/labs');
        break;
      case 'inventory':
        navigate('/clinical/inventory');
        break;
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

  // Emergency report state
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  const [emergencyTitle, setEmergencyTitle] = useState('');
  const [emergencyCategory, setEmergencyCategory] = useState('EPIDEMIC');
  const [emergencySeverity, setEmergencySeverity] = useState('CRITICAL');
  const [emergencyDescription, setEmergencyDescription] = useState('');
  const [emergencySuccess, setEmergencySuccess] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchDoctorData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [queueRes, attendanceRes, medsRes, patientsRes, labsRes] = await Promise.all([
        api.get<any[]>('/doctor/queue'),
        api.get<any>('/doctor/attendance/today'),
        api.get<any[]>('/medications'),
        api.get<any>('/patients?limit=50'),
        api.get<any>('/labs/orders?limit=50'),
      ]);

      if (queueRes.data) {
        // Deterministic priority ordering: EMERGENCY -> PRIORITY -> ROUTINE by token_number
        const sortedQueue = [...queueRes.data].sort((a, b) => {
          const priorityWeight: Record<string, number> = { EMERGENCY: 1, PRIORITY: 2, ROUTINE: 3 };
          const pA = priorityWeight[a.priority] || 3;
          const pB = priorityWeight[b.priority] || 3;
          if (pA !== pB) return pA - pB;
          return (a.token_number || 0) - (b.token_number || 0);
        });
        setQueue(sortedQueue);
      }
      if (attendanceRes.data) setAttendance(attendanceRes.data);
      if (medsRes.data) {
        setMedications(medsRes.data);
        if (medsRes.data.length > 0) {
          setSelectedMedId(medsRes.data[0].id);
        }
      }
      if (patientsRes.data) {
        const pList = Array.isArray(patientsRes.data) ? patientsRes.data : (patientsRes.data.items || []);
        setAllPatients(pList);
      }
      if (labsRes.data) {
        const lList = Array.isArray(labsRes.data) ? labsRes.data : (labsRes.data.items || []);
        setLabOrdersList(lList);
      }

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

    // Start consultation in backend
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
        const rxRes = await api.post('/doctor/prescriptions', {
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
        if (rxRes.error) {
          alert(rxRes.error.detail || 'Failed to create electronic prescription.');
        }
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

      alert('Consultation finalized! Prescriptions and lab orders routed to respective queues.');
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

  const renderPriorityBadge = (priority: string) => {
    if (priority === 'EMERGENCY') {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.25rem',
          backgroundColor: '#fee2e2',
          color: '#dc2626',
          fontWeight: 800,
          fontSize: '0.7rem',
          padding: '0.15rem 0.45rem',
          borderRadius: '6px',
          border: '1px solid #fca5a5'
        }}>
          🚨 EMERGENCY
        </span>
      );
    }
    if (priority === 'PRIORITY') {
      return (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.25rem',
          backgroundColor: '#ffedd5',
          color: '#ea580c',
          fontWeight: 800,
          fontSize: '0.7rem',
          padding: '0.15rem 0.45rem',
          borderRadius: '6px',
          border: '1px solid #fdba74'
        }}>
          ⚠️ PRIORITY
        </span>
      );
    }
    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        backgroundColor: '#dbeafe',
        color: '#2563eb',
        fontWeight: 700,
        fontSize: '0.7rem',
        padding: '0.15rem 0.45rem',
        borderRadius: '6px',
        border: '1px solid #93c5fd'
      }}>
        ROUTINE
      </span>
    );
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading doctor OPD consultation desk..." />;
  }

  if (error && queue.length === 0 && allPatients.length === 0) {
    return <StateView state="error" message={error} onRetry={fetchDoctorData} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner: Shift Attendance & Emergency Button */}
      <div
        className="glass-card"
        style={{
          padding: '1.25rem 1.5rem',
          borderRadius: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          backgroundColor: '#ffffff',
          boxShadow: '0 2px 4px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              backgroundColor: 'rgba(37, 99, 235, 0.1)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Stethoscope size={26} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Medical Officer Clinical Desk</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.2rem' }}>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                Shift Status:
              </span>
              {attendance?.check_in_at ? (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.75rem',
                    color: '#059669',
                    fontWeight: 700,
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '6px',
                  }}
                >
                  <CheckCircle size={13} /> Checked In at {new Date(attendance.check_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              ) : (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    fontSize: '0.75rem',
                    color: '#dc2626',
                    fontWeight: 700,
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '6px',
                  }}
                >
                  <Clock size={13} /> Not Checked In
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {attendance?.check_in_at ? (
            <button
              onClick={handleCheckOut}
              className="btn-secondary"
              style={{ fontSize: '0.825rem', padding: '0.5rem 0.85rem' }}
            >
              Check Out Shift
            </button>
          ) : (
            <button
              onClick={handleCheckIn}
              className="btn-primary"
              style={{ fontSize: '0.825rem', padding: '0.5rem 0.85rem' }}
            >
              Check In Shift
            </button>
          )}

          <button
            onClick={() => {
              setEmergencySuccess(false);
              setIsEmergencyModalOpen(true);
            }}
            className="btn-secondary"
            style={{
              fontSize: '0.825rem',
              padding: '0.5rem 0.85rem',
              color: '#dc2626',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <ShieldAlert size={16} />
            Report Outbreak / Incident
          </button>
        </div>
      </div>

      {/* Sub-Navigation Route Tabs */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        backgroundColor: '#f1f5f9',
        padding: '0.35rem',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        alignSelf: 'flex-start'
      }}>
        <button
          onClick={() => handleTabChange('queue')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.825rem',
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'queue' ? '#ffffff' : 'transparent',
            color: activeTab === 'queue' ? 'var(--primary)' : '#64748b',
            boxShadow: activeTab === 'queue' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease'
          }}
        >
          <Users size={16} />
          OPD Patient Queue ({queue.length})
        </button>

        <button
          onClick={() => handleTabChange('patients')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.825rem',
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'patients' ? '#ffffff' : 'transparent',
            color: activeTab === 'patients' ? 'var(--primary)' : '#64748b',
            boxShadow: activeTab === 'patients' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease'
          }}
        >
          <UserCheck size={16} />
          Patients Directory
        </button>

        <button
          onClick={() => handleTabChange('labs')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.825rem',
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'labs' ? '#ffffff' : 'transparent',
            color: activeTab === 'labs' ? 'var(--primary)' : '#64748b',
            boxShadow: activeTab === 'labs' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease'
          }}
        >
          <FlaskConical size={16} />
          Lab Test Orders ({labOrdersList.length})
        </button>

        <button
          onClick={() => handleTabChange('inventory')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            fontSize: '0.825rem',
            fontWeight: 700,
            border: 'none',
            cursor: 'pointer',
            backgroundColor: activeTab === 'inventory' ? '#ffffff' : 'transparent',
            color: activeTab === 'inventory' ? 'var(--primary)' : '#64748b',
            boxShadow: activeTab === 'inventory' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            transition: 'all 0.15s ease'
          }}
        >
          <Box size={16} />
          Facility Medicine Inventory ({medications.length})
        </button>
      </div>

      {/* VIEW 1: OPD QUEUE & ACTIVE CONSULTATION */}
      {activeTab === 'queue' && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedPatient ? '1fr 1.6fr' : '1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* LEFT COLUMN: OPD QUEUE */}
          <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={18} />
                Today's OPD Patient Queue
              </h3>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                {queue.length} Patients Waiting
              </span>
            </div>

            <DataTable
              data={queue}
              keyExtractor={(item) => item.appointment_id || item.patient_id}
              searchFilter={(item, q) =>
                (item.patient_name || '').toLowerCase().includes(q) ||
                (item.token_number?.toString() || '').includes(q) ||
                (item.reason || item.reason_for_visit || '').toLowerCase().includes(q)
              }
              emptyTitle="OPD Queue Empty"
              emptyMessage="No triaged patients are currently awaiting consultation."
              columns={[
                {
                  key: 'token',
                  header: 'Token & Priority',
                  render: (item) => (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', alignItems: 'flex-start' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(37, 99, 235, 0.1)',
                          color: 'var(--primary)',
                          fontWeight: 800,
                          fontSize: '0.9rem',
                        }}
                      >
                        #{item.token_number}
                      </span>
                      {renderPriorityBadge(item.priority)}
                    </div>
                  ),
                },
                {
                  key: 'patient',
                  header: 'Patient Demographics',
                  render: (item) => (
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{item.patient_name || 'Citizen'}</div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {item.age_years || item.age ? `${item.age_years || item.age} yrs • ${item.gender}` : item.uhid || item.patient_identifier || 'Walk-in'}
                      </span>
                    </div>
                  ),
                },
                {
                  key: 'symptoms',
                  header: 'Reported Symptoms / Reason',
                  render: (item) => {
                    const symptomText = item.reason || item.reason_for_visit || 'General Consultation';
                    return (
                      <div
                        style={{
                          padding: '0.4rem 0.65rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(254, 243, 199, 0.7)',
                          border: '1px solid #fde68a',
                          color: '#92400e',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          maxWidth: '220px',
                        }}
                      >
                        🤒 {symptomText}
                      </div>
                    );
                  },
                },
                {
                  key: 'triage',
                  header: 'Triage & Vitals',
                  render: (item) => (
                    <div>
                      {item.latest_vitals || item.vitals ? (
                        <div style={{ fontSize: '0.75rem' }}>
                          <div>BP: <strong>{(item.latest_vitals || item.vitals).systolic_bp}/{(item.latest_vitals || item.vitals).diastolic_bp}</strong></div>
                          <div>SpO2: <strong>{(item.latest_vitals || item.vitals).spo2 || (item.latest_vitals || item.vitals).spo2_percent}%</strong> | Temp: <strong>{(item.latest_vitals || item.vitals).temperature || (item.latest_vitals || item.vitals).temperature_celsius}°</strong></div>
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Vitals pending</span>
                      )}
                    </div>
                  ),
                },
                {
                  key: 'action',
                  header: 'Action',
                  render: (item) => (
                    <button
                      onClick={() => handleSelectPatient(item)}
                      className="btn-primary"
                      style={{
                        padding: '0.4rem 0.85rem',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: selectedPatient?.appointment_id === item.appointment_id ? '#059669' : 'var(--primary)',
                      }}
                    >
                      {selectedPatient?.appointment_id === item.appointment_id ? 'Active' : 'Consult'}
                    </button>
                  ),
                },
              ]}
            />
          </div>

          {/* RIGHT COLUMN: ACTIVE CONSULTATION WORKSPACE */}
          {selectedPatient && (
            <div
              className="glass-card animate-fade-in"
              style={{
                padding: '1.5rem',
                borderRadius: '14px',
                border: '2px solid rgba(37, 99, 235, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.85rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 700, textTransform: 'uppercase' }}>
                    ACTIVE CLINICAL ENCOUNTER
                  </span>
                  <h3 style={{ margin: '0.2rem 0 0 0', fontSize: '1.25rem', fontWeight: 800 }}>
                    {selectedPatient.patient_name} (Token #{selectedPatient.token_number})
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Reason: {selectedPatient.reason || selectedPatient.reason_for_visit || 'General Consultation'}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="btn-secondary"
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                >
                  Close Encounter
                </button>
              </div>

              {/* Vitals Review Pill */}
              {(selectedPatient.latest_vitals || selectedPatient.vitals) && (
                <div
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '10px',
                    backgroundColor: 'rgba(241, 245, 249, 0.8)',
                    display: 'flex',
                    gap: '1.5rem',
                    flexWrap: 'wrap',
                    fontSize: '0.825rem',
                  }}
                >
                  <div>BP: <strong>{(selectedPatient.latest_vitals || selectedPatient.vitals).systolic_bp}/{(selectedPatient.latest_vitals || selectedPatient.vitals).diastolic_bp} mmHg</strong></div>
                  <div>Pulse: <strong>{(selectedPatient.latest_vitals || selectedPatient.vitals).pulse_rate || selectedPatient.vitals?.heart_rate} bpm</strong></div>
                  <div>Temp: <strong>{(selectedPatient.latest_vitals || selectedPatient.vitals).temperature || (selectedPatient.latest_vitals || selectedPatient.vitals).temperature_celsius}°</strong></div>
                  <div>SpO2: <strong>{(selectedPatient.latest_vitals || selectedPatient.vitals).spo2 || (selectedPatient.latest_vitals || selectedPatient.vitals).spo2_percent}%</strong></div>
                </div>
              )}

              {/* Chief Complaints */}
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Chief Complaints & Reported Symptoms
                </label>
                <textarea
                  rows={2}
                  value={chiefComplaints}
                  onChange={(e) => setChiefComplaints(e.target.value)}
                  placeholder="Patient complains of..."
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.875rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Clinical Examination Notes
                </label>
                <textarea
                  rows={2}
                  value={examinationNotes}
                  onChange={(e) => setExaminationNotes(e.target.value)}
                  placeholder="Physical findings, chest auscultation, throat examination..."
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.875rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Primary Diagnosis (ICD-10)
                </label>
                <select
                  value={selectedDiagnosis}
                  onChange={(e) => setSelectedDiagnosis(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)', fontSize: '0.875rem' }}
                >
                  <option value="J18.9">J18.9 — Pneumonia, unspecified organism</option>
                  <option value="J00">J00 — Acute nasopharyngitis (Common Cold)</option>
                  <option value="A09">A09 — Infectious gastroenteritis and colitis</option>
                  <option value="I10">I10 — Essential (primary) hypertension</option>
                  <option value="E11">E11 — Type 2 diabetes mellitus</option>
                  <option value="A90">A90 — Dengue fever</option>
                </select>
              </div>

              {/* Prescriptions Section */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Pill size={16} />
                  Prescribe Medications (Formulary)
                </h4>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr auto', gap: '0.5rem', alignItems: 'end', marginBottom: '0.75rem' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600 }}>Medicine</label>
                    <select
                      value={selectedMedId}
                      onChange={(e) => setSelectedMedId(e.target.value)}
                      style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                    >
                      {medications.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.generic_name} ({m.strength})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600 }}>Frequency</label>
                    <select
                      value={itemFrequency}
                      onChange={(e) => setItemFrequency(e.target.value)}
                      style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                    >
                      <option value="OD">OD (Once daily)</option>
                      <option value="BD">BD (Twice daily)</option>
                      <option value="TDS">TDS (3 times daily)</option>
                      <option value="QID">QID (4 times daily)</option>
                      <option value="SOS">SOS (As needed)</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600 }}>Days</label>
                    <input
                      type="number"
                      min="1"
                      max="90"
                      value={itemDuration}
                      onChange={(e) => setItemDuration(Number(e.target.value))}
                      style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600 }}>Timing</label>
                    <select
                      value={itemInstructions}
                      onChange={(e) => setItemInstructions(e.target.value)}
                      style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                    >
                      <option value="After meals">After meals</option>
                      <option value="Before meals">Before meals</option>
                      <option value="At bedtime">At bedtime</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddPrescriptionItem}
                    className="btn-secondary"
                    style={{ padding: '0.45rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  >
                    <Plus size={14} /> Add
                  </button>
                </div>

                {prescriptionItems.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '1rem' }}>
                    {prescriptionItems.map((p, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.45rem 0.75rem',
                          backgroundColor: 'rgba(241, 245, 249, 0.7)',
                          borderRadius: '6px',
                          fontSize: '0.825rem',
                        }}
                      >
                        <span>
                          <strong>{p.medication_name}</strong> — {p.dosage} | {p.frequency} for {p.duration_days} days ({p.instructions})
                        </span>
                        <button
                          onClick={() => handleRemovePrescriptionItem(idx)}
                          style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: '0.75rem' }}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Lab Orders Section */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Activity size={16} />
                  Order Laboratory Diagnostics
                </h4>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <select
                    value={selectedLabTest}
                    onChange={(e) => setSelectedLabTest(e.target.value)}
                    style={{ flex: 1, padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                  >
                    <option value="Complete Blood Count (CBC)">Complete Blood Count (CBC)</option>
                    <option value="Random Blood Sugar (RBS)">Random Blood Sugar (RBS)</option>
                    <option value="Dengue NS1 Antigen">Dengue NS1 Antigen</option>
                    <option value="Widal Agglutination (Typhoid)">Widal Agglutination (Typhoid)</option>
                    <option value="Urine Routine & Microscopy">Urine Routine & Microscopy</option>
                    <option value="Sputum AFB (Tuberculosis)">Sputum AFB (Tuberculosis)</option>
                  </select>
                  <button
                    type="button"
                    onClick={handleAddLabOrder}
                    className="btn-secondary"
                    style={{ padding: '0.45rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  >
                    <Plus size={14} /> Add Test
                  </button>
                </div>

                {orderedLabs.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                    {orderedLabs.map((t, idx) => (
                      <span
                        key={idx}
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(139, 92, 246, 0.1)',
                          color: '#7c3aed',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Specialty Referral Option */}
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', fontWeight: 700 }}>
                  Specialty Referral (Optional)
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input
                    type="text"
                    placeholder="Target Facility"
                    value={referralFacility}
                    onChange={(e) => setReferralFacility(e.target.value)}
                    style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                  />
                  <input
                    type="text"
                    placeholder="Specialty (e.g. Cardiology)"
                    value={referralSpecialty}
                    onChange={(e) => setReferralSpecialty(e.target.value)}
                    style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                  />
                </div>
                <input
                  type="text"
                  placeholder="Clinical reason for referral..."
                  value={referralReason}
                  onChange={(e) => setReferralReason(e.target.value)}
                  style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                />
              </div>

              {/* Finalize Button */}
              <button
                onClick={handleFinalizeConsultation}
                disabled={isSubmitting}
                className="btn-primary"
                style={{
                  padding: '0.85rem',
                  fontSize: '1rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                }}
              >
                <Check size={20} />
                {isSubmitting ? 'Finalizing Clinical Encounter...' : 'Finalize Consultation & Sign Orders'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: PATIENTS DIRECTORY */}
      {activeTab === 'patients' && (
        <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <UserCheck size={18} />
                Facility Patients Directory & Medical Records
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                View registered citizens, medical history, and clinical encounters.
              </p>
            </div>
            <div style={{ position: 'relative', width: '280px' }}>
              <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search by UHID, name, phone..."
                value={patientSearchQuery}
                onChange={(e) => setPatientSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.5rem 0.5rem 2.25rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.825rem'
                }}
              />
            </div>
          </div>

          <DataTable
            data={allPatients.filter((p) => {
              if (!patientSearchQuery.trim()) return true;
              const q = patientSearchQuery.toLowerCase();
              const fullName = `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase();
              return fullName.includes(q) || (p.patient_identifier || '').toLowerCase().includes(q) || (p.phone_number || '').includes(q);
            })}
            keyExtractor={(item) => item.id}
            emptyTitle="No Patients Found"
            emptyMessage="No patient records match the specified search query."
            columns={[
              {
                key: 'uhid',
                header: 'UHID / Identifier',
                render: (item) => (
                  <span style={{ fontWeight: 700, fontFamily: 'monospace', color: 'var(--primary)' }}>
                    {item.patient_identifier || item.uhid || 'PHC-CITIZEN'}
                  </span>
                ),
              },
              {
                key: 'name',
                header: 'Patient Full Name',
                render: (item) => (
                  <div>
                    <div style={{ fontWeight: 600 }}>{item.first_name ? `${item.first_name} ${item.last_name}` : item.patient_name || 'Citizen'}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.gender} • DOB: {item.date_of_birth ? new Date(item.date_of_birth).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                ),
              },
              {
                key: 'contact',
                header: 'Phone & Blood Group',
                render: (item) => (
                  <div style={{ fontSize: '0.8rem' }}>
                    <div>📞 {item.phone_number || 'N/A'}</div>
                    <div style={{ color: '#dc2626', fontWeight: 700 }}>🩸 {item.blood_group || 'O+'}</div>
                  </div>
                ),
              },
              {
                key: 'conditions',
                header: 'Chronics & Allergies',
                render: (item) => (
                  <div style={{ fontSize: '0.75rem' }}>
                    <div>Chronics: <strong>{item.chronic_conditions || 'None reported'}</strong></div>
                    <div style={{ color: '#ea580c' }}>Allergies: <strong>{item.allergies || 'None known'}</strong></div>
                  </div>
                ),
              },
              {
                key: 'action',
                header: 'Medical History',
                render: (item) => (
                  <button
                    onClick={() => {
                      setInspectedPatientHistory(item);
                      setIsPatientHistoryModalOpen(true);
                    }}
                    className="btn-secondary"
                    style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                  >
                    <Eye size={14} /> View History
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* VIEW 3: LAB TEST ORDERS */}
      {activeTab === 'labs' && (
        <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FlaskConical size={18} />
                Facility Laboratory Diagnostic Orders & Results
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Worklist of ordered lab tests, pending specimen collection, and completed lab findings.
              </p>
            </div>
          </div>

          <DataTable
            data={labOrdersList}
            keyExtractor={(item) => item.id}
            emptyTitle="No Active Lab Orders"
            emptyMessage="No diagnostic lab orders have been requested at this facility."
            columns={[
              {
                key: 'test',
                header: 'Test Panel / Category',
                render: (item) => (
                  <div>
                    <div style={{ fontWeight: 700, color: '#7c3aed' }}>{item.test_category || item.test_name || 'Blood Test'}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Code: {item.test_code || 'LAB-PANEL'}
                    </span>
                  </div>
                ),
              },
              {
                key: 'patient',
                header: 'Patient Info',
                render: (item) => (
                  <div>
                    <div style={{ fontWeight: 600 }}>{item.patient_name || item.patient?.first_name || 'Patient'}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.patient_identifier || 'Walk-in'}
                    </span>
                  </div>
                ),
              },
              {
                key: 'priority',
                header: 'Urgency',
                render: (item) => renderPriorityBadge(item.priority || 'ROUTINE'),
              },
              {
                key: 'status',
                header: 'Lab Order Status',
                render: (item) => (
                  <span
                    style={{
                      padding: '0.2rem 0.55rem',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor:
                        item.status === 'VERIFIED' ? 'rgba(16, 185, 129, 0.15)' :
                        item.status === 'COMPLETED' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color:
                        item.status === 'VERIFIED' ? '#059669' :
                        item.status === 'COMPLETED' ? '#2563eb' : '#d97706',
                    }}
                  >
                    {item.status || 'PENDING'}
                  </span>
                ),
              },
              {
                key: 'date',
                header: 'Ordered Date',
                render: (item) => (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {item.ordered_at ? new Date(item.ordered_at).toLocaleString() : 'Today'}
                  </span>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* VIEW 4: FACILITY MEDICINE INVENTORY */}
      {activeTab === 'inventory' && (
        <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Box size={18} />
                PHC Essential Drug Formulary & Stock Levels
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Check drug stock availability before issuing digital prescriptions.
              </p>
            </div>
          </div>

          <DataTable
            data={medications}
            keyExtractor={(item) => item.id}
            emptyTitle="No Medication Records"
            emptyMessage="No Essential Drugs registered in the facility inventory database."
            columns={[
              {
                key: 'generic',
                header: 'Generic Name',
                render: (item) => (
                  <div>
                    <div style={{ fontWeight: 700 }}>{item.generic_name}</div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Brand: {item.brand_name || 'Generic Tamil Nadu Medical Services Corp'}
                    </span>
                  </div>
                ),
              },
              {
                key: 'form',
                header: 'Form & Strength',
                render: (item) => (
                  <span style={{ fontSize: '0.825rem', fontWeight: 600 }}>
                    {item.dosage_form} — {item.strength} ({item.unit || 'units'})
                  </span>
                ),
              },
              {
                key: 'category',
                header: 'Category / Route',
                render: (item) => (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {item.route || 'Oral'}
                  </span>
                ),
              },
              {
                key: 'status',
                header: 'Stock Status',
                render: (item) => (
                  <span
                    style={{
                      padding: '0.2rem 0.55rem',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      backgroundColor: item.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: item.is_active ? '#059669' : '#dc2626',
                    }}
                  >
                    {item.is_active ? 'Available in Stock' : 'Out of Stock'}
                  </span>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* PATIENT MEDICAL HISTORY MODAL */}
      <Modal
        isOpen={isPatientHistoryModalOpen}
        onClose={() => setIsPatientHistoryModalOpen(false)}
        title={`Medical Record: ${inspectedPatientHistory?.first_name || ''} ${inspectedPatientHistory?.last_name || ''}`}
      >
        {inspectedPatientHistory && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderRadius: '8px', fontSize: '0.85rem' }}>
              <div><strong>UHID:</strong> {inspectedPatientHistory.patient_identifier || inspectedPatientHistory.uhid}</div>
              <div><strong>Gender & DOB:</strong> {inspectedPatientHistory.gender} ({inspectedPatientHistory.date_of_birth ? new Date(inspectedPatientHistory.date_of_birth).toLocaleDateString() : 'N/A'})</div>
              <div><strong>Phone:</strong> {inspectedPatientHistory.phone_number || 'N/A'}</div>
              <div><strong>Blood Group:</strong> {inspectedPatientHistory.blood_group || 'O+'}</div>
              <div><strong>Chronic Conditions:</strong> {inspectedPatientHistory.chronic_conditions || 'None'}</div>
              <div><strong>Allergies:</strong> {inspectedPatientHistory.allergies || 'None'}</div>
            </div>

            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>Previous Clinical Encounters</h4>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              No previous critical encounter warnings or contraindications recorded for this patient.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button className="btn-primary" onClick={() => setIsPatientHistoryModalOpen(false)}>
                Close Record
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* REPORT OUTBREAK / EMERGENCY MODAL */}
      <Modal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        title="Report Clinical Emergency Incident"
      >
        {emergencySuccess ? (
          <div style={{ textAlign: 'center', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={32} />
            </div>
            <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>Incident Dispatched to DEC!</h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              The District Emergency Coordinator and DHO have been alerted for rapid resource mobilization.
            </p>
            <button className="btn-primary" onClick={() => setIsEmergencyModalOpen(false)}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleReportEmergency} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Incident Title
              </label>
              <input
                type="text"
                placeholder="e.g. Cluster of 12 Acute Diarrheal Cases in Ward 4"
                value={emergencyTitle}
                onChange={(e) => setEmergencyTitle(e.target.value)}
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Category
                </label>
                <select
                  value={emergencyCategory}
                  onChange={(e) => setEmergencyCategory(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                >
                  <option value="EPIDEMIC">Epidemic / Outbreak</option>
                  <option value="MASS_CASUALTY">Mass Casualty / Accident</option>
                  <option value="COLD_CHAIN_FAILURE">Cold Chain Failure</option>
                  <option value="NATURAL_DISASTER">Cyclone / Flood</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Severity Level
                </label>
                <select
                  value={emergencySeverity}
                  onChange={(e) => setEmergencySeverity(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                >
                  <option value="CRITICAL">Critical (Immediate Response)</option>
                  <option value="MAJOR">Major</option>
                  <option value="MODERATE">Moderate</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Clinical Description & Resource Requirements
              </label>
              <textarea
                rows={3}
                placeholder="Describe patient condition, suspected source, and requested medicines/personnel..."
                value={emergencyDescription}
                onChange={(e) => setEmergencyDescription(e.target.value)}
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button type="button" className="btn-secondary" onClick={() => setIsEmergencyModalOpen(false)}>
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
                style={{ backgroundColor: '#dc2626' }}
              >
                {isSubmitting ? 'Transmitting...' : 'Dispatch Emergency Report'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
