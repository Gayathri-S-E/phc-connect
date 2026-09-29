import React, { useState, useEffect } from 'react';
import { 
  Calendar, FileText, Pill, MessageSquare, Star, 
  Clock, Plus, CheckCircle, AlertTriangle, ShieldCheck, 
  MapPin, Heart, ChevronRight, X 
} from 'lucide-react';
import { api } from '../services/api';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';
import { useLanguage } from '../context/LanguageContext';

export default function PatientPortal() {
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<'appointments' | 'records' | 'prescriptions' | 'feedback' | 'awareness'>('appointments');
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
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
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
    if (!profile?.primary_facility_id && !profile?.id) return;

    setIsSubmitting(true);
    try {
      const payload = {
        patient_id: profile.id,
        facility_id: profile.primary_facility_id,
        appointment_date: bookDate,
        slot_time: bookSlot,
        reason_for_visit: bookReason,
      };

      const res = await api.post<any>('/patients/me/appointments', payload);
      if (res.data) {
        setBookingSuccess(res.data);
        fetchData();
      } else {
        alert(res.error?.detail || 'Failed to book appointment.');
      }
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
    return <StateView state="loading" message="Loading your health portal..." />;
  }

  if (error && !profile) {
    return <StateView state="error" message={error} onRetry={fetchData} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Patient Welcome Hero Header */}
      <div
        className="glass-card"
        style={{
          padding: '1.5rem',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(59, 130, 246, 0.03) 100%)',
          border: '1px solid rgba(37, 99, 235, 0.15)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '1.35rem',
            }}
          >
            {profile?.first_name?.charAt(0) || 'P'}
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800 }}>
              {profile ? `${profile.first_name} ${profile.last_name || ''}` : 'Citizen Portal'}
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginTop: '0.25rem', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              <span>UHID: <strong>{profile?.patient_identifier || 'DEMO-PAT-0001'}</strong></span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <MapPin size={13} /> {profile?.facility_name || 'Primary Health Centre Kovalam'}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => {
            setBookingSuccess(null);
            setIsBookModalOpen(true);
          }}
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1.25rem' }}
        >
          <Plus size={18} />
          {t('health.bookAppointment')}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '0.25rem',
          overflowX: 'auto',
        }}
      >
        {[
          { key: 'appointments', label: t('health.appointments'), icon: <Calendar size={16} /> },
          { key: 'records', label: 'Clinical Records', icon: <FileText size={16} /> },
          { key: 'prescriptions', label: t('health.prescription'), icon: <Pill size={16} /> },
          { key: 'feedback', label: 'Feedback & Grievances', icon: <Star size={16} /> },
          { key: 'awareness', label: 'Health Bulletins', icon: <Heart size={16} /> },
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
              whiteSpace: 'nowrap',
            }}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB CONTENT: APPOINTMENTS */}
      {activeTab === 'appointments' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Upcoming & Past Visits</h3>
            <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              Showing {appointments.length} appointments
            </span>
          </div>

          <DataTable
            data={appointments}
            keyExtractor={(a) => a.id}
            searchFilter={(a, q) => a.slot_time.toLowerCase().includes(q) || (a.status || '').toLowerCase().includes(q)}
            emptyTitle="No Appointments Scheduled"
            emptyMessage="You have no upcoming appointments. Click 'Book Appointment' above to schedule a visit."
            columns={[
              {
                key: 'token',
                header: 'Token #',
                render: (a) => (
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(37, 99, 235, 0.1)',
                      color: 'var(--primary)',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                    }}
                  >
                    #{a.token_number}
                  </span>
                ),
              },
              { key: 'appointment_date', header: 'Date', render: (a) => a.appointment_date },
              { key: 'slot_time', header: 'Slot Time', render: (a) => a.slot_time },
              { key: 'reason', header: 'Reason for Visit', render: (a) => a.reason_for_visit || 'General Consultation' },
              { key: 'status', header: 'Status', render: (a) => <Badge status={a.status} /> },
              {
                key: 'actions',
                header: 'Action',
                render: (a) =>
                  a.status === 'SCHEDULED' ? (
                    <button
                      onClick={() => handleCancelAppointment(a.id)}
                      className="btn-secondary"
                      style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', color: '#dc2626' }}
                    >
                      Cancel
                    </button>
                  ) : null,
              },
            ]}
          />
        </div>
      )}

      {/* TAB CONTENT: CLINICAL RECORDS */}
      {activeTab === 'records' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Longitudinal Health Records</h3>
          
          {/* Vitals Summary Card */}
          {records?.vitals && records.vitals.length > 0 && (
            <div className="glass-card" style={{ padding: '1.25rem', borderRadius: '12px' }}>
              <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.95rem', fontWeight: 600, color: 'var(--primary)' }}>
                Latest Triage Vitals
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(241, 245, 249, 0.7)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Blood Pressure</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                    {records.vitals[0].systolic_bp}/{records.vitals[0].diastolic_bp} <span style={{ fontSize: '0.75rem' }}>mmHg</span>
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(241, 245, 249, 0.7)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Heart Rate</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                    {records.vitals[0].heart_rate} <span style={{ fontSize: '0.75rem' }}>bpm</span>
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(241, 245, 249, 0.7)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SpO2 Oxygen</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: records.vitals[0].spo2 < 95 ? '#dc2626' : 'var(--text-main)' }}>
                    {records.vitals[0].spo2}%
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'rgba(241, 245, 249, 0.7)', borderRadius: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Temperature</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                    {records.vitals[0].temperature}°F
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Past Consultations */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>Physician Consultations</h4>
            {records?.consultations?.length === 0 ? (
              <StateView state="empty" title="No Consultation History" message="You have no recorded clinical visits yet." />
            ) : (
              records?.consultations?.map((c: any) => (
                <div key={c.id} className="glass-card" style={{ padding: '1rem', borderRadius: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h5 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>
                        {c.chief_complaints || 'Clinical Consultation'}
                      </h5>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Date: {new Date(c.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <Badge status={c.status} />
                  </div>
                  {c.examination_notes && (
                    <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-main)' }}>
                      <strong>Doctor Notes:</strong> {c.examination_notes}
                    </p>
                  )}
                  {c.diagnosis_codes?.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                      {c.diagnosis_codes.map((diag: string, idx: number) => (
                        <span
                          key={idx}
                          style={{
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            backgroundColor: 'rgba(100, 116, 139, 0.1)',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        >
                          ICD-10: {diag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: PRESCRIPTIONS */}
      {activeTab === 'prescriptions' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Electronic Prescriptions</h3>
          <DataTable
            data={prescriptions}
            keyExtractor={(p) => p.id}
            emptyTitle="No Prescriptions on File"
            emptyMessage="No medications have been prescribed for your account."
            columns={[
              {
                key: 'date',
                header: 'Date',
                render: (p) => new Date(p.created_at).toLocaleDateString(),
              },
              {
                key: 'items',
                header: 'Medications',
                render: (p) => (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    {p.items?.map((item: any, i: number) => (
                      <div key={i} style={{ fontSize: '0.825rem' }}>
                        <strong>{item.medication_name || item.generic_name || 'Medicine'}</strong> — {item.dosage} ({item.frequency}) for {item.duration_days} days
                      </div>
                    ))}
                  </div>
                ),
              },
              { key: 'status', header: 'Fulfillment Status', render: (p) => <Badge status={p.status} /> },
            ]}
          />
        </div>
      )}

      {/* TAB CONTENT: FEEDBACK & GRIEVANCES */}
      {activeTab === 'feedback' && (
        <div className="glass-card" style={{ padding: '1.5rem', borderRadius: '14px', maxWidth: '600px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.15rem', fontWeight: 700 }}>Submit PHC Feedback or Grievance</h3>
          <p style={{ margin: '0 0 1.25rem 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Your feedback directly informs the PHC In-Charge and District Health Officer to improve local health services.
          </p>

          {feedbackSuccess ? (
            <div
              style={{
                padding: '1rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                color: '#059669',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <CheckCircle size={20} />
              <span>Thank you! Your feedback has been submitted to the PHC In-Charge.</span>
            </div>
          ) : (
            <form onSubmit={handleSubmitFeedback} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Satisfaction Rating (1 to 5 Stars)
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setFeedbackRating(star)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '0.25rem',
                        color: star <= feedbackRating ? '#eab308' : '#cbd5e1',
                      }}
                    >
                      <Star size={28} fill={star <= feedbackRating ? '#eab308' : 'none'} />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Category
                </label>
                <select
                  value={feedbackCategory}
                  onChange={(e) => setFeedbackCategory(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.875rem',
                  }}
                >
                  <option value="CARE_QUALITY">Quality of Doctor Care</option>
                  <option value="WAITING_TIME">OPD Waiting Time</option>
                  <option value="MEDICINE_AVAILABILITY">Pharmacy / Medicine Availability</option>
                  <option value="CLEANLINESS">Facility Cleanliness & Hygiene</option>
                  <option value="STAFF_BEHAVIOR">Staff Conduct</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Comments or Grievance Details
                </label>
                <textarea
                  rows={4}
                  value={feedbackComments}
                  onChange={(e) => setFeedbackComments(e.target.value)}
                  placeholder="Describe your visit experience or any issues encountered..."
                  required
                  style={{
                    width: '100%',
                    padding: '0.6rem',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.875rem',
                    outline: 'none',
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !feedbackComments.trim()}
                className="btn-primary"
                style={{ padding: '0.65rem 1rem' }}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </form>
          )}
        </div>
      )}

      {/* TAB CONTENT: AWARENESS BULLETINS */}
      {activeTab === 'awareness' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {awareness.length === 0 ? (
            <StateView state="empty" title="No Bulletins" message="Check back later for seasonal health advisories." />
          ) : (
            awareness.map((slide) => (
              <div
                key={slide.id}
                className="glass-card"
                style={{
                  padding: '1.25rem',
                  borderRadius: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.725rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--primary)',
                  }}
                >
                  {slide.category || 'PREVENTIVE HEALTH'}
                </span>
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>
                  {language === 'ta' && slide.title_ta ? slide.title_ta : slide.title}
                </h4>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  {language === 'ta' && slide.body_ta ? slide.body_ta : slide.body}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* BOOK APPOINTMENT MODAL */}
      <Modal
        isOpen={isBookModalOpen}
        onClose={() => setIsBookModalOpen(false)}
        title="Schedule Clinic Appointment"
      >
        {bookingSuccess ? (
          <div style={{ textAlign: 'center', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
            <div style={{ width: '60px', height: '60px', borderRadius: '50%', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle size={36} />
            </div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Appointment Confirmed!</h3>
            <div
              style={{
                padding: '1rem 1.5rem',
                borderRadius: '12px',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                border: '1px solid rgba(37, 99, 235, 0.2)',
                textAlign: 'center',
              }}
            >
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Your Assigned Token Number</span>
              <div style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--primary)', marginTop: '0.25rem' }}>
                #{bookingSuccess.token_number}
              </div>
              <div style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Date: <strong>{bookingSuccess.appointment_date}</strong> at <strong>{bookingSuccess.slot_time}</strong>
              </div>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
              Please arrive 15 minutes before your slot and present this token at the triage desk.
            </p>
            <button className="btn-primary" onClick={() => setIsBookModalOpen(false)}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleBookAppointment} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Appointment Date
              </label>
              <input
                type="date"
                value={bookDate}
                onChange={(e) => setBookDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Preferred Time Slot
              </label>
              <select
                value={bookSlot}
                onChange={(e) => setBookSlot(e.target.value)}
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              >
                <option value="09:00:00">09:00 AM - 09:30 AM</option>
                <option value="09:30:00">09:30 AM - 10:00 AM</option>
                <option value="10:00:00">10:00 AM - 10:30 AM</option>
                <option value="10:30:00">10:30 AM - 11:00 AM</option>
                <option value="11:00:00">11:00 AM - 11:30 AM</option>
                <option value="14:00:00">02:00 PM - 02:30 PM</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Reason for Visit
              </label>
              <input
                type="text"
                value={bookReason}
                onChange={(e) => setBookReason(e.target.value)}
                placeholder="e.g. Fever, cough, diabetes follow-up"
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
              <button type="button" className="btn-secondary" onClick={() => setIsBookModalOpen(false)}>
                Cancel
              </button>
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? 'Confirming...' : 'Confirm Booking'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
