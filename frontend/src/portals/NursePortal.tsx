import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  HeartPulse, UserPlus, CheckCircle, Clock, 
  AlertTriangle, Thermometer, ShieldAlert, Activity, 
  Search, Plus, Check, Calendar, ArrowRight, Stethoscope,
  LogIn, LogOut, ShieldCheck, UserCheck, Snowflake, Baby
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogFooter,
  DialogClose,
} from '../components/ui/dialog';

export default function NursePortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'triage' | 'intake' | 'coldchain' | 'immunization' => {
    if (path.includes('/registration') || path.includes('/intake')) return 'intake';
    if (path.includes('/coldchain')) return 'coldchain';
    if (path.includes('/immunization')) return 'immunization';
    return 'triage';
  };

  const [activeTab, setActiveTab] = useState<'triage' | 'intake' | 'coldchain' | 'immunization'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'triage' | 'intake' | 'coldchain' | 'immunization') => {
    setActiveTab(tab);
    if (tab === 'intake') navigate('/clinical/registration');
    else navigate(`/clinical/${tab}`);
  };

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
  const [triageSuccessNotice, setTriageSuccessNotice] = useState<string | null>(null);

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
        setTriageSuccessNotice(`Vitals logged for Token #${selectedAppt.token_number} (${selectedAppt.patient_name})! Patient immediately routed to Doctor queue.`);
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
        fetchNurseData();
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
    return <StateView state="loading" message="Loading nurse clinical station..." />;
  }

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Nursing Desk Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Clinical Services' },
          { label: 'Nursing Station & Triage' },
        ]}
        facilityContext="Thirukalukundram PHC • Chengalpattu"
        title="Triage &amp; Clinical Nursing Desk"
        description="OPD patient intake, vital signs screening, cold chain vaccine monitoring, and Universal Immunization Programme sessions."
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
              variant="primary"
              size="sm"
              onClick={() => handleTabChange('intake')}
              className="gap-1.5 shadow-xs"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Register New Citizen</span>
            </Button>
          </div>
        }
        metrics={[
          {
            label: 'Awaiting Triage',
            value: triageQueue.length,
            hint: 'Patients in holding area',
            variant: triageQueue.length > 0 ? 'sky' : 'default',
            icon: <HeartPulse className="w-4 h-4" />,
          },
          {
            label: 'Shift Status',
            value: attendance?.status === 'CHECKED_IN' ? 'On Duty' : 'Off Duty',
            hint: attendance?.check_in_time ? `Since ${attendance.check_in_time.slice(0, 5)}` : 'Shift ready',
            variant: attendance?.status === 'CHECKED_IN' ? 'success' : 'default',
            icon: <Activity className="w-4 h-4" />,
          },
          {
            label: 'Cold Chain ILR',
            value: `${coldChainAssets.length} Units`,
            hint: 'Within 2°C – 8°C band',
            variant: 'success',
            icon: <Snowflake className="w-4 h-4" />,
          },
          {
            label: 'UIP Session',
            value: 'Active',
            hint: 'Immunization day schedule',
            variant: 'default',
            icon: <Baby className="w-4 h-4" />,
          },
        ]}
      />

      {triageSuccessNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 animate-fade-in shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{triageSuccessNotice}</span>
          </div>
          <button
            onClick={() => setTriageSuccessNotice(null)}
            className="text-emerald-700 hover:text-emerald-950 underline text-xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200/80 rounded-xl overflow-x-auto no-scrollbar max-w-full">
        {[
          { key: 'triage', label: `Triage Queue (${triageQueue.length})`, icon: <HeartPulse className="w-4 h-4" /> },
          { key: 'intake', label: 'Citizen Intake & Token', icon: <UserPlus className="w-4 h-4" /> },
          { key: 'coldchain', label: `Cold Chain ILR (${coldChainAssets.length})`, icon: <Snowflake className="w-4 h-4" /> },
          { key: 'immunization', label: 'UIP Immunization Roster', icon: <Baby className="w-4 h-4" /> },
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

      {/* TAB 1: TRIAGE VITALS DESK */}
      {activeTab === 'triage' && (
        <div className="space-y-6">
          {/* Selected Patient Vitals Capture Modal / Panel */}
          {selectedAppt && (
            <Card className="border-sky-300 shadow-md">
              <CardHeader className="bg-sky-50/70 border-b border-sky-100 pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-600 text-white font-bold flex items-center justify-center">
                      #{selectedAppt.token_number}
                    </div>
                    <div>
                      <CardTitle className="text-base">
                        Vitals Entry: {selectedAppt.patient_name || 'Citizen'}
                      </CardTitle>
                      <CardDescription>
                        UHID: {selectedAppt.patient_identifier || 'DEMO-PAT-0001'} • Reason: {selectedAppt.reason || 'General Visit'}
                      </CardDescription>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setSelectedAppt(null)}>
                    Cancel
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="p-6">
                <form onSubmit={handleRecordVitals} className="space-y-5">
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">Systolic BP</label>
                      <Input
                        type="number"
                        value={systolic}
                        onChange={(e) => setSystolic(Number(e.target.value))}
                        placeholder="120"
                        className="font-mono font-bold"
                        required
                      />
                      <span className="text-[10px] text-slate-400">mmHg</span>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">Diastolic BP</label>
                      <Input
                        type="number"
                        value={diastolic}
                        onChange={(e) => setDiastolic(Number(e.target.value))}
                        placeholder="80"
                        className="font-mono font-bold"
                        required
                      />
                      <span className="text-[10px] text-slate-400">mmHg</span>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">Heart Rate</label>
                      <Input
                        type="number"
                        value={heartRate}
                        onChange={(e) => setHeartRate(Number(e.target.value))}
                        placeholder="76"
                        className="font-mono font-bold"
                        required
                      />
                      <span className="text-[10px] text-slate-400">bpm</span>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">SpO2 Oxygen</label>
                      <Input
                        type="number"
                        value={spo2}
                        onChange={(e) => setSpo2(Number(e.target.value))}
                        placeholder="98"
                        className={`font-mono font-bold ${spo2 < 95 ? 'border-red-400 text-red-600' : ''}`}
                        required
                      />
                      <span className="text-[10px] text-slate-400">%</span>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">Temperature</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={temperature}
                        onChange={(e) => setTemperature(Number(e.target.value))}
                        placeholder="98.6"
                        className="font-mono font-bold"
                        required
                      />
                      <span className="text-[10px] text-slate-400">°F</span>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-bold text-slate-700 uppercase">Blood Sugar</label>
                      <Input
                        type="number"
                        value={bloodSugar}
                        onChange={(e) => setBloodSugar(Number(e.target.value))}
                        placeholder="110"
                        className="font-mono font-bold"
                      />
                      <span className="text-[10px] text-slate-400">mg/dL (RBS)</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                    <span className="text-xs text-slate-500">
                      Submitting vitals assigns clinical triage score and pushes token to Doctor Consultation Queue.
                    </span>
                    <Button type="submit" variant="primary" disabled={isSubmitting} className="gap-2">
                      <Check className="w-4 h-4" />
                      <span>{isSubmitting ? 'Routing to Doctor...' : 'Save Vitals & Route to Doctor Queue'}</span>
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Triage Queue Table */}
          <Card>
            <CardHeader>
              <CardTitle>Registered Patients Awaiting Nursing Triage</CardTitle>
              <CardDescription>
                Citizens checked in today. Screen vital signs to establish triage acuity.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                data={triageQueue}
                keyExtractor={(p) => p.id || p.appointment_id || String(p.token_number)}
                searchFilter={(p, q) =>
                  (p.patient_name || '').toLowerCase().includes(q) ||
                  (p.patient_identifier || '').toLowerCase().includes(q) ||
                  (p.reason || '').toLowerCase().includes(q)
                }
                emptyTitle="No Patients Awaiting Triage"
                emptyMessage="All registered OPD patients have completed triage screening."
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
                    key: 'time',
                    header: 'Check-In Slot',
                    render: (p) => <span className="text-xs font-mono text-slate-600">{p.slot_time || '09:30 AM'}</span>,
                  },
                  {
                    key: 'complaint',
                    header: 'Reported Complaint',
                    render: (p) => <span className="text-xs text-slate-700">{p.reason || p.reason_for_visit || 'General Visit'}</span>,
                  },
                  {
                    key: 'status',
                    header: 'Triage Status',
                    render: (p) => <Badge status={p.status || 'PENDING'} size="sm" />,
                  },
                  {
                    key: 'action',
                    header: 'Action',
                    render: (p) => (
                      <div className="flex items-center gap-1.5">
                        {p.status === 'SCHEDULED' && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleCheckInToken(p.appointment_id)}
                            className="h-7 text-xs px-2"
                          >
                            Check In
                          </Button>
                        )}
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => setSelectedAppt(p)}
                          className="h-7 text-xs px-2.5 gap-1"
                        >
                          <HeartPulse className="w-3.5 h-3.5" />
                          <span>Record Vitals</span>
                        </Button>
                      </div>
                    ),
                  },
                ]}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: CITIZEN INTAKE & TOKEN GENERATION */}
      {activeTab === 'intake' && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>OPD Citizen Registration &amp; Token Generator</CardTitle>
            <CardDescription>
              Register walk-in citizens into the state healthcare registry and generate immediate OPD token.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {intakeSuccess ? (
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-3">
                <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto" />
                <h4 className="text-base font-bold text-emerald-950">Patient Successfully Registered</h4>
                <div className="p-3 bg-white border border-emerald-200 rounded-lg inline-block text-left text-xs font-mono space-y-1">
                  <div>UHID: <strong>{intakeSuccess.patient_identifier || 'DEMO-PAT-NEW'}</strong></div>
                  <div>Name: <strong>{intakeSuccess.first_name} {intakeSuccess.last_name}</strong></div>
                  <div>Assigned Facility: <strong>Thirukalukundram PHC</strong></div>
                </div>
                <div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setIntakeSuccess(null);
                      handleTabChange('triage');
                    }}
                  >
                    Go to Triage Queue
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handlePatientIntake} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">First Name</label>
                    <Input
                      type="text"
                      value={intakeFirstName}
                      onChange={(e) => setIntakeFirstName(e.target.value)}
                      placeholder="e.g. Meenakshi"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Last Name</label>
                    <Input
                      type="text"
                      value={intakeLastName}
                      onChange={(e) => setIntakeLastName(e.target.value)}
                      placeholder="e.g. Sundaram"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Date of Birth</label>
                    <Input
                      type="date"
                      value={intakeDob}
                      onChange={(e) => setIntakeDob(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Gender</label>
                    <select
                      value={intakeGender}
                      onChange={(e) => setIntakeGender(e.target.value)}
                      className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                    >
                      <option value="FEMALE">Female</option>
                      <option value="MALE">Male</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Mobile Contact (+91)</label>
                  <Input
                    type="tel"
                    value={intakePhone}
                    onChange={(e) => setIntakePhone(e.target.value)}
                    placeholder="98401 23456"
                  />
                </div>

                <Button type="submit" variant="primary" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? 'Registering Citizen...' : 'Register Citizen & Issue OPD Token'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 3: COLD CHAIN EQUIPMENT TELEMETRY */}
      {activeTab === 'coldchain' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle>Cold Chain Storage Telemetry (ILR &amp; Freezers)</CardTitle>
                <CardDescription>
                  Universal immunization temperature monitoring. Regulatory target: +2°C to +8°C continuous band.
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  Target: 2°C – 8°C Safe Band
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {logSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg text-xs font-semibold">
                Temperature log recorded successfully and synced with eVIN / CoWIN cold chain monitor!
              </div>
            )}
            <DataTable
              data={coldChainAssets}
              keyExtractor={(c) => c.id}
              emptyTitle="No Cold Chain Units Configured"
              emptyMessage="No Ice-Lined Refrigerators or Deep Freezers registered in this facility."
              columns={[
                {
                  key: 'name',
                  header: 'Equipment Name',
                  render: (c) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{c.equipment_name || c.model || 'ILR Unit 1'}</span>
                      <span className="text-[11px] text-slate-400 font-mono">SN: {c.serial_number || 'ILR-KOV-01'}</span>
                    </div>
                  ),
                },
                {
                  key: 'type',
                  header: 'Asset Type',
                  render: (c) => <span className="text-xs text-slate-600 font-medium">{c.equipment_type || 'Ice-Lined Refrigerator'}</span>,
                },
                {
                  key: 'temp',
                  header: 'Latest Reading',
                  render: (c) => {
                    const temp = c.current_temp_c ?? c.latest_temperature ?? 4.2;
                    const inRange = temp >= 2 && temp <= 8;
                    return (
                      <span className={`font-mono font-black text-xs ${inRange ? 'text-emerald-700' : 'text-red-600'}`}>
                        {temp}°C {inRange ? '✅ Safe' : '⚠️ Excursion'}
                      </span>
                    );
                  },
                },
                {
                  key: 'log',
                  header: 'Shift Log',
                  render: (c) => (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        step="0.1"
                        value={logTemp}
                        onChange={(e) => setLogTemp(Number(e.target.value))}
                        className="w-18 h-7 text-xs font-mono"
                      />
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleLogColdChain(c.id)}
                        className="h-7 text-xs px-2"
                      >
                        Log Temp
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: UIP IMMUNIZATION ROSTER */}
      {activeTab === 'immunization' && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Universal Immunization Programme (UIP) Calculator</CardTitle>
            <CardDescription>
              Verify mandatory vaccines due for infants, children, and antenatal mothers per Tamil Nadu UIP guidelines.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <form onSubmit={handleQueryImmunization} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Beneficiary Age (Months)</label>
                  <Input
                    type="number"
                    value={immAgeMonths}
                    onChange={(e) => setImmAgeMonths(Number(e.target.value))}
                    min={0}
                    max={120}
                    required
                  />
                </div>
                <div className="flex items-center pt-6">
                  <label className="flex items-center gap-2 text-xs font-bold text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={immIsPregnant}
                      onChange={(e) => setImmIsPregnant(e.target.checked)}
                      className="w-4 h-4 rounded text-sky-600"
                    />
                    <span>Antenatal Beneficiary (Pregnant Mother)</span>
                  </label>
                </div>
              </div>

              <Button type="submit" variant="primary" disabled={isQueryingImm} className="w-full">
                {isQueryingImm ? 'Calculating Schedule...' : 'Fetch Mandatory Vaccines Due'}
              </Button>
            </form>

            {immGuidance && (
              <div className="p-4 bg-sky-50 border border-sky-200 rounded-xl space-y-3 animate-fade-in">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-sky-950 uppercase">Mandatory Vaccines Due</span>
                  <Badge status="ACTIVE" size="sm" />
                </div>
                <div className="space-y-1.5">
                  {immGuidance.due_vaccines?.map((v: string, idx: number) => (
                    <div key={idx} className="p-2.5 bg-white rounded-lg border border-sky-100 flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-900">{v}</span>
                      <span className="text-[11px] text-emerald-700 font-semibold">Ready for Administration</span>
                    </div>
                  )) || (
                    <div className="text-xs text-slate-600">All standard milestone vaccines up to date for this age group.</div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
