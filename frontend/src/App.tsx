import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { AuthProvider, useAuth, DEMO_ACCOUNTS } from './context/AuthContext';
import { Layout } from './components/common/Layout';
import { StateView } from './components/common/StateView';

// The 13 Canonical Role Portals
import PatientPortal from './portals/PatientPortal';
import DoctorPortal from './portals/DoctorPortal';
import NursePortal from './portals/NursePortal';
import FacilityAdminPortal from './portals/FacilityAdminPortal';
import PharmacistPortal from './portals/PharmacistPortal';
import DistrictHealthPortal from './portals/DistrictHealthPortal';
import DistrictSupplyPortal from './portals/DistrictSupplyPortal';
import DistrictEmergencyPortal from './portals/DistrictEmergencyPortal';
import StateHealthPortal from './portals/StateHealthPortal';
import StateSupplyPortal from './portals/StateSupplyPortal';
import PublicHealthAnalystPortal from './portals/PublicHealthAnalystPortal';
import NationalHealthPortal from './portals/NationalHealthPortal';
import PlatformAdminPortal from './portals/PlatformAdminPortal';

import { 
  Building2, Users, Stethoscope, Activity, 
  Pill, Truck, ShieldAlert, Globe2, Server, 
  MapPin, Award, CheckCircle, Lock, ArrowRight,
  Sparkles, ShieldCheck
} from 'lucide-react';

