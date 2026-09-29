import { useState, useEffect } from 'react';
import { Home, Users } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const getToken = () => localStorage.getItem('access_token');
const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };
  return fetch(`${API_BASE}${url}`, { ...options, headers });
};

export default function NurseDashboard({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState('queue');
  const [queue, setQueue] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<any>(null);

  useEffect(() => {
    fetchQueue();
    fetchAttendance();
  }, []);

  const fetchQueue = async () => {
    try {
      const response = await fetchWithAuth('/nurse/triage/queue');
      if (response.ok) {
        const data = await response.json();
        setQueue(data.data || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAttendance = async () => {
    try {
      const response = await fetchWithAuth('/nurse/attendance/today');
      if (response.ok) {
        const data = await response.json();
        setAttendance(data.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const checkIn = async () => {
    try {
      await fetchWithAuth('/nurse/attendance/check-in', { method: 'POST' });
      fetchAttendance();
    } catch (e) {
      console.error(e);
    }
  };

  const checkOut = async () => {
    try {
      await fetchWithAuth('/nurse/attendance/check-out', { method: 'POST' });
      fetchAttendance();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-color)', color: 'var(--text-color)' }}>
      {/* Sidebar */}
      <aside className="glass-panel" style={{ width: '250px', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'white', fontWeight: 'bold', fontSize: '1.25rem' }}>👩‍⚕️</span>
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>PHC Connect</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary-color)' }}>Nurse Portal</span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          {[
            { id: 'home', label: 'Overview', icon: Home },
            { id: 'queue', label: 'Triage Queue', icon: Users },
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={activeTab === item.id ? 'active' : ''}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem 1rem',
                borderRadius: '0.5rem', width: '100%', textAlign: 'left',
                background: activeTab === item.id ? 'var(--primary-light)' : 'transparent',
                color: activeTab === item.id ? 'var(--primary-color)' : 'var(--text-color)',
                border: 'none', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              <item.icon size={20} />
              <span style={{ fontWeight: 500 }}>{item.label}</span>
            </button>
          ))}
        </nav>
        
        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--bg-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: '1.2rem' }}>{user?.full_name?.charAt(0) || 'N'}</span>
            </div>
            <div>
              <p style={{ fontWeight: 500, fontSize: '0.875rem' }}>Nurse {user?.full_name || 'User'}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {attendance?.check_in_time && !attendance?.check_out_time ? '🟢 On Duty' : '🔴 Off Duty'}
              </p>
            </div>
          </div>
          <button 
            onClick={() => { localStorage.removeItem('access_token'); window.location.reload(); }}
            style={{ marginTop: '1rem', width: '100%', padding: '0.5rem', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '0.5rem', cursor: 'pointer', color: 'var(--text-muted)' }}
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 'bold', textTransform: 'capitalize' }}>
            {activeTab.replace('-', ' ')}
          </h2>
          <div style={{ display: 'flex', gap: '1rem' }}>
            {!attendance?.check_in_time ? (
              <button className="btn-primary" onClick={checkIn}>Check In (Duty Start)</button>
            ) : !attendance?.check_out_time ? (
              <button className="btn-secondary" onClick={checkOut}>Check Out (Duty End)</button>
            ) : (
              <span style={{ padding: '0.5rem 1rem', background: '#dcfce7', color: '#166534', borderRadius: '0.5rem', fontWeight: 500 }}>Duty Completed</span>
            )}
          </div>
        </header>

        <div className="page-content">
          {activeTab === 'home' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#e0e7ff', color: '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Users size={24} /></div>
                <div><h3 style={{ fontSize: '2rem', fontWeight: 'bold' }}>{queue.length}</h3><p style={{ color: 'var(--text-muted)' }}>Patients in Triage Queue</p></div>
              </div>
            </div>
          )}
          
          {activeTab === 'queue' && (
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Triage Queue</h3>
              {queue.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No patients in triage queue.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {queue.map(item => (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ background: 'var(--primary-color)', color: 'white', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 'bold' }}>Token #{item.token_number}</span>
                        </div>
                        <h4 style={{ fontWeight: 'bold', marginTop: '0.5rem' }}>{item.patient_name}</h4>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Reason: {item.appointment_reason || 'N/A'}</p>
                      </div>
                      <button className="btn-primary" style={{ padding: '0.5rem 1rem' }}>Start Triage</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
