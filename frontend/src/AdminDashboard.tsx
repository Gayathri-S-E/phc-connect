import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';

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

export default function AdminDashboard({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState('attendance');
  const [attendanceRecords, setAttendanceRecords] = useState<any[]>([]);

  useEffect(() => {
    fetchAttendance();
  }, [user]);

  const fetchAttendance = async () => {
    if (!user?.facility_id) return;
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetchWithAuth(`/facility-admin/staff-attendance?facility_id=${user.facility_id}&from_date=${today}&to_date=${today}`);
      if (response.ok) {
        const data = await response.json();
        setAttendanceRecords(data.data || []);
      }
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
            <span style={{ color: 'white', fontWeight: 'bold', fontSize: '1.25rem' }}>⚙️</span>
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>PHC Connect</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary-color)' }}>Facility Admin</span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          {[
            { id: 'attendance', label: 'Staff Attendance', icon: Activity },
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
              <span style={{ fontSize: '1.2rem' }}>{user?.full_name?.charAt(0) || 'A'}</span>
            </div>
            <div>
              <p style={{ fontWeight: 500, fontSize: '0.875rem' }}>{user?.full_name || 'Admin'}</p>
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
        </header>

        <div className="page-content">
          {activeTab === 'attendance' && (
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Today's Staff Attendance</h3>
              {attendanceRecords.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No attendance records found for today.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {attendanceRecords.map(item => (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
                      <div>
                        <h4 style={{ fontWeight: 'bold' }}>{item.user_name || item.user_id}</h4>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                          Check-in: {item.check_in_time ? new Date(item.check_in_time).toLocaleTimeString() : 'N/A'} | 
                          Check-out: {item.check_out_time ? new Date(item.check_out_time).toLocaleTimeString() : 'N/A'}
                        </p>
                      </div>
                      <span style={{ padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 'bold', background: item.check_in_time && !item.check_out_time ? '#dcfce7' : '#fee2e2', color: item.check_in_time && !item.check_out_time ? '#166534' : '#dc2626' }}>
                        {item.check_in_time && !item.check_out_time ? 'On Duty' : 'Off Duty'}
                      </span>
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
