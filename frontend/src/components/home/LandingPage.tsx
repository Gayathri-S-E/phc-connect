import React, { useState } from 'react';
import {
  Building2, Users, Stethoscope, Activity, Pill, Truck,
  ShieldAlert, Globe2, Server, Award, ShieldCheck, LineChart,
  HeartPulse, Boxes, Layers,
} from 'lucide-react';
import { DEMO_ACCOUNTS, useAuth } from '../../context/AuthContext';
import { Container } from '../common/Container';
import { Navbar } from './Navbar';
import { Hero } from './Hero';
import { PillarCard } from './PillarCard';
import { RoleFilter, type RoleCategory } from './RoleFilter';
import { RoleCard } from './RoleCard';
import { FlowStepper } from './FlowStepper';
import { Footer } from './Footer';

interface Props {
  onOpenLogin: () => void;
  onSelectRole: (roleCode: string) => void;
  loadingRoleCode?: string | null;
  loginError?: string | null;
  onClearError?: () => void;
}

/* Typed data arrays — single source of truth */
const ROLE_ICONS: Record<string, React.ReactNode> = {
  PATIENT:                      <Users        className="w-4 h-4" />,
  DOCTOR:                       <Stethoscope  className="w-4 h-4" />,
  NURSE:                        <Activity     className="w-4 h-4" />,
  PHC_IN_CHARGE:                <Building2    className="w-4 h-4" />,
  PHARMACIST:                   <Pill         className="w-4 h-4" />,
  DISTRICT_HEALTH_OFFICER:      <ShieldCheck  className="w-4 h-4" />,
  DISTRICT_SUPPLY_OFFICER:      <Truck        className="w-4 h-4" />,
  DISTRICT_EMERGENCY_COORDINATOR: <ShieldAlert className="w-4 h-4" />,
  STATE_HEALTH_ADMIN:           <Award        className="w-4 h-4" />,
  STATE_SUPPLY_MANAGER:         <Truck        className="w-4 h-4" />,
  STATE_PUBLIC_HEALTH_ANALYST:  <LineChart    className="w-4 h-4" />,
  NATIONAL_HEALTH_AUTHORITY:    <Globe2       className="w-4 h-4" />,
  SUPER_ADMIN:                  <Server       className="w-4 h-4" />,
};

const ROLE_CATEGORIES: Record<string, 'clinical' | 'supply' | 'admin'> = {
  PATIENT:                        'clinical',
  DOCTOR:                         'clinical',
  NURSE:                          'clinical',
  PHC_IN_CHARGE:                  'clinical',
  PHARMACIST:                     'supply',
  DISTRICT_HEALTH_OFFICER:        'admin',
  DISTRICT_SUPPLY_OFFICER:        'supply',
  DISTRICT_EMERGENCY_COORDINATOR: 'admin',
  STATE_HEALTH_ADMIN:             'admin',
  STATE_SUPPLY_MANAGER:           'supply',
  STATE_PUBLIC_HEALTH_ANALYST:    'admin',
  NATIONAL_HEALTH_AUTHORITY:      'admin',
  SUPER_ADMIN:                    'admin',
};

const PILLARS = [
  {
    icon: <HeartPulse className="w-6 h-6" />,
    iconBg: '#0284c7',
    title: 'Healthcare Intelligence',
    description: 'Streamlined patient registration, OPD triage, electronic prescriptions, and lab workflows built for high-volume primary care centers.',
  },
  {
    icon: <Boxes className="w-6 h-6" />,
    iconBg: '#0d9488',
    title: 'Inventory Coordination',
    description: 'Automated stock thresholds, batch expiry alerts, dispensary management, and inter-facility transfers to prevent medicine stock-outs.',
  },
  {
    icon: <ShieldCheck className="w-6 h-6" />,
    iconBg: '#1d4ed8',
    title: 'Supply Chain Resilience',
    description: 'Multi-tier administrative oversight from District Officers to National Health Authorities, ensuring emergency dispatch during public health crises.',
    colSpan: true,
  },
];

/* Section vertical rhythm */
const SECTION_PY = 'py-16 md:py-20 lg:py-24';

