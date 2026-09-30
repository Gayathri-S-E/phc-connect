import React, { useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { MedLogo } from '../brand/MedLogo';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../ui/sheet';
import { TooltipProvider } from '../ui/tooltip';
import { UnifiedAiAssistant } from '../ai/UnifiedAiAssistant';
import { ShellProvider, useShell } from './ShellContext';
import { SidebarContent, SidebarNav } from './SidebarNav';
import { TopBar } from './TopBar';

const MAIN_ID = 'main-content';

const ShellFrame: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { mobileNavOpen, setMobileNavOpen } = useShell();
  const { t } = useLanguage();
  const { pathname } = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const firstRender = useRef(true);

  // New page: reset scroll and move focus to the content region (keyboard and screen reader users start at the top).
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    const el = mainRef.current;
    if (el) {
      el.scrollTop = 0;
      el.focus({ preventScroll: true });
    }
  }, [pathname]);

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background font-sans text-foreground antialiased">
      <a
        href={`#${MAIN_ID}`}
        className="sr-only z-[100] rounded-md bg-card px-3 py-2 text-small font-semibold text-primary-text shadow-md focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
        onClick={(e) => {
          e.preventDefault();
          mainRef.current?.focus();
        }}
      >
        {t('nav.skipToContent', 'Skip to main content')}
      </a>

      <SidebarNav />

      {/* Mobile navigation: Sheet with its own focus trap and Escape handling */}
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent
          side="left"
          closeLabel={t('nav.closeMenu', 'Close Menu')}
          aria-describedby={undefined}
          className="w-72 max-w-[85vw] gap-0 bg-sidebar p-0 md:hidden"
        >
          <SheetHeader className="flex-row items-center border-sidebar-border p-0 px-4 py-3.5">
            <SheetTitle className="sr-only">{t('nav.navigation', 'Navigation')}</SheetTitle>
            <SheetDescription className="sr-only">{t('nav.workspace', 'Authorized Portal')}</SheetDescription>
            <Link to="/" onClick={() => setMobileNavOpen(false)} aria-label="Med2Us" className="rounded-md">
              <MedLogo variant="full" size={28} title="Med2Us" />
            </Link>
          </SheetHeader>
          <SidebarContent onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <div className="flex min-h-0 flex-1">
          <main
            ref={mainRef}
            id={MAIN_ID}
            tabIndex={-1}
            aria-label={t('nav.content', 'Main content')}
            className="min-w-0 flex-1 overflow-y-auto overflow-x-hidden px-4 py-5 outline-none sm:px-6 lg:px-8"
          >
            {children}
          </main>
          {/* Docked column on xl (shares the layout), bottom sheet below */}
          <UnifiedAiAssistant />
        </div>
      </div>
    </div>
  );
};

/** Authenticated application shell: SidebarNav + TopBar + content (+ docked AI panel). */
export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <TooltipProvider delayDuration={300}>
    <ShellProvider>
      <ShellFrame>{children}</ShellFrame>
    </ShellProvider>
  </TooltipProvider>
);

export default AppShell;
