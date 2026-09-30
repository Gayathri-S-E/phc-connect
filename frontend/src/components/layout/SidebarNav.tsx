import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { MedLogo } from '../brand/MedLogo';
import { Skeleton } from '../ui/skeleton';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';
import { cn } from '../../lib/utils';
import { NAV_ICONS, useNavCatalogue } from './nav-catalogue';
import { useShell } from './ShellContext';

interface SidebarContentProps {
  /** Icon rail: icons only, labels in tooltips. */
  rail?: boolean;
  onNavigate?: () => void;
}

/** Global destinations grouped by section. Exactly one item is marked active (aria-current="page"). */
export const SidebarContent: React.FC<SidebarContentProps> = ({ rail = false, onNavigate }) => {
  const { groups, current } = useNavCatalogue();
  const { navItems } = useAuth();
  const { t } = useLanguage();

  return (
    <nav aria-label={t('nav.navigation', 'Navigation')} className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3">
      {navItems.length === 0 ? (
        <div className="space-y-2 px-1" role="status" aria-busy="true">
          <span className="sr-only">{t('state.loading', 'Loading')}</span>
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className={cn('h-8', rail ? 'w-8' : 'w-full')} />
          ))}
        </div>
      ) : (
        <ul className="space-y-5">
          {groups.map((group, gi) => (
            <li key={group.sectionKey}>
              {rail ? (
                gi > 0 && <div role="presentation" className="mx-2 mb-3 border-t border-sidebar-border" />
              ) : (
                <div className="mb-1 px-3 text-caption font-semibold uppercase tracking-wide text-muted-foreground">
                  {group.label}
                </div>
              )}
              <ul className="space-y-0.5" aria-label={rail ? group.label : undefined}>
                {group.items.map((item) => {
                  const Icon = NAV_ICONS[item.icon] ?? Activity;
                  const active = current.entry?.path === item.path;
                  const link = (
                    <Link
                      to={item.path}
                      onClick={onNavigate}
                      aria-current={active ? 'page' : undefined}
                      aria-label={rail ? item.label : undefined}
                      className={cn(
                        'relative flex items-center gap-3 rounded-md px-3 py-2 text-small transition-colors',
                        'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring',
                        rail && 'justify-center px-0',
                        active
                          ? 'bg-sidebar-accent font-semibold text-sidebar-accent-foreground'
                          : 'font-medium text-muted-foreground hover:bg-accent hover:text-foreground'
                      )}
                    >
                      {active && (
                        <span aria-hidden="true" className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-primary-text" />
                      )}
                      <Icon className={cn('size-4 shrink-0', active && 'text-primary-text')} aria-hidden={true} />
                      {!rail && <span className="truncate">{item.label}</span>}
                    </Link>
                  );
                  return (
                    <li key={item.path}>
                      {rail ? (
                        <Tooltip>
                          <TooltipTrigger asChild>{link}</TooltipTrigger>
                          <TooltipContent side="right">{item.label}</TooltipContent>
                        </Tooltip>
                      ) : (
                        link
                      )}
                    </li>
                  );
                })}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
};

/** Desktop sidebar (md and up): expanded on lg by default, collapsible to an icon rail. Hidden below md (Sheet in AppShell). */
export const SidebarNav: React.FC = () => {
  const { navCollapsed, toggleNavCollapsed } = useShell();
  const { t } = useLanguage();
  const label = navCollapsed ? t('nav.expand', 'Expand navigation') : t('nav.collapse', 'Collapse navigation');

  return (
    <aside
      aria-label={t('nav.navigation', 'Navigation')}
      className={cn(
        'hidden shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground md:flex',
        navCollapsed ? 'w-14' : 'w-60'
      )}
    >
      <div className={cn('flex h-14 shrink-0 items-center border-b border-sidebar-border', navCollapsed ? 'justify-center' : 'px-4')}>
        <Link
          to="/"
          aria-label="Med2Us"
          className="rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <MedLogo variant={navCollapsed ? 'mark' : 'full'} size={navCollapsed ? 28 : 30} title="Med2Us" />
        </Link>
      </div>
      <SidebarContent rail={navCollapsed} />
      <div className={cn('flex shrink-0 border-t border-sidebar-border p-2', navCollapsed ? 'justify-center' : 'justify-end')}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={toggleNavCollapsed}
              aria-label={label}
              aria-expanded={!navCollapsed}
              className="inline-flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              {navCollapsed ? <PanelLeftOpen className="size-4" aria-hidden="true" /> : <PanelLeftClose className="size-4" aria-hidden="true" />}
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">{label}</TooltipContent>
        </Tooltip>
      </div>
    </aside>
  );
};
