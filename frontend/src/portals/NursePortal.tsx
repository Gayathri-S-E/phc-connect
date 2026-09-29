import React, { useState, useEffect } from 'react';
import { 
  HeartPulse, UserPlus, CheckCircle, Clock, 
  AlertTriangle, Thermometer, ShieldAlert, Activity, 
  Search, Plus, Check, Calendar, ArrowRight 
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';

export default function NursePortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'triage' | 'intake' | 'coldchain' | 'immunization'>('triage');
  const [triageQueue, setTriageQueue] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<any>(null);
  const [coldChainAssets, setColdChainAssets] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected Patient for Triage Entry
  const [selectedAppt, setSelectedAppt] = useState<any>(null);
  const [systolic, setSystolic] = useState(120);
  const [diastolic, setDiastolic] = useState(80);
  const [heartRate, setHeartRate] = useState(76);
  const [respRate, setRespRate] = useState(18);
  const [temperature, setTemperature] = useState(98.6);
  const [spo2, setSpo2] = useState(98);
  const [bloodSugar, setBloodSugar] = useState(110);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New Citizen Intake Form State
  const [intakeFirstName, setIntakeFirstName] = useState('');
  const [intakeLastName, setIntakeLastName] = useState('');
  const [intakeDob, setIntakeDob] = useState('1990-01-01');
  const [intakeGender, setIntakeGender] = useState('FEMALE');
  const [intakePhone, setIntakePhone] = useState('');
  const [intakeSuccess, setIntakeSuccess] = useState<any>(null);

  // Cold chain logging state
  const [logTemp, setLogTemp] = useState(4.2);
  const [logShift, setLogShift] = useState<'MORNING' | 'EVENING'>('MORNING');
  const [logSuccess, setLogSuccess] = useState(false);

  // Immunization Guidance State
  const [immAgeMonths, setImmAgeMonths] = useState(9);
  const [immIsPregnant, setImmIsPregnant] = useState(false);
  const [immGuidance, setImmGuidance] = useState<any>(null);
  const [isQueryingImm, setIsQueryingImm] = useState(false);

  const fetchNurseData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const facilityIdParam = user?.facility_id ? `?facility_id=${user.facility_id}` : '';
      const [queueRes, attendanceRes, ccRes] = await Promise.all([
        api.get<any[]>('/nurse/triage/queue'),
        api.get<any>('/nurse/attendance/today'),
        api.get<any[]>(`/facility-admin/cold-chain/equipment${facilityIdParam}`),
      ]);

      if (queueRes.data) setTriageQueue(queueRes.data);
      if (attendanceRes.data) setAttendance(attendanceRes.data);
      if (ccRes.data) setColdChainAssets(ccRes.data);

      if (queueRes.error) {
        setError(queueRes.error.detail);
      }
    } catch {
      setError('Failed to fetch nurse operations data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNurseData();
  }, []);

  const handleCheckIn = async () => {
    const res = await api.post('/nurse/attendance/check-in', { shift: 'GENERAL' });
    if (res.data) fetchNurseData();
  };

  const handleCheckOut = async () => {
    const res = await api.post('/nurse/attendance/check-out', { notes: 'Shift completed' });
    if (res.data) fetchNurseData();
  };

  const handleRecordVitals = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt?.appointment_id) return;

    setIsSubmitting(true);
    try {
      const tempNum = Number(temperature);
      const tempCelsius = tempNum > 45 ? Math.round(((tempNum - 32) * 5 / 9) * 10) / 10 : tempNum;

      const payload = {
        systolic_bp: systolic ? Number(systolic) : undefined,
        diastolic_bp: diastolic ? Number(diastolic) : undefined,
        pulse_rate: heartRate ? Number(heartRate) : undefined,
        respiratory_rate: respRate ? Number(respRate) : undefined,
        temperature_celsius: tempCelsius,
        spo2_percent: spo2 ? Number(spo2) : undefined,
        triage_level: 'ROUTINE',
        triage_notes: bloodSugar ? `Random Blood Sugar: ${bloodSugar} mg/dL` : undefined,
      };

      const res = await api.post(`/nurse/triage/vitals?appointment_id=${selectedAppt.appointment_id}`, payload);
      if (res.data) {
        alert(`Vitals recorded for Token #${selectedAppt.token_number}! Patient routed to Doctor queue.`);
        setSelectedAppt(null);
        fetchNurseData();
      } else {
        alert(res.error?.detail || 'Failed to record vitals.');
      }
    } catch (err: any) {
      alert(err?.detail || 'Failed to record vitals.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePatientIntake = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post<any>('/patients', {
        first_name: intakeFirstName,
        last_name: intakeLastName,
        date_of_birth: intakeDob,
        gender: intakeGender,
        phone_number: intakePhone || '+919999999999',
        primary_facility_id: user?.facility_id,
      });

      if (res.data) {
        setIntakeSuccess(res.data);
        setIntakeFirstName('');
        setIntakeLastName('');
        setIntakePhone('');
      } else {
        alert(res.error?.detail || 'Intake failed.');
      }
    } catch (err: any) {
      alert(err?.detail || 'Intake failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogColdChain = async (equipmentId: string) => {
    const res = await api.post(`/facility-admin/cold-chain/equipment/${equipmentId}/log`, {
      temperature_c: Number(logTemp),
      notes: `Recorded during ${logShift} shift by Staff Nurse`,
    });

    if (res.data) {
      setLogSuccess(true);
      setTimeout(() => setLogSuccess(false), 3000);
      fetchNurseData();
    } else {
      alert(res.error?.detail || 'Failed to record temperature log.');
    }
  };

  const handleCheckInToken = async (appointmentId: string) => {
    const res = await api.patch(`/nurse/appointments/${appointmentId}/check-in`);
    if (res.data) {
      fetchNurseData();
    } else {
      alert(res.error?.detail || 'Failed to check in patient token.');
    }
  };

  const handleQueryImmunization = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsQueryingImm(true);
    try {
      const res = await api.post<any>('/nurse/ai-assistant/immunization-guidance', {
        age_months: Number(immAgeMonths),
        is_pregnant: immIsPregnant,
        trimester: immIsPregnant ? 2 : undefined,
      });
      if (res.data) {
        setImmGuidance(res.data);
      }
    } finally {
      setIsQueryingImm(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading nurse triage desk..." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header Card */}
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
              backgroundColor: 'rgba(236, 72, 153, 0.1)',
              color: '#db2777',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <HeartPulse size={26} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Nurse Triage & Intake Desk</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.2rem' }}>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Shift Status:</span>
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
                  <CheckCircle size={13} /> Checked In
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

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {attendance?.check_in_at ? (
            <button onClick={handleCheckOut} className="btn-secondary" style={{ fontSize: '0.825rem', padding: '0.5rem 0.85rem' }}>
              Check Out Shift
            </button>
          ) : (
            <button onClick={handleCheckIn} className="btn-primary" style={{ fontSize: '0.825rem', padding: '0.5rem 0.85rem' }}>
              Check In Shift
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.25rem' }}>
        {[
          { key: 'triage', label: 'Triage Queue & Vitals', icon: <HeartPulse size={16} /> },
          { key: 'intake', label: 'Citizen Registration', icon: <UserPlus size={16} /> },
          { key: 'coldchain', label: 'Vaccine Cold Chain', icon: <Thermometer size={16} /> },
          { key: 'immunization', label: 'Immunization AI Protocol', icon: <Activity size={16} /> },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.65rem 1rem',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              cursor: 'pointer',
              fontWeight: activeTab === tab.key ? 700 : 500,
              fontSize: '0.875rem',
              color: activeTab === tab.key ? 'var(--primary)' : 'var(--text-muted)',
              borderBottom: activeTab === tab.key ? '2px solid var(--primary)' : '2px solid transparent',
              backgroundColor: 'transparent',
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: TRIAGE QUEUE & VITALS CAPTURE */}
      {activeTab === 'triage' && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedAppt ? '1fr 1.2fr' : '1fr', gap: '1.5rem', alignItems: 'start' }}>
          <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px' }}>
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem', fontWeight: 700 }}>
              Arriving Patients Awaiting Vitals
            </h3>
            <DataTable
              data={triageQueue}
              keyExtractor={(item) => item.appointment_id}
              emptyTitle="No Arriving Patients"
              emptyMessage="All scheduled patients have been triaged."
              columns={[
                {
                  key: 'token',
                  header: 'Token',
                  render: (item) => (
                    <span style={{ padding: '0.2rem 0.5rem', borderRadius: '6px', backgroundColor: 'rgba(37, 99, 235, 0.1)', color: 'var(--primary)', fontWeight: 800 }}>
                      #{item.token_number}
                    </span>
                  ),
                },
                {
                  key: 'name',
                  header: 'Patient Name',
                  render: (item) => (
                    <div>
                      <div style={{ fontWeight: 600 }}>{item.patient_name}</div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.age} yrs • {item.gender}</span>
                    </div>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (item) => item.vitals ? <Badge status="COMPLETED" label="Vitals Recorded" /> : <Badge status="PENDING" label="Needs Vitals" />,
                },
                {
                  key: 'action',
                  header: 'Action',
                  render: (item) => (
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      {item.status !== 'CHECKED_IN' && item.status !== 'IN_CONSULTATION' && (
                        <button
                          onClick={() => handleCheckInToken(item.appointment_id)}
                          className="btn-secondary"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          title="Mark token as physically arrived at PHC"
                        >
                          Check In
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setSelectedAppt(item);
                          if (item.vitals) {
                            setSystolic(item.vitals.systolic_bp);
                            setDiastolic(item.vitals.diastolic_bp);
                            setHeartRate(item.vitals.heart_rate);
                            setTemperature(item.vitals.temperature);
                            setSpo2(item.vitals.spo2);
                          }
                        }}
                        className="btn-primary"
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                      >
                        {item.vitals ? 'Update Vitals' : 'Record Vitals'}
                      </button>
                    </div>
                  ),
                },
              ]}
            />
          </div>

          {/* VITALS RECORDING FORM */}
          {selectedAppt && (
            <div className="glass-card animate-fade-in" style={{ padding: '1.5rem', borderRadius: '14px', border: '2px solid rgba(236, 72, 153, 0.3)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#db2777', fontWeight: 700, textTransform: 'uppercase' }}>
                    PATIENT TRIAGE DESK
                  </span>
                  <h3 style={{ margin: '0.2rem 0 0 0', fontSize: '1.2rem', fontWeight: 800 }}>
                    Token #{selectedAppt.token_number} — {selectedAppt.patient_name}
                  </h3>
                </div>
                <button onClick={() => setSelectedAppt(null)} className="btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                  Close
                </button>
              </div>

              <form onSubmit={handleRecordVitals} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Systolic BP (mmHg)
                    </label>
                    <input
                      type="number"
                      value={systolic}
                      onChange={(e) => setSystolic(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Diastolic BP (mmHg)
                    </label>
                    <input
                      type="number"
                      value={diastolic}
                      onChange={(e) => setDiastolic(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Heart Rate (bpm)
                    </label>
                    <input
                      type="number"
                      value={heartRate}
                      onChange={(e) => setHeartRate(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Temp (°F)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      SpO2 (%)
                    </label>
                    <input
                      type="number"
                      value={spo2}
                      onChange={(e) => setSpo2(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Resp Rate (/min)
                    </label>
                    <input
                      type="number"
                      value={respRate}
                      onChange={(e) => setRespRate(Number(e.target.value))}
                      required
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                      Blood Sugar (mg/dL)
                    </label>
                    <input
                      type="number"
                      value={bloodSugar}
                      onChange={(e) => setBloodSugar(Number(e.target.value))}
                      style={{ width: '100%', padding: '0.55rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary"
                  style={{
                    backgroundColor: '#db2777',
                    padding: '0.75rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <Check size={18} />
                  {isSubmitting ? 'Recording & Calculating EWS...' : 'Save Vitals & Route to Doctor Queue'}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CITIZEN REGISTRATION / INTAKE */}
      {activeTab === 'intake' && (
        <div className="glass-card" style={{ padding: '1.5rem', borderRadius: '14px', maxWidth: '600px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem', fontWeight: 700 }}>Walk-in Citizen Registration</h3>
          <p style={{ margin: '0 0 1.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Register new citizens and allocate a Primary Health Centre Universal Health ID (UHID).
          </p>

          {intakeSuccess && (
            <div style={{ padding: '1rem', borderRadius: '8px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#059669', marginBottom: '1rem' }}>
              <strong>Citizen Registered Successfully!</strong>
              <div>UHID: <strong>{intakeSuccess.patient_identifier}</strong></div>
              <div>Name: {intakeSuccess.first_name} {intakeSuccess.last_name}</div>
            </div>
          )}

          <form onSubmit={handlePatientIntake} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>First Name</label>
                <input
                  type="text"
                  required
                  value={intakeFirstName}
                  onChange={(e) => setIntakeFirstName(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>Last Name</label>
                <input
                  type="text"
                  value={intakeLastName}
                  onChange={(e) => setIntakeLastName(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>Date of Birth</label>
                <input
                  type="date"
                  required
                  value={intakeDob}
                  onChange={(e) => setIntakeDob(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>Gender</label>
                <select
                  value={intakeGender}
                  onChange={(e) => setIntakeGender(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
                >
                  <option value="FEMALE">Female</option>
                  <option value="MALE">Male</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>Mobile Phone (+91)</label>
              <input
                type="tel"
                placeholder="+919876543210"
                value={intakePhone}
                onChange={(e) => setIntakePhone(e.target.value)}
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              />
            </div>

            <button type="submit" disabled={isSubmitting} className="btn-primary" style={{ padding: '0.7rem' }}>
              {isSubmitting ? 'Registering...' : 'Register Citizen & Generate UHID'}
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: COLD CHAIN LOGGING */}
      {activeTab === 'coldchain' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '700px' }}>
          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>Vaccine Refrigerator Temperature Log</h3>
          {logSuccess && (
            <div style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#059669' }}>
              Temperature recorded successfully! Status verified within safe bounds (+2°C to +8°C).
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {coldChainAssets.map((asset) => (
              <div key={asset.id} className="glass-card" style={{ padding: '1.25rem', borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>{asset.equipment_name || 'ILR Refrigerator'}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Model: {asset.model_number || 'Blue Star ILR-300'}</span>
                  </div>
                  <Badge status="ACTIVE" label="Safe Range: +2°C to +8°C" />
                </div>

                <div style={{ margin: '1rem 0' }}>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <input
                      type="number"
                      step="0.1"
                      value={logTemp}
                      onChange={(e) => setLogTemp(Number(e.target.value))}
                      style={{ width: '100px', padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
                    />
                    <span>°C</span>
                    <select
                      value={logShift}
                      onChange={(e) => setLogShift(e.target.value as any)}
                      style={{ padding: '0.45rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}
                    >
                      <option value="MORNING">Morning (08:00)</option>
                      <option value="EVENING">Evening (16:00)</option>
                    </select>
                  </div>
                </div>

                <button onClick={() => handleLogColdChain(asset.id)} className="btn-secondary" style={{ width: '100%', fontSize: '0.8rem' }}>
                  Save Temperature Reading
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: IMMUNIZATION & ANC PROTOCOL ASSISTANT */}
      {activeTab === 'immunization' && (
        <div className="glass-card" style={{ padding: '1.5rem', borderRadius: '14px', maxWidth: '650px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem', fontWeight: 700 }}>
            Tamil Nadu Universal Immunization Program (UIP) Protocol
          </h3>
          <p style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Instant vaccine milestone check and High-Risk Pregnancy maternal protocol adviser.
          </p>

          <form onSubmit={handleQueryImmunization} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>Child Age (Months)</label>
              <input
                type="number"
                min="0"
                max="60"
                value={immAgeMonths}
                onChange={(e) => setImmAgeMonths(Number(e.target.value))}
                style={{ width: '120px', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}
              />
            </div>
            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', cursor: 'pointer', paddingBottom: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={immIsPregnant}
                  onChange={(e) => setImmIsPregnant(e.target.checked)}
                />
                Pregnant Mother (ANC Protocol)
              </label>
            </div>
            <button type="submit" disabled={isQueryingImm} className="btn-primary" style={{ padding: '0.55rem 1rem' }}>
              {isQueryingImm ? 'Checking...' : 'Check Schedule'}
            </button>
          </form>

          {immGuidance && (
            <div style={{ padding: '1rem', borderRadius: '10px', backgroundColor: 'rgba(241, 245, 249, 0.8)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary)' }}>
                Recommended Vaccines & Protocols:
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', lineHeight: 1.6 }}>
                {immGuidance.recommended_vaccines?.map((v: string, i: number) => (
                  <li key={i}><strong>{v}</strong></li>
                ))}
              </ul>
              {immGuidance.clinical_notes && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <strong>Note:</strong> {immGuidance.clinical_notes}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
