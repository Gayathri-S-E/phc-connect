import React, { useState, useEffect, useRef } from 'react';
import { Hospital, Globe2, Lock, Menu, X, ChevronDown } from 'lucide-react';
import { Container } from '../common/Container';
import { useLanguage } from '../../context/LanguageContext';

interface NavbarProps {
  onOpenLogin: () => void;
}

const NAV_LINKS = [
  { href: '#platform', labelKey: 'nav.dashboard', defaultLabel: 'Platform' },
  { href: '#roles', labelKey: 'role.patient', defaultLabel: 'Roles' },
  { href: '#workflow', labelKey: 'nav.activeWorkspace', defaultLabel: 'How It Connects' },
  { href: '#about', labelKey: 'app.subtitle', defaultLabel: 'Architecture' },
];

export const Navbar: React.FC<NavbarProps> = ({ onOpenLogin }) => {
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  /* Close on Escape */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  /* Lock body scroll */
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const close = () => setOpen(false);

  return (
    <>
      <header
        className="sticky top-0 z-50 border-b border-slate-200"
        style={{ backgroundColor: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(12px)' }}
      >
        <Container className="flex items-center justify-between h-16 lg:h-[72px] gap-4">

          {/* ── Zone 1: Logo ── */}
          <a href="#" className="flex items-center gap-3 shrink-0 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-sm shrink-0"
              style={{ background: 'linear-gradient(135deg, #5aa9e6 0%, #7fc8f8 100%)' }}
            >
              <Hospital className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-lg font-black tracking-tight text-slate-900 whitespace-nowrap">{t('app.title')}</span>
              <span
                className="hidden md:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider whitespace-nowrap"
                style={{ backgroundColor: '#f0f9ff', color: '#257bb5', border: '1px solid #7fc8f8' }}
              >
                Resilience Platform
              </span>
            </div>
          </a>

          {/* ── Zone 2: Desktop nav links ── */}
          <nav className="hidden lg:flex items-center gap-8 text-sm font-semibold text-slate-600" aria-label="Primary Navigation">
            {NAV_LINKS.map(({ href, defaultLabel }) => (
              <a
                key={href}
                href={href}
                className="hover:text-sky-600 transition-colors py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 rounded"
              >
                {defaultLabel}
              </a>
            ))}
          </nav>

          {/* ── Zone 3: Actions ── */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Trilingual Language Selector */}
            <div className="relative hidden sm:flex items-center">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as any)}
                aria-label={t('nav.language')}
                className="pl-8 pr-7 py-2 rounded-xl text-xs font-bold text-slate-700 border border-slate-200 bg-white hover:bg-slate-50 transition min-h-[38px] cursor-pointer appearance-none outline-none focus-visible:ring-2 focus-visible:ring-sky-500 shadow-2xs"
              >
                <option value="en">English</option>
                <option value="ta">தமிழ்</option>
                <option value="hi">हिन्दी</option>
              </select>
              <Globe2 className="w-3.5 h-3.5 text-sky-600 absolute left-2.5 pointer-events-none" />
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2.5 pointer-events-none" />
            </div>

            {/* Primary Sign In CTA */}
            <button
              onClick={onOpenLogin}
              aria-label={t('form.signIn')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold text-white transition shadow-sm hover:opacity-90 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
              style={{ backgroundColor: '#0284c7' }}
            >
              <Lock className="w-3.5 h-3.5 shrink-0" />
              <span>{t('form.signIn')}</span>
            </button>

            {/* Mobile hamburger (< lg) */}
            <button
              ref={triggerRef}
              onClick={() => setOpen(o => !o)}
              aria-expanded={open}
              aria-controls="mobile-nav"
              aria-label={t('nav.navigation')}
              className="lg:hidden inline-flex items-center justify-center w-10 h-10 rounded-xl text-slate-600 hover:bg-slate-100 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
            >
              {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </Container>
      </header>

      {/* ── Mobile Drawer ── */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50 flex flex-col" aria-modal="true" role="dialog" aria-label="Navigation">
          {/* Backdrop */}
          <div
            className="absolute inset-0"
            style={{ backgroundColor: 'rgba(15,23,42,0.6)', backdropFilter: 'blur(4px)' }}
            onClick={close}
          />
          {/* Panel */}
          <div
            ref={drawerRef}
            id="mobile-nav"
            className="relative w-full bg-white border-b border-slate-200 shadow-xl px-6 pt-5 pb-8 space-y-6"
          >
            <div className="flex items-center justify-between">
              <span className="text-base font-extrabold text-slate-900">{t('nav.navigation')}</span>
              <button
                onClick={close}
                aria-label={t('nav.closeMenu')}
                className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <nav className="flex flex-col gap-1">
              {NAV_LINKS.map(({ href, defaultLabel }) => (
                <a
                  key={href}
                  href={href}
                  onClick={close}
                  className="px-4 py-3 rounded-xl text-base font-semibold text-slate-700 hover:bg-slate-100 hover:text-sky-600 transition min-h-[48px] flex items-center"
                >
                  {defaultLabel}
                </a>
              ))}
            </nav>

            <div className="flex flex-col gap-3 pt-4 border-t border-slate-100">
              <div className="relative">
                <select
                  value={language}
                  onChange={(e) => { setLanguage(e.target.value as any); close(); }}
                  aria-label={t('nav.language')}
                  className="w-full pl-9 pr-8 py-3 rounded-xl font-bold text-sm text-slate-700 border border-slate-200 bg-white hover:bg-slate-50 transition min-h-[48px] appearance-none outline-none"
                >
                  <option value="en">English</option>
                  <option value="ta">தமிழ் (Tamil)</option>
                  <option value="hi">हिन्दी (Hindi)</option>
                </select>
                <Globe2 className="w-4 h-4 text-sky-600 absolute left-3 top-3.5 pointer-events-none" />
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3.5 pointer-events-none" />
              </div>
              <button
                onClick={() => { close(); onOpenLogin(); }}
                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-bold text-sm text-white transition min-h-[48px] shadow-sm"
                style={{ backgroundColor: '#0284c7' }}
              >
                <Lock className="w-4 h-4" />
                {t('form.signIn')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