// --- LOGIN & DEMO SWITCHER SCREEN ---
const LoginScreen: React.FC = () => {
  const { login, switchDemoRole, isLoading } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const navigate = useNavigate();

  const [email, setEmail] = useState('patient@demo.smarthealth.com');
  const [password, setPassword] = useState('Demo@Health2026');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setLoginError(null);
    const result = await login(email, password);
    setIsSubmitting(false);
    if (!result.success) {
      setLoginError(result.error || 'Authentication failed. Please check credentials.');
    }
  };

  const handleQuickRole = async (roleCode: string) => {
    setIsSubmitting(true);
    setLoginError(null);
    const targetPath = await switchDemoRole(roleCode);
    setIsSubmitting(false);
    if (targetPath && targetPath !== '/login') {
      navigate(targetPath);
    }
  };

  const ROLE_ICONS: Record<string, React.ReactNode> = {
    PATIENT: <Users className="w-4 h-4 text-emerald-600" />,
    DOCTOR: <Stethoscope className="w-4 h-4 text-blue-600" />,
    NURSE: <Activity className="w-4 h-4 text-rose-600" />,
    PHC_IN_CHARGE: <Building2 className="w-4 h-4 text-teal-600" />,
    PHARMACIST: <Pill className="w-4 h-4 text-indigo-600" />,
    DISTRICT_HEALTH_OFFICER: <ShieldCheck className="w-4 h-4 text-cyan-600" />,
    DISTRICT_SUPPLY_OFFICER: <Truck className="w-4 h-4 text-sky-600" />,
    DISTRICT_EMERGENCY_COORDINATOR: <ShieldAlert className="w-4 h-4 text-red-600" />,
    STATE_HEALTH_ADMIN: <Award className="w-4 h-4 text-violet-600" />,
    STATE_SUPPLY_MANAGER: <Truck className="w-4 h-4 text-blue-700" />,
    STATE_PUBLIC_HEALTH_ANALYST: <Activity className="w-4 h-4 text-purple-600" />,
    NATIONAL_HEALTH_AUTHORITY: <Globe2 className="w-4 h-4 text-indigo-800" />,
    SUPER_ADMIN: <Server className="w-4 h-4 text-gray-800" />,
  };

  return (
    <div className="min-h-screen bg-slate-900 text-gray-100 flex flex-col justify-between p-4 sm:p-6 lg:p-8">
      {/* Top Bar with Language Toggle */}
      <div className="flex justify-between items-center max-w-7xl mx-auto w-full mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Building2 className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-white flex items-center gap-1.5">
              PHC CONNECT
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                13 Roles
              </span>
            </span>
            <p className="text-xs text-slate-400">Smart Primary Healthcare & Supply Chain Resilience</p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-800/80 backdrop-blur p-1 rounded-lg border border-slate-700">
          <button
            onClick={() => setLanguage('en')}
            className={`px-3 py-1 rounded text-xs font-bold transition ${
              language === 'en' ? 'bg-emerald-500 text-slate-950' : 'text-slate-300 hover:text-white'
            }`}
          >
            English
          </button>
          <button
            onClick={() => setLanguage('ta')}
            className={`px-3 py-1 rounded text-xs font-bold transition ${
              language === 'ta' ? 'bg-emerald-500 text-slate-950' : 'text-slate-300 hover:text-white'
            }`}
          >
            தமிழ்
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start my-auto">
        {/* Left: Instant 13-Role Demo Selector */}
        <div className="lg:col-span-7 bg-slate-800/50 backdrop-blur border border-slate-700/60 rounded-2xl p-6 shadow-2xl space-y-4">
          <div className="border-b border-slate-700 pb-3">
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              13-Role Interactive Demo Switcher
            </div>
            <h2 className="text-lg font-bold text-white mt-1">Select Any Canonical Role to Experience Full End-to-End Flow</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any role to authenticate instantly with verified database seed credentials.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-[520px] overflow-y-auto pr-1">
            {Object.entries(DEMO_ACCOUNTS).map(([code, account], index) => (
              <button
                key={code}
                type="button"
                onClick={() => handleQuickRole(code)}
                disabled={isSubmitting || isLoading}
                className="flex items-start gap-3 p-3 text-left rounded-xl bg-slate-900/60 hover:bg-slate-700/60 border border-slate-700/70 hover:border-emerald-500/50 transition group disabled:opacity-50"
              >
                <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 group-hover:scale-105 transition">
                  {ROLE_ICONS[code] || <Users className="w-4 h-4 text-emerald-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 group-hover:text-emerald-300">
                      {String(index + 1).padStart(2, '0')}. {account.role}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 opacity-0 group-hover:opacity-100 transition" />
                  </div>
                  <div className="text-xs font-semibold text-white truncate mt-0.5">{account.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono truncate">{account.email}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right: Direct Sign-in Card */}
        <div className="lg:col-span-5 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-2xl p-6 sm:p-8 shadow-2xl">
          <div className="mb-6">
            <h3 className="text-xl font-bold text-white">Manual Sign In</h3>
            <p className="text-xs text-slate-400 mt-1">Authenticate with registered system credentials.</p>
          </div>

          {loginError && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-xs text-red-200">
              {loginError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@demo.smarthealth.com"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none font-mono"
                required
              />
              <span className="text-[11px] text-slate-400 mt-1 inline-block">Default demo password: Demo@Health2026</span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-sm transition shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Lock className="w-4 h-4" />
              {isSubmitting ? 'Authenticating...' : 'Sign In to Portal'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-700/60 text-center text-xs text-slate-400">
            Smart Health & Supply Chain Resilience • Government of Tamil Nadu
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto w-full text-center text-xs text-slate-500 pt-6">
        Protected by Strict Scope Authorization (GLOBAL, STATE, DISTRICT, FACILITY, SELF) & RFC 7807 RFC Auditing.
      </div>
    </div>
  );
};

// --- AUTHENTICATED APP ROUTER ---
const AuthenticatedApp: React.FC = () => {
  const { user, isAuthenticated, isLoading, activeRole } = useAuth();

  if (isLoading) {
    return <StateView type="loading" message="Verifying session and database permissions..." />;
  }

  if (!isAuthenticated || !user) {
    return <LoginScreen />;
  }

  // Get active role default redirect
  const getDefaultPathForRole = () => {
    switch (activeRole) {
      case 'PATIENT': return '/patient';
      case 'DOCTOR': return '/clinical/queue';
      case 'NURSE': return '/clinical/triage';
      case 'PHC_IN_CHARGE': return '/facility';
      case 'PHARMACIST': return '/pharmacy/dispense';
      case 'DISTRICT_HEALTH_OFFICER': return '/district';
      case 'DISTRICT_SUPPLY_OFFICER': return '/supply/requests';
      case 'DISTRICT_EMERGENCY_COORDINATOR': return '/emergency';
      case 'STATE_HEALTH_ADMIN': return '/state';
      case 'STATE_SUPPLY_MANAGER': return '/supply';
      case 'STATE_PUBLIC_HEALTH_ANALYST': return '/analytics';
      case 'NATIONAL_HEALTH_AUTHORITY': return '/national';
      case 'SUPER_ADMIN': return '/platform';
      default: return '/patient';
    }
  };

  return (
    <Layout>
      <Routes>
        {/* Role 01: Patient Portal */}
        <Route path="/patient/*" element={<PatientPortal />} />

        {/* Role 02: Doctor Portal */}
        <Route path="/clinical/queue" element={<DoctorPortal />} />
        <Route path="/clinical/patients" element={<DoctorPortal />} />
        <Route path="/clinical/labs" element={<DoctorPortal />} />

        {/* Role 03: Nurse Portal */}
        <Route path="/clinical/triage" element={<NursePortal />} />
        <Route path="/clinical/*" element={activeRole === 'NURSE' ? <NursePortal /> : <DoctorPortal />} />

        {/* Role 04: PHC In-Charge Facility Admin Portal */}
        <Route path="/facility/*" element={<FacilityAdminPortal />} />

        {/* Role 05: Pharmacist Dispensary Portal */}
        <Route path="/pharmacy/*" element={<PharmacistPortal />} />

        {/* Role 06: District Health Officer Portal */}
        <Route path="/district/*" element={<DistrictHealthPortal />} />

        {/* Role 07 & 10: Supply Chain Portals */}
        <Route path="/supply/requests" element={<DistrictSupplyPortal />} />
        <Route path="/supply/impacts" element={<DistrictSupplyPortal />} />
        <Route path="/supply/*" element={activeRole === 'STATE_SUPPLY_MANAGER' ? <StateSupplyPortal /> : <DistrictSupplyPortal />} />

        {/* Role 08: District Emergency Coordinator Portal */}
        <Route path="/emergency/*" element={<DistrictEmergencyPortal />} />

        {/* Role 09: State Health Administrator Portal */}
        <Route path="/state/*" element={<StateHealthPortal />} />
        <Route path="/governance/*" element={<StateHealthPortal />} />

        {/* Role 11: State Public Health Analyst Portal */}
        <Route path="/analytics/*" element={<PublicHealthAnalystPortal />} />

        {/* Role 12: National Health Authority Portal */}
        <Route path="/national/*" element={<NationalHealthPortal />} />

        {/* Role 13: Super / Platform Administrator Portal */}
        <Route path="/platform/*" element={<PlatformAdminPortal />} />

        {/* Default route redirects to active role's home view */}
        <Route path="/" element={<Navigate to={getDefaultPathForRole()} replace />} />
        <Route path="*" element={<Navigate to={getDefaultPathForRole()} replace />} />
      </Routes>
    </Layout>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <AuthenticatedApp />
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}
