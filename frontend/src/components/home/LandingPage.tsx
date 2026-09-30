import React, { useState } from 'react';
import {
  Building2, Users, Stethoscope, Activity, Pill, Truck,
  ShieldAlert, Globe2, Server, Award, ShieldCheck, LineChart,
  HeartPulse, Boxes, AlertCircle, Languages, Info,
} from 'lucide-react';
import { DEMO_ACCOUNTS, useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { Container } from '../common/Container';
import { Navbar } from './Navbar';
import { Hero } from './Hero';
import { PillarCard } from './PillarCard';
import { RoleFilter, tabId, type RoleCategory } from './RoleFilter';
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

/* Typed data arrays - single source of truth */
const ROLE_ICONS: Record<string, React.ReactNode> = {
  PATIENT:                        <Users        className="h-4 w-4" />,
  DOCTOR:                         <Stethoscope  className="h-4 w-4" />,
  NURSE:                          <Activity     className="h-4 w-4" />,
  PHC_IN_CHARGE:                  <Building2    className="h-4 w-4" />,
  PHARMACIST:                     <Pill         className="h-4 w-4" />,
  DISTRICT_HEALTH_OFFICER:        <ShieldCheck  className="h-4 w-4" />,
  DISTRICT_SUPPLY_OFFICER:        <Truck        className="h-4 w-4" />,
  DISTRICT_EMERGENCY_COORDINATOR: <ShieldAlert  className="h-4 w-4" />,
  STATE_HEALTH_ADMIN:             <Award        className="h-4 w-4" />,
  STATE_SUPPLY_MANAGER:           <Truck        className="h-4 w-4" />,
  STATE_PUBLIC_HEALTH_ANALYST:    <LineChart    className="h-4 w-4" />,
  NATIONAL_HEALTH_AUTHORITY:      <Globe2       className="h-4 w-4" />,
  SUPER_ADMIN:                    <Server       className="h-4 w-4" />,
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
  { key: 'care',   icon: <HeartPulse className="h-5 w-5" /> },
  { key: 'stock',  icon: <Boxes      className="h-5 w-5" /> },
  { key: 'supply', icon: <ShieldCheck className="h-5 w-5" /> },
] as const;

const SECTION_PY = 'py-12 md:py-16';

export const LandingPage: React.FC<Props> = ({
  onOpenLogin,
  onSelectRole,
  loadingRoleCode = null,
  loginError = null,
  onClearError,
}) => {
  const { isLoading } = useAuth();
  const { t } = useLanguage();
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
    <div className="flex min-h-screen w-full flex-col overflow-x-hidden bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-md focus:border focus:border-border focus:bg-card focus:px-4 focus:py-2 focus:text-small focus:font-semibold focus:text-foreground"
      >
        {t('landing.skip')}
      </a>

      <Navbar onOpenLogin={onOpenLogin} />

      <main id="main" className="flex-1">
        {/* Sign-in failure from a role quick-login */}
        {loginError && (
          <div role="alert" className="border-b border-danger-border bg-danger-soft text-danger-text">
            <Container className="flex items-start gap-3 py-3 text-small">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <p className="min-w-0 flex-1">
                <span className="font-semibold">{t('landing.error.title')}: </span>
                <span className="break-words">{loginError}</span>
              </p>
              {onClearError && (
                <button
                  type="button"
                  onClick={onClearError}
                  className="shrink-0 rounded-sm font-semibold underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {t('landing.error.dismiss')}
                </button>
              )}
            </Container>
          </div>
        )}

        <Hero onOpenLogin={onOpenLogin} />

        {/* Capabilities */}
        <section
          id="capabilities"
          aria-labelledby="capabilities-title"
          className={`scroll-mt-20 border-b border-border bg-card ${SECTION_PY}`}
        >
          <Container>
            <div className="max-w-2xl">
              <h2 id="capabilities-title" className="text-2xl font-semibold tracking-tight text-foreground">
                {t('landing.cap.title')}
              </h2>
              <p className="mt-2 text-body text-muted-foreground">{t('landing.cap.lead')}</p>
            </div>

            <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3 lg:gap-6">
              {PILLARS.map((p) => (
                <PillarCard
                  key={p.key}
                  icon={p.icon}
                  title={t(`landing.pillar.${p.key}.title`)}
                  description={t(`landing.pillar.${p.key}.desc`)}
                  items={[1, 2, 3, 4].map((n) => t(`landing.pillar.${p.key}.i${n}`))}
                />
              ))}
            </div>

            <div className="mt-6 flex items-start gap-3 rounded-lg border border-border bg-background p-4">
              <Languages className="mt-0.5 h-5 w-5 shrink-0 text-primary-text" aria-hidden="true" />
              <div>
                <h3 className="text-body font-semibold text-foreground">{t('landing.lang.title')}</h3>
                <p className="text-small text-muted-foreground">{t('landing.lang.desc')}</p>
              </div>
            </div>
          </Container>
        </section>

        {/* Role portals */}
        <section
          id="roles"
          aria-labelledby="roles-title"
          className={`scroll-mt-20 border-b border-border ${SECTION_PY}`}
        >
          <Container>
            <div className="max-w-2xl">
              <p className="text-small font-semibold uppercase tracking-wide text-primary-text">
                {t('landing.roles.eyebrow')}
              </p>
              <h2 id="roles-title" className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
                {t('landing.roles.title')}
              </h2>
              <p className="mt-2 text-body text-muted-foreground">{t('landing.roles.lead')}</p>
            </div>

            <p className="mt-4 flex items-start gap-2 text-small text-muted-foreground">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary-text" aria-hidden="true" />
              <span>{t('landing.roles.note')}</span>
            </p>

            <div className="mt-6">
              <RoleFilter selected={cat} counts={counts} onChange={setCat} panelId="role-panel" />
            </div>

            <div
              id="role-panel"
              role="tabpanel"
              aria-labelledby={tabId(cat)}
              className="mt-6 grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-3"
            >
              {filtered.map(([code, account], index) => (
                <RoleCard
                  key={code}
                  code={code}
                  index={index}
                  account={account}
                  category={ROLE_CATEGORIES[code] ?? 'admin'}
                  icon={ROLE_ICONS[code] ?? <Users className="h-4 w-4" />}
                  isDisabled={isLoading || !!loadingRoleCode}
                  isLoading={loadingRoleCode === code}
                  onSelect={onSelectRole}
                />
              ))}
            </div>
          </Container>
        </section>

        {/* Workflow */}
        <section
          id="workflow"
          aria-labelledby="workflow-title"
          className={`scroll-mt-20 bg-card ${SECTION_PY}`}
        >
          <Container>
            <div className="max-w-2xl">
              <h2 id="workflow-title" className="text-2xl font-semibold tracking-tight text-foreground">
                {t('landing.flow.title')}
              </h2>
              <p className="mt-2 text-body text-muted-foreground">{t('landing.flow.lead')}</p>
            </div>
            <div className="mt-8">
              <FlowStepper />
            </div>
          </Container>
        </section>
      </main>

      <Footer />
    </div>
  );
};
