import { useState, useEffect } from 'react';
import { ClipboardList } from 'lucide-react';

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

export default function PharmacistDashboard({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState('prescriptions');
  const [prescriptions, setPrescriptions] = useState<any[]>([]);

  useEffect(() => {
    fetchPrescriptions();
  }, [user]);

  const fetchPrescriptions = async () => {
    if (!user?.facility_id) return;
    try {
      const response = await fetchWithAuth(`/pharmacist/prescriptions/pending?facility_id=${user.facility_id}`);
      if (response.ok) {
        const data = await response.json();
        setPrescriptions(data.data || []);
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
            <span style={{ color: 'white', fontWeight: 'bold', fontSize: '1.25rem' }}>💊</span>
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>PHC Connect</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--primary-color)' }}>Pharmacy</span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          {[
            { id: 'prescriptions', label: 'Pending Prescriptions', icon: ClipboardList },
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
              <span style={{ fontSize: '1.2rem' }}>{user?.full_name?.charAt(0) || 'P'}</span>
            </div>
            <div>
              <p style={{ fontWeight: 500, fontSize: '0.875rem' }}>{user?.full_name || 'Pharmacist'}</p>
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
          {activeTab === 'prescriptions' && (
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Pending Prescriptions</h3>
              {prescriptions.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No pending prescriptions.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {prescriptions.map(item => (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: '0.5rem' }}>
                      <div>
                        <h4 style={{ fontWeight: 'bold' }}>{item.patient_name}</h4>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Dr. {item.doctor_name}</p>
                      </div>
                      <button className="btn-primary" style={{ padding: '0.5rem 1rem' }}>Dispense</button>
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
