import React, { useState, useEffect } from 'react';
import DoctorDashboard from './DoctorDashboard';
import NurseDashboard from './NurseDashboard';
import PharmacistDashboard from './PharmacistDashboard';
import AdminDashboard from './AdminDashboard';
import { 
  Home, User, Calendar, MessageSquare, Menu, 
  Loader, Send, FilePlus
} from 'lucide-react';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// --- AUTHENTICATION UTILS ---
const getToken = () => localStorage.getItem('access_token');
const setToken = (token: string) => localStorage.setItem('access_token', token);

const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };
  return fetch(`${API_BASE}${url}`, { ...options, headers });
};

// --- SUB-COMPONENTS ---

const AiAssistant = () => {
  const [messages, setMessages] = useState<any[]>([{ text: "Hello! I am your AI Wellness Assistant. How can I help you stay healthy today?", sender: "ai" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { text: input, sender: "user" }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    
    try {
      const res = await fetchWithAuth('/patients/wellness-assistant/chat', { 
        method: 'POST', 
        body: JSON.stringify({ message: input, language: 'en' }) 
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, { text: data.data.response_text || data.data.response, sender: "ai" }]);
      } else {
        setMessages(prev => [...prev, { text: "Sorry, I am having trouble connecting to the server.", sender: "ai" }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { text: "Error connecting to AI service.", sender: "ai" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
      <div className="card-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div className="card-title"><MessageSquare size={20} /> AI Wellness Assistant</div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 0', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ 
            alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
            background: msg.sender === 'user' ? 'var(--primary)' : 'rgba(37, 99, 235, 0.1)',
            color: msg.sender === 'user' ? 'white' : 'var(--text-main)',
            padding: '0.75rem 1rem',
            borderRadius: '1rem',
            borderBottomRightRadius: msg.sender === 'user' ? '0.25rem' : '1rem',
            borderBottomLeftRadius: msg.sender === 'ai' ? '0.25rem' : '1rem',
            maxWidth: '80%'
          }}>
            {msg.text}
          </div>
        ))}
        {loading && <div style={{ alignSelf: 'flex-start', padding: '0.75rem 1rem', borderRadius: '1rem', background: 'rgba(37, 99, 235, 0.1)' }}><Loader size={16} className="animate-spin" /></div>}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a health or wellness question..." 
          style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '2rem', border: '1px solid var(--border-color)', outline: 'none' }}
        />
        <button onClick={handleSend} className="btn-primary" style={{ borderRadius: '50%', padding: '0.75rem', width: '48px', height: '48px', display: 'flex', justifyContent: 'center' }}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

const Appointments = ({ user }: { user?: any }) => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [facilities, setFacilities] = useState<any[]>([]);
  const [newAppt, setNewAppt] = useState({
    facility_id: '',
    appointment_date: new Date().toISOString().slice(0, 16),
    reason: '',
    priority: 'ROUTINE'
  });

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const response = await fetchWithAuth('/patients/me/appointments');
      if (response.ok) {
        const data = await response.json();
        setAppointments(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch appointments", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFacilities = async () => {
    try {
      // The API base is handled by fetchWithAuth but the path is just /facilities
      const response = await fetchWithAuth('/facilities');
      if (response.ok) {
        const data = await response.json();
        setFacilities(data.data || []);
        if (data.data && data.data.length > 0) {
          setNewAppt(prev => ({ ...prev, facility_id: data.data[0].id }));
        }
      }
    } catch (error) {
      console.error("Failed to fetch facilities", error);
    }
  };

  useEffect(() => {
    fetchAppointments();
    fetchFacilities();
  }, []);

  const handleCancel = async (id: string) => {
    try {
      await fetchWithAuth(`/patients/me/appointments/${id}/cancel`, { method: 'PATCH' });
      fetchAppointments();
    } catch (error) {
      console.error(error);
    }
  };

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!newAppt.facility_id) {
        alert("No facility available to book. Please contact support.");
        return;
      }
      const payload = {
        patient_id: user?.id || "00000000-0000-0000-0000-000000000000",
        facility_id: newAppt.facility_id,
        appointment_date: new Date(newAppt.appointment_date).toISOString(),
        reason: newAppt.reason,
        priority: newAppt.priority
      };
      const response = await fetchWithAuth('/patients/me/appointments', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        setShowModal(false);
        setNewAppt({ facility_id: facilities[0]?.id || '', appointment_date: new Date().toISOString().slice(0, 16), reason: '', priority: 'ROUTINE' });
        fetchAppointments();
      } else {
        const errorText = await response.text();
        alert(`Failed to book appointment: ${errorText}`);
      }
    } catch (error) {
      console.error(error);
      alert(`Failed to book appointment: ${(error as any).message}`);
    }
  };

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600' }}>My Appointments</h2>
        <button className="btn-primary" onClick={() => setShowModal(true)}><FilePlus size={18} /> Book New Appointment</button>
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}><Loader className="animate-spin" size={24} style={{ margin: '0 auto' }}/></div>
      ) : appointments.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <p>No appointments found.</p>
        </div>
      ) : (
        appointments.map((apt: any) => (
          <div key={apt.id} className="glass-card" style={{ marginBottom: '1.5rem' }}>
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ background: apt.status === 'CANCELLED' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', color: apt.status === 'CANCELLED' ? 'red' : 'var(--secondary)', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.75rem', fontWeight: '600' }}>{apt.status}</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Token #{apt.token_number || apt.id.substring(0,6)}</span>
                  </div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.25rem' }}>{apt.appointment_type || 'General Checkup'}</h3>
                  <p style={{ color: 'var(--text-muted)' }}><Calendar size={14} style={{ display: 'inline', marginRight: '4px' }}/> {new Date(apt.appointment_date).toLocaleString()}</p>
                </div>
                {apt.status !== 'CANCELLED' && (
                  <button className="btn-secondary" onClick={() => handleCancel(apt.id)}>Cancel</button>
                )}
             </div>
          </div>
        ))
      )}

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="glass-card" style={{ width: '400px', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>Book New Appointment</h3>
            <form onSubmit={handleBook} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Facility</label>
                <select value={newAppt.facility_id} onChange={e => setNewAppt({...newAppt, facility_id: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }} required>
                  {facilities.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Date & Time</label>
                <input type="datetime-local" value={newAppt.appointment_date} onChange={e => setNewAppt({...newAppt, appointment_date: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }} required />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Reason</label>
                <input type="text" value={newAppt.reason} onChange={e => setNewAppt({...newAppt, reason: e.target.value})} placeholder="e.g., Fever and cough" style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }} required minLength={2} />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Priority</label>
                <select value={newAppt.priority} onChange={e => setNewAppt({...newAppt, priority: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }}>
                  <option value="ROUTINE">Routine</option>
                  <option value="URGENT">Urgent</option>
                  <option value="EMERGENCY">Emergency</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary" style={{ flex: 1 }}>Cancel</button>
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Book</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const Profile = ({ user: _user }: { user?: any }) => {
  const [profile, setProfile] = useState<any>({ first_name: '', last_name: '', blood_group: '', preferred_language: 'en' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetchWithAuth('/patients/me');
        if (response.ok) {
          const data = await response.json();
          setProfile(data.data || {});
        }
      } catch (error) {
        console.error("Failed to fetch profile", error);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMsg('');
    try {
      const { first_name, last_name, phone_number, address, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, preferred_language, chronic_conditions, allergies } = profile;
      const payload = { first_name, last_name, phone_number, address, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, preferred_language, chronic_conditions, allergies };
      
      // Remove undefined values
      Object.keys(payload).forEach(key => (payload as any)[key] === undefined && delete (payload as any)[key]);
      
      const response = await fetchWithAuth('/patients/me', {
        method: 'PATCH',
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        setMsg('Profile saved successfully!');
      } else {
        setMsg('Failed to save profile.');
      }
    } catch (error) {
      setMsg('Error saving profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="animate-fade-in glass-card" style={{ maxWidth: '600px' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '2rem' }}>My Health Profile</h2>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}><Loader className="animate-spin" size={24} style={{ margin: '0 auto' }}/></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>First Name</label>
              <input type="text" value={profile.first_name || ''} onChange={e => setProfile({...profile, first_name: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', background: '#f8fafc' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>Last Name</label>
              <input type="text" value={profile.last_name || ''} onChange={e => setProfile({...profile, last_name: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', background: '#f8fafc' }} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>Blood Group</label>
              <input type="text" value={profile.blood_group || ''} onChange={e => setProfile({...profile, blood_group: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', fontSize: '0.875rem' }}>Preferred Language</label>
              <select value={profile.preferred_language || 'en'} onChange={e => setProfile({...profile, preferred_language: e.target.value})} style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', outline: 'none' }}>
                <option value="en">English</option>
                <option value="ta">Tamil (தமிழ்)</option>
              </select>
            </div>
          </div>
          <button className="btn-primary" style={{ alignSelf: 'flex-start' }} onClick={handleSave} disabled={saving}>
            {saving ? <Loader className="animate-spin" size={16} /> : 'Save Changes'}
          </button>
          {msg && <p style={{ color: msg.includes('success') ? 'var(--secondary)' : 'red', fontSize: '0.875rem' }}>{msg}</p>}
        </div>
      )}
    </div>
  );
};

// --- AUTH WRAPPER ---
const AuthWrapper = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getToken());
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');

  const loginWithCredentials = async (loginEmail: string, loginPassword: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword })
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.data.access_token);
        setIsAuthenticated(true);
      } else {
        setError('Login failed. Please check credentials or start the backend.');
      }
    } catch (err) {
      setError('Connection error. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await loginWithCredentials(email, password);
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email, 
          password, 
          full_name: 'Demo Patient', 
          phone_number: '+919999999999' 
        })
      });
      if (res.ok) {
        handleLogin(new Event('submit') as any);
      } else {
        setError('Registration failed.');
      }
    } catch (err) {
      setError('Connection error.');
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) return <>{children}</>;

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-color)' }}>
      <div className="glass-card" style={{ width: '400px', padding: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem', textAlign: 'center' }}>Sign In to Patient Portal</h2>
        {error && <p style={{ color: 'red', fontSize: '0.875rem', marginBottom: '1rem', textAlign: 'center' }}>{error}</p>}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Email</label>
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: '500' }}>Password</label>
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{ width: '100%', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }} />
          </div>
          <button type="submit" className="btn-primary" style={{ justifyContent: 'center', marginTop: '1rem' }}>
            {loading ? <Loader className="animate-spin" /> : 'Login'}
          </button>
          <button type="button" onClick={handleRegister} className="btn-secondary" style={{ justifyContent: 'center' }}>
            Register Demo Account
          </button>
          
          <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <p style={{ fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.75rem', textAlign: 'center', color: 'var(--text-muted)' }}>Quick Demo Logins</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
              <button type="button" onClick={() => loginWithCredentials('patient@demo.smarthealth.com', 'Demo@Health2026')} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.5rem' }}>Patient</button>
              <button type="button" onClick={() => loginWithCredentials('doctor@demo.smarthealth.com', 'Demo@Health2026')} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.5rem' }}>Doctor</button>
              <button type="button" onClick={() => loginWithCredentials('nurse@demo.smarthealth.com', 'Demo@Health2026')} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.5rem' }}>Nurse</button>
              <button type="button" onClick={() => loginWithCredentials('state.health.admin@demo.smarthealth.com', 'Demo@Health2026')} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.5rem' }}>Admin</button>
              <button type="button" onClick={() => loginWithCredentials('pharmacist@demo.smarthealth.com', 'Demo@Health2026')} className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.5rem' }}>Pharmacy</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

// --- MAIN APP ---

function Dashboard({ user }: { user?: any }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('home');

  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'profile', label: 'My Health Profile', icon: User },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'ai', label: 'AI Wellness Assistant', icon: MessageSquare },
  ];

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.reload();
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return (
          <div className="animate-fade-in">
            <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>Good Morning!</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Welcome to the Patient Portal.</p>
            <div className="quick-actions stagger-2">
              <button className="btn-primary" onClick={() => setActiveTab('appointments')}><Calendar size={20} /> View Appointments</button>
              <button className="btn-secondary" onClick={() => setActiveTab('ai')}><MessageSquare size={20} /> Ask AI Assistant</button>
              <button className="btn-secondary" onClick={() => setActiveTab('profile')}><User size={20} /> Edit Profile</button>
            </div>
          </div>
        );
      case 'ai': return <AiAssistant />;
      case 'appointments': return <Appointments user={user} />;
      case 'profile': return <Profile user={user} />;
      default: return <p>Under development</p>;
    }
  };

  return (
    <div className="app-container">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">PHC</div>
          <div className="sidebar-title">Smart Health</div>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={`nav-item ${activeTab === item.id ? 'active' : ''}`} onClick={() => setActiveTab(item.id)}>
                <Icon className="nav-icon" /><span>{item.label}</span>
              </button>
            )
          })}
        </nav>
        <button className="nav-item" onClick={handleLogout} style={{ marginTop: 'auto', color: 'red' }}>Logout</button>
      </aside>

      <main className="main-content">
        <header className="top-bar">
          <div className="flex items-center gap-4">
            <button className="menu-toggle" onClick={() => setSidebarOpen(true)}><Menu size={24} /></button>
            <h1 className="page-title">{navItems.find(i => i.id === activeTab)?.label || 'Dashboard'}</h1>
          </div>
        </header>

        <div className="page-content">{renderContent()}</div>
      </main>
    </div>
  );
}

