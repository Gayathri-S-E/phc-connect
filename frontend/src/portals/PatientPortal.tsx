import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Calendar, FileText, Pill, MessageSquare, Star, 
  Clock, Plus, CheckCircle, AlertTriangle, ShieldCheck, 
  MapPin, Heart, ChevronRight, X, Bot, Sparkles, User,
  Activity, Shield, Stethoscope, Award
} from 'lucide-react';
import { api } from '../services/api';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';
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

export default function PatientPortal() {
  const { t, language } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'appointments' | 'records' | 'prescriptions' | 'feedback' | 'awareness' | 'assistant' => {
    if (path.includes('/records')) return 'records';
    if (path.includes('/prescriptions')) return 'prescriptions';
    if (path.includes('/feedback')) return 'feedback';
    if (path.includes('/awareness')) return 'awareness';
    if (path.includes('/assistant')) return 'assistant';
    return 'appointments';
  };

  const [activeTab, setActiveTab] = useState<'appointments' | 'records' | 'prescriptions' | 'feedback' | 'awareness' | 'assistant'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'appointments' | 'records' | 'prescriptions' | 'feedback' | 'awareness' | 'assistant') => {
    setActiveTab(tab);
    if (tab === 'appointments') {
      navigate('/patient/appointments');
    } else {
      navigate(`/patient/${tab}`);
    }
  };

  const [profile, setProfile] = useState<any>(null);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [records, setRecords] = useState<any>(null);
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [awareness, setAwareness] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Booking Modal State
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [bookDate, setBookDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  });
  const [bookSlot, setBookSlot] = useState('09:30:00');
  const [bookReason, setBookReason] = useState('Routine Checkup');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState<any>(null);

  // Feedback State
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackCategory, setFeedbackCategory] = useState('CARE_QUALITY');
  const [feedbackComments, setFeedbackComments] = useState('');
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [profileRes, apptsRes, recordsRes, presRes, awareRes] = await Promise.all([
        api.get<any>('/patients/me'),
        api.get<any[]>('/patients/me/appointments'),
        api.get<any>('/patients/me/records'),
        api.get<any[]>('/patients/me/prescriptions'),
        api.get<any[]>('/patients/awareness-slides'),
      ]);

      if (profileRes.data) setProfile(profileRes.data);
      if (apptsRes.data) setAppointments(apptsRes.data);
      if (recordsRes.data) setRecords(recordsRes.data);
      if (presRes.data) setPrescriptions(presRes.data);
      if (awareRes.data) setAwareness(awareRes.data);

      if (!profileRes.data && profileRes.error) {
        setError(profileRes.error.detail);
      }
    } catch {
      setError('Failed to fetch patient portal data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleBookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile?.primary_facility_id || !profile?.id) {
      alert('Patient profile or primary facility information is missing.');
      return;
    }

    setIsSubmitting(true);
    try {
      const slot = bookSlot.length === 5 ? `${bookSlot}:00` : bookSlot;
      const isoDate = `${bookDate}T${slot}`;

      const payload = {
        patient_id: profile.id,
        facility_id: profile.primary_facility_id,
        appointment_date: isoDate,
        time_slot: slot,
        reason: bookReason,
        priority: 'ROUTINE',
      };

      const res = await api.post<any>('/patients/me/appointments', payload);
      if (res.data) {
        setBookingSuccess(res.data);
        fetchData();
      } else {
        alert(res.error?.detail || 'Failed to book appointment.');
      }
    } catch (err: any) {
      alert(err?.detail || 'An error occurred while booking.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelAppointment = async (id: string) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    const res = await api.patch(`/patients/me/appointments/${id}/cancel?cancellation_reason=Cancelled+by+citizen`);
    if (res.data) {
      fetchData();
    } else {
      alert(res.error?.detail || 'Failed to cancel appointment.');
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackComments.trim()) return;

    setIsSubmitting(true);
    try {
      const res = await api.post('/patients/me/feedback', {
        facility_id: profile?.primary_facility_id,
        category: feedbackCategory,
        rating: feedbackRating,
        comments: feedbackComments,
      });

      if (res.data) {
        setFeedbackSuccess(true);
        setFeedbackComments('');
      } else {
        alert(res.error?.detail || 'Failed to submit feedback.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading your personal health portal..." />;
  }

  if (error && !profile) {
    return <StateView state="error" message={error} onRetry={fetchData} />;
  }

  const upcomingAppts = appointments.filter((a) => a.status === 'SCHEDULED');
  const activePrescriptions = prescriptions.filter((p) => p.status === 'ACTIVE' || p.status === 'PENDING_DISPENSING');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Page Header with Live Citizen Health Metrics */}
      <PageHeader
        breadcrumbs={[
          { label: 'Citizen Services' },
          { label: profile ? `${profile.first_name} ${profile.last_name || ''}` : 'My Health Portal' },
        ]}
        facilityContext={profile?.facility_name || 'Primary Health Centre Kovalam'}
        title={profile ? `Welcome, ${profile.first_name}` : 'Citizen Health Portal'}
        description={`Registered UHID: ${profile?.patient_identifier || 'DEMO-PAT-0001'} • Primary care health records and electronic visits synchronized with Government of Tamil Nadu Health Mission.`}
        actions={
          <Button
            variant="primary"
            onClick={() => {
              setBookingSuccess(null);
              setIsBookModalOpen(true);
            }}
            className="gap-2 shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>{t('health.bookAppointment') || 'Book Appointment'}</span>
          </Button>
        }
        metrics={[
          {
            label: 'Upcoming Visits',
            value: upcomingAppts.length,
            hint: upcomingAppts[0] ? `Next: ${upcomingAppts[0].appointment_date}` : 'No queue tokens today',
            variant: upcomingAppts.length > 0 ? 'sky' : 'default',
            icon: <Calendar className="w-4 h-4" />,
          },
          {
            label: 'Active Prescriptions',
            value: prescriptions.length,
            hint: `${activePrescriptions.length} pending pickup`,
            variant: activePrescriptions.length > 0 ? 'success' : 'default',
            icon: <Pill className="w-4 h-4" />,
          },
          {
            label: 'Latest SpO2',
            value: records?.vitals?.[0]?.spo2 ? `${records.vitals[0].spo2}%` : 'Normal',
            hint: records?.vitals?.[0] ? `BP ${records.vitals[0].systolic_bp}/${records.vitals[0].diastolic_bp}` : 'Vitals logged',
            variant: 'default',
            icon: <Activity className="w-4 h-4" />,
          },
          {
            label: 'ABHA Linkage',
            value: 'Verified',
            hint: 'National Health ID active',
            variant: 'success',
            icon: <ShieldCheck className="w-4 h-4" />,
          },
        ]}
      />

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200/80 rounded-xl overflow-x-auto no-scrollbar max-w-full">
        {[
          { key: 'appointments', label: t('health.appointments') || 'Appointments', icon: <Calendar className="w-4 h-4" /> },
          { key: 'records', label: 'Clinical Records', icon: <FileText className="w-4 h-4" /> },
          { key: 'prescriptions', label: t('health.prescription') || 'Prescriptions', icon: <Pill className="w-4 h-4" /> },
          { key: 'feedback', label: 'Care Feedback', icon: <Star className="w-4 h-4" /> },
          { key: 'awareness', label: 'Health Bulletins', icon: <Heart className="w-4 h-4" /> },
          { key: 'assistant', label: 'AI Wellness Guide', icon: <Bot className="w-4 h-4" /> },
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

      {/* TAB CONTENT: APPOINTMENTS */}
      {activeTab === 'appointments' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle>Upcoming &amp; Past Visits</CardTitle>
                <CardDescription>
                  Review appointment tokens, assigned medical officers, and queue statuses.
                </CardDescription>
              </div>
              <span className="text-xs text-slate-500 font-medium">
                {appointments.length} total visit records
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <DataTable
              data={appointments}
              keyExtractor={(a) => a.id}
              searchFilter={(a, q) =>
                a.slot_time.toLowerCase().includes(q) ||
                (a.status || '').toLowerCase().includes(q) ||
                (a.reason_for_visit || '').toLowerCase().includes(q)
              }
              emptyTitle="No Appointments Scheduled"
              emptyMessage="You have no appointments booked yet. Click 'Book Appointment' to schedule a doctor visit."
              columns={[
                {
                  key: 'token',
                  header: 'OPD Token',
                  render: (a) => (
                    <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-sky-50 text-sky-800 font-mono font-bold text-xs border border-sky-200/80">
                      #{a.token_number}
                    </span>
                  ),
                },
                { key: 'appointment_date', header: 'Date', render: (a) => a.appointment_date },
                { key: 'slot_time', header: 'Slot Time', render: (a) => a.slot_time },
                {
                  key: 'reason',
                  header: 'Reason for Visit',
                  render: (a) => (
                    <span className="font-medium text-slate-800">
                      {a.reason_for_visit || 'General Consultation'}
                    </span>
                  ),
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (a) => <Badge status={a.status} size="sm" />,
                },
                {
                  key: 'actions',
                  header: 'Actions',
                  render: (a) =>
                    a.status === 'SCHEDULED' ? (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleCancelAppointment(a.id)}
                        className="h-7 text-xs px-2.5"
                      >
                        Cancel
                      </Button>
                    ) : (
                      <span className="text-xs text-slate-400">—</span>
                    ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: CLINICAL RECORDS */}
      {activeTab === 'records' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Latest Vitals Card */}
          <Card className="lg:col-span-1 h-fit">
            <CardHeader>
              <CardTitle className="text-sm">Latest Triage Vitals</CardTitle>
              <CardDescription>Recorded by triage nurse during OPD check-in</CardDescription>
            </CardHeader>
            <CardContent>
              {records?.vitals && records.vitals.length > 0 ? (
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase">Blood Pressure</span>
                    <div className="text-base font-extrabold text-slate-900">
                      {records.vitals[0].systolic_bp}/{records.vitals[0].diastolic_bp}{' '}
                      <span className="text-[10px] text-slate-400 font-normal">mmHg</span>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase">Heart Rate</span>
                    <div className="text-base font-extrabold text-slate-900">
                      {records.vitals[0].heart_rate}{' '}
                      <span className="text-[10px] text-slate-400 font-normal">bpm</span>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase">SpO2 Oxygen</span>
                    <div className={`text-base font-extrabold ${records.vitals[0].spo2 < 95 ? 'text-red-600' : 'text-emerald-700'}`}>
                      {records.vitals[0].spo2}%
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                    <span className="text-[11px] font-bold text-slate-500 uppercase">Temperature</span>
                    <div className="text-base font-extrabold text-slate-900">
                      {records.vitals[0].temperature}°F
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-400 text-center py-6">
                  No vitals logged yet.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Past Consultations */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-sm">Doctor Consultation Encounters</CardTitle>
              <CardDescription>Clinical diagnoses, physician observations, and treatment plans</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!records?.consultations || records.consultations.length === 0 ? (
                <StateView state="empty" title="No Past Encounters" message="You have no recorded clinical visits on file." />
              ) : (
                records.consultations.map((c: any) => (
                  <div key={c.id} className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition shadow-2xs space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">
                          {c.chief_complaints || 'Clinical OPD Consultation'}
                        </h4>
                        <span className="text-xs text-slate-400">
                          Encounter Date: {new Date(c.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <Badge status={c.status} size="sm" />
                    </div>

                    {c.examination_notes && (
                      <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        <strong className="text-slate-900">Physician Notes:</strong> {c.examination_notes}
                      </p>
                    )}

                    {c.diagnosis_codes?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {c.diagnosis_codes.map((diag: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[11px] font-semibold"
                          >
                            ICD-10: {diag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB CONTENT: PRESCRIPTIONS */}
      {activeTab === 'prescriptions' && (
        <Card>
          <CardHeader>
            <CardTitle>Digital Prescriptions</CardTitle>
            <CardDescription>
              Electronic medicine orders issued by medical officers, linked to facility dispensary inventory.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={prescriptions}
              keyExtractor={(p) => p.id}
              emptyTitle="No Prescriptions Issued"
              emptyMessage="You currently have no active or historical prescriptions on record."
              columns={[
                {
                  key: 'id',
                  header: 'Prescription ID',
                  render: (p) => <span className="font-mono text-xs text-slate-600">Rx-{p.id.slice(0, 8)}</span>,
                },
                {
                  key: 'date',
                  header: 'Issued Date',
                  render: (p) => (p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Today'),
                },
                {
                  key: 'doctor',
                  header: 'Prescribing Officer',
                  render: (p) => (
                    <span className="font-semibold text-slate-800">
                      {p.doctor_name || 'Dr. Ramesh (Medical Officer)'}
                    </span>
                  ),
                },
                {
                  key: 'medications',
                  header: 'Medications',
                  render: (p) => (
                    <div className="flex flex-wrap gap-1 max-w-sm">
                      {p.items?.map((it: any, idx: number) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-100 text-[11px] font-medium"
                        >
                          {it.medication_name} ({it.dosage})
                        </span>
                      )) || <span className="text-xs text-slate-500">Standard formulary pack</span>}
                    </div>
                  ),
                },
                {
                  key: 'status',
                  header: 'Dispense Status',
                  render: (p) => <Badge status={p.status} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: FEEDBACK */}
      {activeTab === 'feedback' && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Facility Care &amp; Service Feedback</CardTitle>
            <CardDescription>
              Help us improve public health services at {profile?.facility_name || 'your local PHC'}. Your comments are reviewed by the District Health Officer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {feedbackSuccess ? (
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
                <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto" />
                <h4 className="text-base font-bold text-emerald-950">Thank you for your feedback!</h4>
                <p className="text-xs text-emerald-800">
                  Your grievance / suggestion has been logged with the District Family Welfare Office.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFeedbackSuccess(false)}
                  className="mt-3"
                >
                  Submit Another Note
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmitFeedback} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Rating (1 to 5 Stars)
                  </label>
                  <div className="flex items-center gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setFeedbackRating(star)}
                        className={`p-2 rounded-lg border transition ${
                          feedbackRating >= star
                            ? 'bg-amber-50 border-amber-300 text-amber-500'
                            : 'bg-slate-50 border-slate-200 text-slate-300'
                        }`}
                      >
                        <Star className="w-5 h-5 fill-current" />
                      </button>
                    ))}
                    <span className="text-xs font-bold text-slate-700 ml-2">
                      {feedbackRating} of 5 Stars
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Feedback Category
                  </label>
                  <select
                    value={feedbackCategory}
                    onChange={(e) => setFeedbackCategory(e.target.value)}
                    className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                  >
                    <option value="CARE_QUALITY">Doctor &amp; Nursing Care Quality</option>
                    <option value="WAIT_TIME">Wait Time &amp; OPD Queue</option>
                    <option value="MEDICINE_AVAILABILITY">Medicine Availability in Dispensary</option>
                    <option value="FACILITY_CLEANLINESS">Cleanliness &amp; Infrastructure</option>
                    <option value="STAFF_COURTESY">Staff Courtesy &amp; Helpfulness</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Your Comments
                  </label>
                  <Textarea
                    value={feedbackComments}
                    onChange={(e) => setFeedbackComments(e.target.value)}
                    placeholder="Describe your experience during this visit..."
                    rows={4}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting || !feedbackComments.trim()}
                  className="w-full"
                >
                  {isSubmitting ? 'Submitting Feedback...' : 'Submit Citizen Feedback'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB CONTENT: AWARENESS BULLETINS */}
      {activeTab === 'awareness' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900">Tamil Nadu Public Health Bulletins</h3>
              <p className="text-xs text-slate-500">Preventive education, epidemic awareness, and maternal care guidance.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {awareness.length > 0 ? (
              awareness.map((slide, idx) => (
                <Card key={idx} className="flex flex-col justify-between overflow-hidden">
                  <CardHeader className="bg-sky-50/50 pb-3">
                    <div className="flex items-center gap-2 text-sky-700 text-[10px] font-extrabold uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{slide.category || 'Public Health Alert'}</span>
                    </div>
                    <CardTitle className="text-sm mt-1">{slide.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-3">
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {slide.description || slide.content}
                    </p>
                  </CardContent>
                </Card>
              ))
            ) : (
              [
                {
                  title: 'Dengue & Vector-Borne Prevention',
                  category: 'Epidemic Guidance',
                  content: 'Eliminate stagnant water around homes. Utilize mosquito nets and report high fever lasting more than 48 hours to the nearest PHC immediately.',
                },
                {
                  title: 'Universal Child Immunization (UIP)',
                  category: 'Maternal & Child Health',
                  content: 'Ensure timely administration of Pentavalent, OPV, and MR vaccines. Visit every Wednesday during Village Health and Nutrition Days (VHND).',
                },
                {
                  title: 'Makkalai Thedi Maruthuvam (Healthcare at Doorstep)',
                  category: 'State Health Scheme',
                  content: 'Free home delivery of hypertension and diabetes medications for elderly and non-ambulatory citizens across Tamil Nadu.',
                },
              ].map((slide, i) => (
                <Card key={i} className="flex flex-col justify-between">
                  <CardHeader className="bg-sky-50/50 pb-3">
                    <div className="flex items-center gap-2 text-sky-700 text-[10px] font-extrabold uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{slide.category}</span>
                    </div>
                    <CardTitle className="text-sm mt-1">{slide.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-3">
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {slide.content}
                    </p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: AI ASSISTANT INFO */}
      {activeTab === 'assistant' && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <CardTitle>AI Citizen Health Assistant</CardTitle>
                <CardDescription>Multilingual voice &amp; text clinical guide</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs text-slate-600 leading-relaxed">
              Your Citizen Health Assistant can clarify medical prescriptions, explain diagnosis terms in Tamil or Hindi, find operating hours of nearby PHCs, and assist with booking appointment slots.
            </p>
            <div className="p-3 bg-sky-50 border border-sky-100 rounded-xl text-xs text-sky-950 font-medium flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-600 shrink-0" />
              <span>Click the floating button in the bottom right corner anytime to speak or chat with the assistant.</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Booking Dialog Modal */}
      <Dialog open={isBookModalOpen} onOpenChange={setIsBookModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Book OPD Doctor Appointment</DialogTitle>
          <DialogClose onClose={() => setIsBookModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          {bookingSuccess ? (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
              <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto" />
              <h4 className="text-base font-bold text-emerald-950">Appointment Confirmed!</h4>
              <div className="p-2.5 bg-white rounded-lg border border-emerald-200 text-xs font-mono font-bold text-emerald-900">
                Token #{bookingSuccess.token_number} • {bookingSuccess.slot_time}
              </div>
              <p className="text-xs text-emerald-800">
                Please arrive at {profile?.facility_name || 'the PHC'} 15 minutes before your time slot.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setIsBookModalOpen(false);
                  setBookingSuccess(null);
                }}
                className="mt-3 w-full"
              >
                Done
              </Button>
            </div>
          ) : (
            <form onSubmit={handleBookAppointment} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Primary Health Facility
                </label>
                <div className="p-2.5 rounded-lg bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-800 flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5 text-sky-600" />
                  <span>{profile?.facility_name || 'Primary Health Centre Kovalam'}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Appointment Date
                </label>
                <Input
                  type="date"
                  value={bookDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setBookDate(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Preferred Time Slot
                </label>
                <select
                  value={bookSlot}
                  onChange={(e) => setBookSlot(e.target.value)}
                  className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                >
                  <option value="09:00:00">09:00 AM – 09:30 AM (Morning OPD)</option>
                  <option value="09:30:00">09:30 AM – 10:00 AM (Morning OPD)</option>
                  <option value="10:00:00">10:00 AM – 10:30 AM (Morning OPD)</option>
                  <option value="10:30:00">10:30 AM – 11:00 AM (Morning OPD)</option>
                  <option value="11:30:00">11:30 AM – 12:00 PM (Mid-day OPD)</option>
                  <option value="14:30:00">02:30 PM – 03:00 PM (Afternoon OPD)</option>
                  <option value="15:30:00">03:30 PM – 04:00 PM (Afternoon OPD)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Reason for Visit
                </label>
                <Input
                  type="text"
                  value={bookReason}
                  onChange={(e) => setBookReason(e.target.value)}
                  placeholder="e.g. Fever, routine BP check, cough..."
                  required
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsBookModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Confirming Token...' : 'Confirm Appointment'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
