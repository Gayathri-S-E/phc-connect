import React, { useState, useEffect, useRef } from 'react';
import { Globe2, LogIn, Menu, X } from 'lucide-react';
import { Container } from '../common/Container';
import { MedLogo } from '../brand/MedLogo';
import { useLanguage } from '../../context/LanguageContext';

interface NavbarProps {
  onOpenLogin: () => void;
}

const NAV_LINKS = [
  { href: '#capabilities', labelKey: 'landing.nav.capabilities' },
  { href: '#roles', labelKey: 'landing.nav.roles' },
  { href: '#workflow', labelKey: 'landing.nav.workflow' },
];

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'ta', label: 'தமிழ்' },
  { value: 'hi', label: 'हिन्दी' },
];

const focusRing =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background';

export const Navbar: React.FC<NavbarProps> = ({ onOpenLogin }) => {
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  /* Close on Escape and return focus to the toggle */
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  const close = () => setOpen(false);

  const languageSelect = (id: string, className = '') => (
    <div className={`relative flex items-center ${className}`}>
      <Globe2 className="absolute left-2.5 h-4 w-4 text-primary-text pointer-events-none" aria-hidden="true" />
      <select
        id={id}
        value={language}
        onChange={(e) => setLanguage(e.target.value as 'en' | 'ta' | 'hi')}
        aria-label={t('nav.language')}
        className={`h-10 w-full cursor-pointer rounded-md border border-input bg-card pl-8 pr-3 text-sm font-medium text-foreground hover:bg-accent ${focusRing}`}
      >
        {LANGUAGE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card">
      <Container className="flex h-16 items-center justify-between gap-4">
        <a href="#top" className={`shrink-0 rounded-md ${focusRing}`} aria-label={`${t('app.title')} - ${t('app.subtitle')}`}>
          <MedLogo variant="full" size={32} />
        </a>

        <nav className="hidden items-center gap-1 lg:flex" aria-label={t('nav.navigation')}>
          {NAV_LINKS.map(({ href, labelKey }) => (
            <a
              key={href}
              href={href}
              className={`rounded-md px-3 py-2 text-small font-medium text-muted-foreground hover:bg-accent hover:text-foreground ${focusRing}`}
            >
              {t(labelKey)}
            </a>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          {languageSelect('landing-language', 'hidden w-32 sm:flex')}

          <button
            type="button"
            onClick={onOpenLogin}
            className={`inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary-hover ${focusRing}`}
          >
            <LogIn className="h-4 w-4" aria-hidden="true" />
            <span>{t('form.signIn')}</span>
          </button>

          <button
            type="button"
            ref={triggerRef}
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-controls="landing-mobile-nav"
            aria-label={open ? t('nav.closeMenu') : t('nav.navigation')}
            className={`inline-flex h-10 w-10 items-center justify-center rounded-md border border-input bg-card text-foreground hover:bg-accent lg:hidden ${focusRing}`}
          >
            {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
        </div>
      </Container>

      {/* Collapsible mobile navigation */}
      <div
        id="landing-mobile-nav"
        hidden={!open}
        className="border-t border-border bg-card lg:hidden"
      >
        <Container className="flex flex-col gap-1 py-3">
          <nav aria-label={t('nav.navigation')} className="flex flex-col">
            {NAV_LINKS.map(({ href, labelKey }) => (
              <a
                key={href}
                href={href}
                onClick={close}
                className={`flex min-h-11 items-center rounded-md px-3 text-base font-medium text-foreground hover:bg-accent ${focusRing}`}
              >
                {t(labelKey)}
              </a>
            ))}
          </nav>
          <div className="mt-2 border-t border-border pt-3 sm:hidden">
            {languageSelect('landing-language-mobile', 'w-full')}
          </div>
        </Container>
      </div>
    </header>
  );
};