function MainApp() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetchWithAuth('/auth/me');
        if (response.ok) {
          const data = await response.json();
          setUser(data.data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  if (loading) return <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}><Loader className="animate-spin" size={48} /></div>;
  if (!user) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
        <h2>Failed to load user profile. Your session may have expired.</h2>
        <button className="btn-primary" onClick={() => { localStorage.removeItem('access_token'); window.location.reload(); }}>
          Back to Login
        </button>
      </div>
    );
  }

  const isDoctor = user?.roles?.some((r: any) => typeof r === 'string' ? r.toLowerCase().includes('doctor') || r === 'MEDICAL_OFFICER' : r.role?.name?.toLowerCase().includes('doctor'));
  const isNurse = user?.roles?.some((r: any) => typeof r === 'string' ? r.toLowerCase().includes('nurse') : r.role?.name?.toLowerCase().includes('nurse'));
  const isPharmacist = user?.roles?.some((r: any) => typeof r === 'string' ? r.toLowerCase().includes('pharmacist') || r.toLowerCase().includes('pharmacy') : r.role?.name?.toLowerCase().includes('pharmacist') || r.role?.name?.toLowerCase().includes('pharmacy'));
  const isAdmin = user?.roles?.some((r: any) => typeof r === 'string' ? r.toLowerCase().includes('admin') : r.role?.name?.toLowerCase().includes('admin'));

  if (isDoctor) {
    return <DoctorDashboard user={user} />;
  }
  if (isNurse) {
    return <NurseDashboard user={user} />;
  }
  if (isPharmacist) {
    return <PharmacistDashboard user={user} />;
  }
  if (isAdmin) {
    return <AdminDashboard user={user} />;
  }

  return <Dashboard user={user} />;
}

export default function App() {
  return (
    <AuthWrapper>
      <MainApp />
    </AuthWrapper>
  );
}