export const LandingPage: React.FC<Props> = ({
  onOpenLogin,
  onSelectRole,
  loadingRoleCode = null,
  loginError = null,
  onClearError,
}) => {
  const { isLoading } = useAuth();
  const [cat, setCat] = useState<RoleCategory>('all');

  const allRoles = Object.entries(DEMO_ACCOUNTS);

  const counts: Record<RoleCategory, number> = {
    all:      allRoles.length,
    clinical: allRoles.filter(([c]) => ROLE_CATEGORIES[c] === 'clinical').length,
    supply:   allRoles.filter(([c]) => ROLE_CATEGORIES[c] === 'supply').length,
    admin:    allRoles.filter(([c]) => ROLE_CATEGORIES[c] === 'admin').length,
  };

  const filtered = cat === 'all'
    ? allRoles
    : allRoles.filter(([c]) => ROLE_CATEGORIES[c] === cat);

  return (
    <div className="min-h-screen flex flex-col w-full overflow-x-hidden" style={{ backgroundColor: '#f8fafc', color: '#0f172a' }}>

      {/* ── 1. Sticky Navbar ── */}
      <Navbar onOpenLogin={onOpenLogin} />

      <main className="flex-1">

        {/* Global Error Banner if demo authentication fails */}
        {loginError && (
          <div className="bg-red-600/90 text-white px-4 py-3 flex items-center justify-between text-sm shadow-md sticky top-[72px] z-40 backdrop-blur-sm">
            <div className="flex items-center gap-2 max-w-5xl mx-auto w-full">
              <span className="font-bold">⚠️ Connection Notice:</span>
              <span className="truncate">{loginError}</span>
              {onClearError && (
                <button
                  onClick={onClearError}
                  className="ml-auto underline hover:text-red-100 font-semibold text-xs"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        )}

        {/* ── 2. Hero ── */}
        <Hero onOpenLogin={onOpenLogin} />

        {/* ── 3. Core Platform Pillars ── */}
        <section id="platform" className={`scroll-mt-[72px] ${SECTION_PY} border-b border-slate-200`} style={{ backgroundColor: '#ffffff' }}>
          <Container>
            {/* Centered section header */}
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight text-balance">
                Core Platform Pillars
              </h2>
              <p className="mt-3 text-base text-slate-600 leading-relaxed text-pretty">
                Designed for synchronized healthcare delivery and resilient inventory management.
              </p>
            </div>

            {/* 3-col card grid — 3rd card spans full width on md (2-col) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 items-stretch">
              {PILLARS.map((p) => (
                <PillarCard
                  key={p.title}
                  icon={p.icon}
                  iconBg={p.iconBg}
                  title={p.title}
                  description={p.description}
                  className={p.colSpan ? 'md:col-span-2 lg:col-span-1' : ''}
                />
              ))}
            </div>
          </Container>
        </section>

        {/* ── 4. 13 Canonical Role Portals (Dark) ── */}
        <section
          id="roles"
          className={`scroll-mt-[72px] ${SECTION_PY} border-b border-slate-800`}
          style={{ backgroundColor: '#0f172a' }}
        >
          <Container>
            {/* Header row: on lg → space-between; on mobile → stacked */}
            <div className="flex flex-col lg:flex-row lg:items-end gap-6 mb-8 pb-6 border-b min-w-0" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-sky-400 text-xs font-bold uppercase tracking-wider mb-1">
                  <Layers className="w-4 h-4 shrink-0" />
                  Role-Based Architecture (RBAC)
                </div>
                <h2
                  className="font-extrabold text-white tracking-tight text-balance"
                  style={{ fontSize: 'clamp(1.5rem, 3vw + 0.5rem, 2.5rem)' }}
                >
                  13 Canonical Role Portals
                </h2>
                <p className="mt-1 text-sm text-slate-400 max-w-xl text-pretty">
                  Click any verified demo persona to authenticate directly into their authorized portal view.
                </p>
              </div>

              {/* Segmented filter tabs — never clipped */}
              <div className="shrink-0 max-w-full overflow-x-auto no-scrollbar">
                <RoleFilter selected={cat} counts={counts} onChange={setCat} />
              </div>
            </div>

            {/* Role cards grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
              {filtered.map(([code, account], index) => (
                <RoleCard
                  key={code}
                  code={code}
                  index={index}
                  account={account}
                  category={ROLE_CATEGORIES[code] ?? 'admin'}
                  icon={ROLE_ICONS[code] ?? <Users className="w-4 h-4" />}
                  isDisabled={isLoading || !!loadingRoleCode}
                  isLoading={loadingRoleCode === code}
                  onSelect={onSelectRole}
                />
              ))}
            </div>
          </Container>
        </section>

        {/* ── 5. End-to-End Healthcare Flow ── */}
        <section id="workflow" className={`scroll-mt-[72px] ${SECTION_PY} border-b border-slate-200`} style={{ backgroundColor: '#ffffff' }}>
          <Container>
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight text-balance">
                End-to-End Healthcare Flow
              </h2>
              <p className="mt-3 text-base text-slate-600 leading-relaxed text-pretty">
                How patient care directly synchronizes with regional inventory fulfillment.
              </p>
            </div>
            <FlowStepper />
          </Container>
        </section>

      </main>

      {/* ── 6. Footer ── */}
      <Footer />
    </div>
  );
};
