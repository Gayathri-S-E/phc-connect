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

// Capacity, supply intelligence and Google-powered screens
import CapacityDashboard from './pages/capacity/CapacityDashboard';
import FacilityBedsPanel from './pages/capacity/FacilityBedsPanel';
import StockoutWarnings from './pages/supply-intelligence/StockoutWarnings';
import RedistributionPlanner from './pages/supply-intelligence/RedistributionPlanner';
import FederatedModelPanel from './pages/supply-intelligence/FederatedModelPanel';
import NearestFacilities from './pages/google/NearestFacilities';
import GoogleServicesPanel from './pages/google/GoogleServicesPanel';

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
  const [loadingRoleCode, setLoadingRoleCode] = useState<string | null>(null);
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
    setLoadingRoleCode(roleCode);
    setLoginError(null);
    try {
      const result = await switchDemoRole(roleCode);
      if (result.success && result.path && result.path !== '/login') {
        navigate(result.path);
      } else if (!result.success) {
        setLoginError(result.error || 'Could not sign in. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
      setLoadingRoleCode(null);
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
        loadingRoleCode={loadingRoleCode}
        loginError={loginError}
        onClearError={() => setLoginError(null)}
      />

      {/* Login Modal Overlay */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/40 backdrop-blur-xs animate-fade-in">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 max-w-md w-full max-h-[92vh] overflow-y-auto shadow-2xl space-y-5 relative">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-800 text-lg font-bold p-1 cursor-pointer"
            >
              ✕
            </button>

            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-sky-700 uppercase">
                <Lock className="w-4 h-4" />
                Sign In to Platform
              </div>
              <h3 className="text-xl font-extrabold text-slate-900 mt-1">Med2Us Authentication</h3>
              <p className="text-xs text-slate-500">Enter system credentials to access authorized role views.</p>
            </div>

            {loginError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 font-medium">
                {loginError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@demo.smarthealth.com"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-sm text-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none font-mono transition"
                  required
                />
                <span className="text-[11px] text-slate-500 mt-1 inline-block">Default demo password: Demo@Health2026</span>
              </div>

              <button
                type="submit"
                disabled={isSubmitting || isLoading}
                className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-lg text-sm transition shadow-md shadow-sky-600/20 flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <Lock className="w-4 h-4" />
                {isSubmitting ? 'Authenticating...' : 'Sign In to Portal'}
              </button>
            </form>

            <div className="pt-4 border-t border-slate-200">
              <div className="text-[11px] font-bold text-slate-700 uppercase mb-2">
                Demo credentials · password <span className="font-mono text-sky-700 font-bold">Demo@Health2026</span>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                {Object.entries(DEMO_ACCOUNTS).map(([key, acc]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => { setEmail(acc.email); setPassword('Demo@Health2026'); setLoginError(null); }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg border text-xs transition cursor-pointer ${
                      email === acc.email
                        ? 'border-sky-500 bg-sky-50 text-sky-950 font-bold'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white text-slate-700'
                    }`}
                  >
                    <span className="block font-bold text-slate-900">{acc.name}</span>
                    <span className="block font-mono text-slate-500 truncate">{acc.email}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 text-center text-xs text-slate-500 font-medium">
              Med2Us — Connected Healthcare &amp; Supply Chain Resilience • Government of Tamil Nadu
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// --- ROLE GUARD ---
// Client-side route protection (UX layer). The backend remains the authority and re-checks every request.
const SUPER = 'SUPER_ADMIN';
const ROUTE_ROLES: Record<string, string[]> = {
  '/patient': ['PATIENT'],
  '/clinical': ['DOCTOR', 'NURSE'],
  '/facility': ['PHC_IN_CHARGE'],
  '/pharmacy': ['PHARMACIST', 'DOCTOR'],
  '/district': ['DISTRICT_HEALTH_OFFICER'],
  '/supply': ['DISTRICT_SUPPLY_OFFICER', 'STATE_SUPPLY_MANAGER'],
  '/emergency': ['DISTRICT_EMERGENCY_COORDINATOR'],
  '/state': ['STATE_HEALTH_ADMIN'],
  '/governance': ['DISTRICT_HEALTH_OFFICER', 'STATE_HEALTH_ADMIN', 'NATIONAL_HEALTH_AUTHORITY'],
  '/analytics': ['STATE_PUBLIC_HEALTH_ANALYST'],
  '/national': ['NATIONAL_HEALTH_AUTHORITY'],
  '/platform': [],
  '/capacity': ['PHC_IN_CHARGE', 'DISTRICT_HEALTH_OFFICER', 'DISTRICT_SUPPLY_OFFICER', 'DISTRICT_EMERGENCY_COORDINATOR',
    'STATE_HEALTH_ADMIN', 'STATE_SUPPLY_MANAGER', 'STATE_PUBLIC_HEALTH_ANALYST', 'NATIONAL_HEALTH_AUTHORITY', 'DOCTOR', 'NURSE'],
  '/intelligence': ['PHC_IN_CHARGE', 'PHARMACIST', 'DISTRICT_HEALTH_OFFICER', 'DISTRICT_SUPPLY_OFFICER',
    'STATE_HEALTH_ADMIN', 'STATE_SUPPLY_MANAGER', 'STATE_PUBLIC_HEALTH_ANALYST', 'NATIONAL_HEALTH_AUTHORITY'],
  '/facilities/nearest': ['*'],
  '/admin/google': ['STATE_HEALTH_ADMIN', 'NATIONAL_HEALTH_AUTHORITY'],
};

const RequireRole: React.FC<{ prefix: string; fallback: string; children: React.ReactElement }> = ({ prefix, fallback, children }) => {
  const { activeRole } = useAuth();
  const allowed = ROUTE_ROLES[prefix] ?? [];
  const ok = !!activeRole && (activeRole === SUPER || allowed.includes('*') || allowed.includes(activeRole));
  return ok ? children : <Navigate to={fallback} replace />;
};

// --- AUTHENTICATED APP ROUTER ---
const AuthenticatedApp: React.FC = () => {
  const { user, isAuthenticated, isLoading, activeRole } = useAuth();

  if (isLoading) {
    return <StateView type="loading" message="Signing you in..." />;
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

  const home = getDefaultPathForRole();

  return (
    <Layout>
      <Routes>
        {/* Role 01: Patient Portal */}
        <Route path="/patient" element={<RequireRole prefix="/patient" fallback={home}><PatientPortal /></RequireRole>} />
        <Route path="/patient/*" element={<RequireRole prefix="/patient" fallback={home}><PatientPortal /></RequireRole>} />

        {/* Role 02 & 03: Clinical Portals (Doctor & Nurse) */}
        <Route path="/clinical/queue" element={<RequireRole prefix="/clinical" fallback={home}><DoctorPortal /></RequireRole>} />
        <Route path="/clinical/patients" element={<RequireRole prefix="/clinical" fallback={home}><DoctorPortal /></RequireRole>} />
        <Route path="/clinical/labs" element={<RequireRole prefix="/clinical" fallback={home}><DoctorPortal /></RequireRole>} />
        <Route path="/clinical/inventory" element={<RequireRole prefix="/clinical" fallback={home}><DoctorPortal /></RequireRole>} />
        <Route path="/clinical/triage" element={<RequireRole prefix="/clinical" fallback={home}><NursePortal /></RequireRole>} />
        <Route path="/clinical/registration" element={<RequireRole prefix="/clinical" fallback={home}><NursePortal /></RequireRole>} />
        <Route path="/clinical/coldchain" element={<RequireRole prefix="/clinical" fallback={home}><NursePortal /></RequireRole>} />
        <Route path="/clinical/immunization" element={<RequireRole prefix="/clinical" fallback={home}><NursePortal /></RequireRole>} />
        <Route path="/clinical/*" element={<RequireRole prefix="/clinical" fallback={home}>{activeRole === 'NURSE' ? <NursePortal /> : <DoctorPortal />}</RequireRole>} />

        {/* Role 04: PHC In-Charge Facility Admin Portal */}
        <Route path="/facility" element={<RequireRole prefix="/facility" fallback={home}><FacilityAdminPortal /></RequireRole>} />
        <Route path="/facility/*" element={<RequireRole prefix="/facility" fallback={home}><FacilityAdminPortal /></RequireRole>} />

        {/* Role 05: Pharmacist Dispensary Portal */}
        <Route path="/pharmacy/dispense" element={<RequireRole prefix="/pharmacy" fallback={home}><PharmacistPortal /></RequireRole>} />
        <Route path="/pharmacy/inventory" element={<RequireRole prefix="/pharmacy" fallback={home}>{activeRole === 'DOCTOR' ? <DoctorPortal /> : <PharmacistPortal />}</RequireRole>} />
        <Route path="/pharmacy/alerts" element={<RequireRole prefix="/pharmacy" fallback={home}><PharmacistPortal /></RequireRole>} />
        <Route path="/pharmacy/receipts" element={<RequireRole prefix="/pharmacy" fallback={home}><PharmacistPortal /></RequireRole>} />
        <Route path="/pharmacy/druginfo" element={<RequireRole prefix="/pharmacy" fallback={home}><PharmacistPortal /></RequireRole>} />
        <Route path="/pharmacy/*" element={<RequireRole prefix="/pharmacy" fallback={home}><PharmacistPortal /></RequireRole>} />

        {/* Role 06: District Health Officer Portal */}
        <Route path="/district" element={<RequireRole prefix="/district" fallback={home}><DistrictHealthPortal /></RequireRole>} />
        <Route path="/district/*" element={<RequireRole prefix="/district" fallback={home}><DistrictHealthPortal /></RequireRole>} />

        {/* Role 07 & 10: Supply Chain Portals (District & State) */}
        <Route path="/supply/requests" element={<RequireRole prefix="/supply" fallback={home}><DistrictSupplyPortal /></RequireRole>} />
        <Route path="/supply/transfers" element={<RequireRole prefix="/supply" fallback={home}><DistrictSupplyPortal /></RequireRole>} />
        <Route path="/supply/warehouse" element={<RequireRole prefix="/supply" fallback={home}>{activeRole === 'STATE_SUPPLY_MANAGER' ? <StateSupplyPortal /> : <DistrictSupplyPortal />}</RequireRole>} />
        <Route path="/supply/impacts" element={<RequireRole prefix="/supply" fallback={home}><DistrictSupplyPortal /></RequireRole>} />
        <Route path="/supply/escalated" element={<RequireRole prefix="/supply" fallback={home}><StateSupplyPortal /></RequireRole>} />
        <Route path="/supply/monitoring" element={<RequireRole prefix="/supply" fallback={home}><StateSupplyPortal /></RequireRole>} />
        <Route path="/supply/shortages" element={<RequireRole prefix="/supply" fallback={home}><StateSupplyPortal /></RequireRole>} />
        <Route path="/supply/*" element={<RequireRole prefix="/supply" fallback={home}>{activeRole === 'STATE_SUPPLY_MANAGER' ? <StateSupplyPortal /> : <DistrictSupplyPortal />}</RequireRole>} />

        {/* Role 08: District Emergency Coordinator Portal */}
        <Route path="/emergency" element={<RequireRole prefix="/emergency" fallback={home}><DistrictEmergencyPortal /></RequireRole>} />
        <Route path="/emergency/*" element={<RequireRole prefix="/emergency" fallback={home}><DistrictEmergencyPortal /></RequireRole>} />

        {/* Role 09: State Health Administrator Portal */}
        <Route path="/state" element={<RequireRole prefix="/state" fallback={home}><StateHealthPortal /></RequireRole>} />
        <Route path="/state/*" element={<RequireRole prefix="/state" fallback={home}><StateHealthPortal /></RequireRole>} />

        {/* Cross-Role Governance Routes (District, National, State) */}
        <Route
          path="/governance/*"
          element={
            <RequireRole prefix="/governance" fallback={home}>
              {activeRole === 'DISTRICT_HEALTH_OFFICER' ? (
                <DistrictHealthPortal />
              ) : activeRole === 'NATIONAL_HEALTH_AUTHORITY' ? (
                <NationalHealthPortal />
              ) : (
                <StateHealthPortal />
              )}
            </RequireRole>
          }
        />

        {/* Role 11: State Public Health Analyst Portal */}
        <Route path="/analytics" element={<RequireRole prefix="/analytics" fallback={home}><PublicHealthAnalystPortal /></RequireRole>} />
        <Route path="/analytics/*" element={<RequireRole prefix="/analytics" fallback={home}><PublicHealthAnalystPortal /></RequireRole>} />

        {/* Role 12: National Health Authority Portal */}
        <Route path="/national" element={<RequireRole prefix="/national" fallback={home}><NationalHealthPortal /></RequireRole>} />
        <Route path="/national/*" element={<RequireRole prefix="/national" fallback={home}><NationalHealthPortal /></RequireRole>} />

        {/* Role 13: Super / Platform Administrator Portal */}
        <Route path="/platform" element={<RequireRole prefix="/platform" fallback={home}><PlatformAdminPortal /></RequireRole>} />
        <Route path="/platform/*" element={<RequireRole prefix="/platform" fallback={home}><PlatformAdminPortal /></RequireRole>} />

        {/* Cross-role screens: beds, supply intelligence, Google tools (access is enforced by the backend) */}
        <Route path="/capacity" element={<RequireRole prefix="/capacity" fallback={home}><CapacityDashboard /></RequireRole>} />
        <Route path="/capacity/beds" element={<RequireRole prefix="/capacity" fallback={home}><FacilityBedsPanel /></RequireRole>} />
        <Route path="/intelligence/warnings" element={<RequireRole prefix="/intelligence" fallback={home}><StockoutWarnings /></RequireRole>} />
        <Route path="/intelligence/redistribution" element={<RequireRole prefix="/intelligence" fallback={home}><RedistributionPlanner /></RequireRole>} />
        <Route path="/intelligence/federation" element={<RequireRole prefix="/intelligence" fallback={home}><FederatedModelPanel /></RequireRole>} />
        <Route path="/facilities/nearest" element={<RequireRole prefix="/facilities/nearest" fallback={home}><NearestFacilities /></RequireRole>} />
        <Route path="/admin/google" element={<RequireRole prefix="/admin/google" fallback={home}><GoogleServicesPanel /></RequireRole>} />

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
