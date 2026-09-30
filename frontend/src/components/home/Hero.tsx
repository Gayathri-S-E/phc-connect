import React from 'react';
import { ArrowRight, Languages, LogIn } from 'lucide-react';
import { Container } from '../common/Container';
import { useLanguage } from '../../context/LanguageContext';
import { formatRoleName } from '../../utils/formatters';

interface HeroProps {
  onOpenLogin: () => void;
}

/* Real role tiers: every code exists in DEMO_ACCOUNTS / the backend role catalogue. */
const TIERS: { key: string; roles: string[] }[] = [
  {
    key: 'facility',
    roles: ['PATIENT', 'DOCTOR', 'NURSE', 'PHC_IN_CHARGE', 'PHARMACIST'],
  },
  {
    key: 'district',
    roles: ['DISTRICT_HEALTH_OFFICER', 'DISTRICT_SUPPLY_OFFICER', 'DISTRICT_EMERGENCY_COORDINATOR'],
  },
  {
    key: 'state',
    roles: [
      'STATE_HEALTH_ADMIN',
      'STATE_SUPPLY_MANAGER',
      'STATE_PUBLIC_HEALTH_ANALYST',
      'NATIONAL_HEALTH_AUTHORITY',
      'SUPER_ADMIN',
    ],
  },
];

const focusRing =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background';

export const Hero: React.FC<HeroProps> = ({ onOpenLogin }) => {
  const { t } = useLanguage();

  return (
    <section id="top" aria-labelledby="hero-title" className="border-b border-border bg-background">
      <Container className="grid items-start gap-10 py-10 sm:py-14 lg:grid-cols-12 lg:gap-12 lg:py-20">
        {/* Left: what it is, who it is for, primary action */}
        <div className="lg:col-span-7">
          <p className="text-small font-semibold uppercase tracking-wide text-primary-text">
            {t('landing.hero.kicker')}
          </p>
          <h1
            id="hero-title"
            className="mt-3 text-balance text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-5xl"
          >
            {t('landing.hero.title')}
          </h1>
          <p className="mt-5 max-w-2xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            {t('landing.hero.lead')}
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={onOpenLogin}
              className={`inline-flex h-12 items-center justify-center gap-2 rounded-md bg-primary px-6 text-sm font-semibold text-primary-foreground hover:bg-primary-hover ${focusRing}`}
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              {t('form.signIn')}
            </button>
            <a
              href="#roles"
              className={`inline-flex h-12 items-center justify-center gap-2 rounded-md border border-input bg-card px-6 text-sm font-semibold text-foreground hover:bg-accent ${focusRing}`}
            >
              {t('landing.hero.chooseRole')}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>

          <p className="mt-6 flex items-start gap-2 text-small text-muted-foreground">
            <Languages className="mt-0.5 h-4 w-4 shrink-0 text-primary-text" aria-hidden="true" />
            <span>{t('landing.hero.languages')}</span>
          </p>
        </div>

        {/* Right: structured overview of who uses the platform */}
        <aside
          aria-labelledby="overview-title"
          className="rounded-lg border border-border bg-card lg:col-span-5"
        >
          <div className="border-b border-border px-5 py-4">
            <h2 id="overview-title" className="text-section-title font-semibold text-foreground">
              {t('landing.overview.title')}
            </h2>
            <p className="mt-1 text-small text-muted-foreground">{t('landing.overview.lead')}</p>
          </div>
          <ol className="divide-y divide-border">
            {TIERS.map((tier, i) => (
              <li key={tier.key} className="flex gap-4 px-5 py-4">
                <span
                  aria-hidden="true"
                  className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-primary-soft font-mono text-small font-semibold text-primary-text"
                >
                  {i + 1}
                </span>
                <div className="min-w-0">
                  <h3 className="text-body font-semibold text-foreground">
                    {t(`landing.tier.${tier.key}`)}
                  </h3>
                  <p className="text-small text-muted-foreground">{t(`landing.tier.${tier.key}.desc`)}</p>
                  <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-small text-foreground">
                    {tier.roles.map((code) => (
                      <li key={code} className="after:ml-3 after:text-border after:content-['|'] last:after:content-none">
                        {formatRoleName(code, t)}
                      </li>
                    ))}
                  </ul>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </Container>
    </section>
  );
};
