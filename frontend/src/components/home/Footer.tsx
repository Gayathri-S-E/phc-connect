import React from 'react';
import { Container } from '../common/Container';
import { MedLogo } from '../brand/MedLogo';
import { useLanguage } from '../../context/LanguageContext';

const LINKS = [
  { href: '#capabilities', labelKey: 'landing.nav.capabilities' },
  { href: '#roles', labelKey: 'landing.nav.roles' },
  { href: '#workflow', labelKey: 'landing.nav.workflow' },
];

export const Footer: React.FC = () => {
  const { t } = useLanguage();

  return (
    <footer id="about" className="border-t border-border bg-card">
      <Container className="grid gap-6 py-8 md:grid-cols-12 md:items-start">
        <div className="md:col-span-6">
          <MedLogo variant="full" size={28} />
          <p className="mt-3 text-small text-muted-foreground">{t('landing.footer.tagline')}</p>
          <p className="mt-1 text-small font-medium text-foreground">{t('landing.footer.org')}</p>
        </div>

        <nav aria-label={t('nav.navigation')} className="md:col-span-3">
          <ul className="space-y-2 text-small">
            {LINKS.map(({ href, labelKey }) => (
              <li key={href}>
                <a
                  href={href}
                  className="rounded-sm text-primary-text underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {t(labelKey)}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <p className="text-small text-muted-foreground md:col-span-3">{t('landing.footer.security')}</p>
      </Container>
    </footer>
  );
};
