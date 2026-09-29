import React, { useState, useEffect, useRef } from 'react';
import { Building2, Globe2, Lock, Menu, X } from 'lucide-react';
import { Container } from '../common/Container';
import { useLanguage } from '../../context/LanguageContext';

interface NavbarProps {
  onOpenLogin: () => void;
}

const NAV_LINKS = [
  { href: '#platform', label: 'Platform' },
  { href: '#roles', label: '13 Canonical Roles' },
  { href: '#workflow', label: 'How It Connects' },
  { href: '#about', label: 'Architecture' },
];

export const Navbar: React.FC<NavbarProps> = ({ onOpenLogin }) => {
  const { language, setLanguage } = useLanguage();
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
              style={{ background: 'linear-gradient(135deg, #0284c7 0%, #0d9488 100%)' }}
            >
              <Building2 className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-lg font-black tracking-tight text-slate-900 whitespace-nowrap">PHC CONNECT</span>
              <span
                className="hidden md:inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider whitespace-nowrap"
                style={{ backgroundColor: '#e0f2fe', color: '#0369a1' }}
              >
                Resilience Platform
              </span>
            </div>
          </a>

          {/* ── Zone 2: Desktop nav links ── */}
          <nav className="hidden lg:flex items-center gap-8 text-sm font-semibold text-slate-600" aria-label="Primary Navigation">
            {NAV_LINKS.map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="hover:text-sky-600 transition-colors py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 rounded"
              >
                {label}
              </a>
            ))}
          </nav>

          {/* ── Zone 3: Actions ── */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Language toggle */}
            <button
              onClick={() => setLanguage(language === 'en' ? 'ta' : 'en')}
              aria-label={`Switch to ${language === 'en' ? 'Tamil' : 'English'}`}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold text-slate-700 border border-slate-200 hover:bg-slate-50 transition min-h-[38px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
              style={{ backgroundColor: '#ffffff' }}
            >
              <Globe2 className="w-3.5 h-3.5 text-sky-600 shrink-0" />
              {language === 'en' ? 'தமிழ்' : 'English'}
            </button>

            {/* Primary Sign In CTA */}
            <button
              onClick={onOpenLogin}
              aria-label="Sign In to Portal"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold text-white transition shadow-sm hover:opacity-90 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
              style={{ backgroundColor: '#0284c7' }}
            >
              <Lock className="w-3.5 h-3.5 shrink-0" />
              <span>Sign In</span>
            </button>

            {/* Mobile hamburger (< lg) */}
            <button
              ref={triggerRef}
              onClick={() => setOpen(o => !o)}
              aria-expanded={open}
              aria-controls="mobile-nav"
              aria-label="Toggle navigation menu"
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
              <span className="text-base font-extrabold text-slate-900">Navigation</span>
              <button
                onClick={close}
                aria-label="Close menu"
                className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <nav className="flex flex-col gap-1">
              {NAV_LINKS.map(({ href, label }) => (
                <a
                  key={href}
                  href={href}
                  onClick={close}
                  className="px-4 py-3 rounded-xl text-base font-semibold text-slate-700 hover:bg-slate-100 hover:text-sky-600 transition min-h-[48px] flex items-center"
                >
                  {label}
                </a>
              ))}
            </nav>

            <div className="flex flex-col gap-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => { setLanguage(language === 'en' ? 'ta' : 'en'); close(); }}
                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-bold text-sm text-slate-700 border border-slate-200 hover:bg-slate-50 transition min-h-[48px]"
                style={{ backgroundColor: '#ffffff' }}
              >
                <Globe2 className="w-4 h-4 text-sky-600" />
                {language === 'en' ? 'Switch to தமிழ்' : 'Switch to English'}
              </button>
              <button
                onClick={() => { close(); onOpenLogin(); }}
                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-bold text-sm text-white transition min-h-[48px] shadow-sm"
                style={{ backgroundColor: '#0284c7' }}
              >
                <Lock className="w-4 h-4" />
                Sign In to Portal
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
