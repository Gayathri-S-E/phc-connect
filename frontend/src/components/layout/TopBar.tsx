import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, ChevronDown, Globe, LogOut, Menu, RefreshCw, Shield, Sparkles, UserRound } from 'lucide-react';
import { useAuth, DEMO_ACCOUNTS } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { formatRoleName } from '../../utils/formatters';
import { Button } from '../ui/button';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../ui/breadcrumb';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { cn } from '../../lib/utils';
import { useNavCatalogue } from './nav-catalogue';
import { useShell } from './ShellContext';

const LANGUAGES: { code: 'en' | 'ta' | 'hi'; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'hi', label: 'हिन्दी' },
];

const iconButton =
  'inline-flex h-9 items-center justify-center gap-1.5 rounded-md px-2 text-small font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring data-[state=open]:bg-accent';

/** Page location (section > page), derived from the route and the backend navigation catalogue. Never lists other destinations. */
const TopBreadcrumb: React.FC = () => {
  const { current } = useNavCatalogue();
  const { t } = useLanguage();
  return (
    <Breadcrumb aria-label={t('nav.breadcrumb', 'Breadcrumb')} className="min-w-0">
      <BreadcrumbList className="flex-nowrap">
        {current.sectionLabel && (
          <>
            <BreadcrumbItem className="hidden min-w-0 sm:inline-flex">
              <span className="truncate">{current.sectionLabel}</span>
            </BreadcrumbItem>
            <BreadcrumbSeparator className="hidden sm:inline-flex" />
          </>
        )}
        <BreadcrumbItem className="min-w-0">
          <BreadcrumbPage className="truncate">{current.pageLabel}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
};

export const TopBar: React.FC = () => {
  const { user, activeRole, scope, logout, switchDemoRole } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const { setMobileNavOpen, aiOpen, toggleAi } = useShell();
  const navigate = useNavigate();
  const [isSwitching, setIsSwitching] = useState(false);

  const handleRoleChange = async (roleKey: string) => {
    if (roleKey === activeRole) return;
    setIsSwitching(true);
    try {
      const res = await switchDemoRole(roleKey);
      if (res.success && res.path) navigate(res.path);
    } finally {
      setIsSwitching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const roleLabel = activeRole ? formatRoleName(activeRole, t) : t('nav.workspace', 'Authorized Portal');
  const facility = user?.facility_name || null;
  const displayName = user?.full_name || [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email || '';
  const initials =
    displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase())
      .join('') || 'U';
  const aiLabel = aiOpen ? t('ai.closeAssistant', 'Close AI Assistant') : t('ai.openAssistant', 'Open AI Assistant');

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-card px-3 sm:px-4">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={() => setMobileNavOpen(true)}
        aria-label={t('nav.navigation', 'Navigation')}
      >
        <Menu className="size-5" aria-hidden="true" />
      </Button>

      <div className="min-w-0 flex-1">
        <TopBreadcrumb />
      </div>

      {/* Role and scope context (not navigation) */}
      <div
        className="hidden min-w-0 max-w-[22rem] items-center gap-2 rounded-md border border-neutral-border bg-neutral-soft px-2.5 py-1 text-caption text-neutral-text lg:flex"
        title={facility ? `${roleLabel} - ${facility}` : roleLabel}
      >
        <Shield className="size-3.5 shrink-0 text-primary-text" aria-hidden="true" />
        <span className="truncate font-semibold">{roleLabel}</span>
        {(facility || scope) && (
          <span className="flex min-w-0 items-center gap-1 border-l border-neutral-border pl-2">
            {facility && <Building2 className="size-3.5 shrink-0" aria-hidden="true" />}
            <span className="truncate">{facility || `${String(scope).toUpperCase()} ${t('nav.scope', 'scope')}`}</span>
          </span>
        )}
      </div>

      {/* AI toggle */}
      <Button
        variant="outline"
        size="sm"
        onClick={toggleAi}
        aria-pressed={aiOpen}
        aria-label={aiLabel}
        className={cn('h-9 gap-1.5 px-2.5', aiOpen && 'border-ai-border bg-ai-soft text-ai-text hover:bg-ai-soft')}
      >
        <Sparkles className="size-4 text-ai-text" aria-hidden="true" />
        <span className="hidden sm:inline">{t('ai.short', 'AI')}</span>
      </Button>

      {/* Language */}
      <DropdownMenu>
        <DropdownMenuTrigger className={iconButton} aria-label={t('nav.language', 'Language')}>
          <Globe className="size-4" aria-hidden="true" />
          <span className="hidden text-caption font-semibold uppercase sm:inline">{language}</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{t('nav.language', 'Language')}</DropdownMenuLabel>
          <DropdownMenuRadioGroup value={language} onValueChange={(v) => setLanguage(v as 'en' | 'ta' | 'hi')}>
            {LANGUAGES.map((l) => (
              <DropdownMenuRadioItem key={l.code} value={l.code}>
                {l.label}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Account */}
      {user && (
        <DropdownMenu>
          <DropdownMenuTrigger
            className="inline-flex h-9 items-center gap-1.5 rounded-md pl-1 pr-1.5 text-muted-foreground transition-colors hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring data-[state=open]:bg-accent"
            aria-label={`${t('nav.account', 'Account')}: ${displayName}`}
          >
            <span
              aria-hidden="true"
              className="flex size-7 items-center justify-center rounded-full border border-info-border bg-info-soft text-caption font-semibold text-info-text"
            >
              {isSwitching ? <RefreshCw className="size-3.5 animate-spin" /> : initials}
            </span>
            <ChevronDown className="hidden size-3.5 sm:block" aria-hidden="true" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <div className="px-2 py-1.5">
              <p className="truncate text-small font-semibold text-foreground">{displayName}</p>
              <p className="truncate text-caption text-muted-foreground">{user.email}</p>
              <p className="mt-0.5 truncate text-caption text-muted-foreground">{roleLabel}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger disabled={isSwitching}>
                <UserRound aria-hidden="true" />
                {t('nav.switchRole', 'Switch Role (Demo)')}
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="max-h-80 w-72 overflow-y-auto">
                <DropdownMenuRadioGroup value={activeRole || ''} onValueChange={(v) => void handleRoleChange(v)}>
                  {Object.entries(DEMO_ACCOUNTS).map(([key, acc]) => (
                    <DropdownMenuRadioItem key={key} value={key}>
                      <span className="flex min-w-0 flex-col">
                        <span className="truncate font-medium">{acc.name}</span>
                        <span className="truncate text-caption text-muted-foreground">{formatRoleName(key, t)}</span>
                      </span>
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => void handleLogout()}>
              <LogOut aria-hidden="true" />
              {t('nav.logout', 'Sign Out')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </header>
  );
};
