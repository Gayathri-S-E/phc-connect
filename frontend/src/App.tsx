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
import { LandingPage } from './components/home/LandingPage';

const UnauthenticatedApp: React.FC = () => {
  const { login, switchDemoRole, isLoading } = useAuth();
  const { t, language, setLanguage } = useLanguage();
  const navigate = useNavigate();

  const [showLoginModal, setShowLoginModal] = useState(false);
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
    const result = await switchDemoRole(roleCode);
    setIsSubmitting(false);
    if (result.success && result.path && result.path !== '/login') {
      navigate(result.path);
    } else if (!result.success) {
      setLoginError(result.error || 'Failed to authenticate demo account.');
    }
  };

  const ROLE_ICONS: Record<string, React.ReactNode> = {
    PATIENT: <Users className="w-4 h-4 text-emerald-600" />,
    DOCTOR: <Stethoscope className="w-4 h-4 text-sky-600" />,
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
    SUPER_ADMIN: <Server className="w-4 h-4 text-slate-800" />,
  };

  return (
    <>
      <LandingPage
        onOpenLogin={() => setShowLoginModal(true)}
        onSelectRole={(roleCode) => handleQuickRole(roleCode)}
      />

      {/* Login Modal Overlay */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 sm:p-8 max-w-md w-full shadow-2xl space-y-5 relative">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-lg font-bold p-1"
            >
              ✕
            </button>

            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-sky-400 uppercase">
                <Lock className="w-4 h-4" />
                Sign In to Platform
              </div>
              <h3 className="text-xl font-bold text-white mt-1">Portal Authentication</h3>
              <p className="text-xs text-slate-400">Enter system credentials to access authorized role views.</p>
            </div>

            {loginError && (
              <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-xs text-red-200">
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
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none font-mono"
                  required
                />
                <span className="text-[11px] text-slate-400 mt-1 inline-block">Default demo password: Demo@Health2026</span>
              </div>

              <button
                type="submit"
                disabled={isSubmitting || isLoading}
                className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-lg text-sm transition shadow-lg shadow-sky-600/20 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Lock className="w-4 h-4" />
                {isSubmitting ? 'Authenticating...' : 'Sign In to Portal'}
              </button>
            </form>

            <div className="pt-4 border-t border-slate-800 text-center text-xs text-slate-400">
              Smart Health & Supply Chain Resilience • Government of Tamil Nadu
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// --- AUTHENTICATED APP ROUTER ---
const AuthenticatedApp: React.FC = () => {
  const { user, isAuthenticated, isLoading, activeRole } = useAuth();

  if (isLoading) {
    return <StateView type="loading" message="Verifying session and database permissions..." />;
  }

  if (!isAuthenticated || !user) {
    return <UnauthenticatedApp />;
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
        <Route path="/patient" element={<PatientPortal />} />
        <Route path="/patient/*" element={<PatientPortal />} />

        {/* Role 02 & 03: Clinical Portals (Doctor & Nurse) */}
        <Route path="/clinical/queue" element={<DoctorPortal />} />
        <Route path="/clinical/patients" element={<DoctorPortal />} />
        <Route path="/clinical/labs" element={<DoctorPortal />} />
        <Route path="/clinical/inventory" element={<DoctorPortal />} />
        <Route path="/clinical/triage" element={<NursePortal />} />
        <Route path="/clinical/registration" element={<NursePortal />} />
        <Route path="/clinical/coldchain" element={<NursePortal />} />
        <Route path="/clinical/immunization" element={<NursePortal />} />
        <Route path="/clinical/*" element={activeRole === 'NURSE' ? <NursePortal /> : <DoctorPortal />} />

        {/* Role 04: PHC In-Charge Facility Admin Portal */}
        <Route path="/facility" element={<FacilityAdminPortal />} />
        <Route path="/facility/*" element={<FacilityAdminPortal />} />

        {/* Role 05: Pharmacist Dispensary Portal */}
        <Route path="/pharmacy/dispense" element={<PharmacistPortal />} />
        <Route path="/pharmacy/inventory" element={activeRole === 'DOCTOR' ? <DoctorPortal /> : <PharmacistPortal />} />
        <Route path="/pharmacy/alerts" element={<PharmacistPortal />} />
        <Route path="/pharmacy/receipts" element={<PharmacistPortal />} />
        <Route path="/pharmacy/druginfo" element={<PharmacistPortal />} />
        <Route path="/pharmacy/*" element={<PharmacistPortal />} />

        {/* Role 06: District Health Officer Portal */}
        <Route path="/district" element={<DistrictHealthPortal />} />
        <Route path="/district/*" element={<DistrictHealthPortal />} />

        {/* Role 07 & 10: Supply Chain Portals (District & State) */}
        <Route path="/supply/requests" element={<DistrictSupplyPortal />} />
        <Route path="/supply/transfers" element={<DistrictSupplyPortal />} />
        <Route path="/supply/warehouse" element={activeRole === 'STATE_SUPPLY_MANAGER' ? <StateSupplyPortal /> : <DistrictSupplyPortal />} />
        <Route path="/supply/impacts" element={<DistrictSupplyPortal />} />
        <Route path="/supply/escalated" element={<StateSupplyPortal />} />
        <Route path="/supply/monitoring" element={<StateSupplyPortal />} />
        <Route path="/supply/shortages" element={<StateSupplyPortal />} />
        <Route path="/supply/*" element={activeRole === 'STATE_SUPPLY_MANAGER' ? <StateSupplyPortal /> : <DistrictSupplyPortal />} />

        {/* Role 08: District Emergency Coordinator Portal */}
        <Route path="/emergency" element={<DistrictEmergencyPortal />} />
        <Route path="/emergency/*" element={<DistrictEmergencyPortal />} />

        {/* Role 09: State Health Administrator Portal */}
        <Route path="/state" element={<StateHealthPortal />} />
        <Route path="/state/*" element={<StateHealthPortal />} />

        {/* Cross-Role Governance Routes (District, National, State) */}
        <Route
          path="/governance/*"
          element={
            activeRole === 'DISTRICT_HEALTH_OFFICER' ? (
              <DistrictHealthPortal />
            ) : activeRole === 'NATIONAL_HEALTH_AUTHORITY' ? (
              <NationalHealthPortal />
            ) : (
              <StateHealthPortal />
            )
          }
        />

        {/* Role 11: State Public Health Analyst Portal */}
        <Route path="/analytics" element={<PublicHealthAnalystPortal />} />
        <Route path="/analytics/*" element={<PublicHealthAnalystPortal />} />

        {/* Role 12: National Health Authority Portal */}
        <Route path="/national" element={<NationalHealthPortal />} />
        <Route path="/national/*" element={<NationalHealthPortal />} />

        {/* Role 13: Super / Platform Administrator Portal */}
        <Route path="/platform" element={<PlatformAdminPortal />} />
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
