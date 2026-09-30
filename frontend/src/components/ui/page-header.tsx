import React from 'react';
import { Building2, MapPin, Shield } from 'lucide-react';
import { Badge } from './badge';
import { Metric } from './metric';
import { cn } from '../../lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

export interface MetricItem {
  label: string;
  value: React.ReactNode;
  hint?: string;
  variant?: 'default' | 'success' | 'warning' | 'destructive' | 'sky';
  icon?: React.ReactNode;
}

export interface BadgeInfo {
  label: string;
  variant?: any;
}

export interface PageHeaderProps {
  /**
   * Optional in-page trail (e.g. a record under a list). The global "section > page" location is already shown in the
   * TopBar, so most pages should NOT pass this.
   */
  breadcrumbs?: BreadcrumbItem[];
  title: string;
  /** One-line purpose of the page (what this is for / what to do here). */
  description?: string;
  /** Legacy single badge beside the title. Prefer `chips`. */
  badge?: React.ReactNode;
  /** State chips (StatusBadge, etc.) shown beside the title: the page state at a glance. */
  chips?: React.ReactNode;
  /** Shown as a context chip. Role/scope are no longer added automatically (the TopBar shows them). */
  scopeBadge?: BadgeInfo | React.ReactNode;
  roleBadge?: BadgeInfo | React.ReactNode;
  facilityContext?: string;
  /** Legacy actions slot. Equivalent to `secondaryActions` + `primaryAction` rendered in order. */
  actions?: React.ReactNode;
  /** The single most important action on this page (one per page). Rendered last (rightmost). */
  primaryAction?: React.ReactNode;
  /** Other actions, rendered before the primary action. */
  secondaryActions?: React.ReactNode;
  /** Compact metric strip (single bordered panel, not a row of cards). */
  metrics?: MetricItem[];
  className?: string;
}

const METRIC_TONE: Record<NonNullable<MetricItem['variant']>, string> = {
  default: '',
  sky: '[&_dd:first-of-type]:text-primary-text',
  success: '[&_dd:first-of-type]:text-success-text',
  warning: '[&_dd:first-of-type]:text-warning-text',
  destructive: '[&_dd:first-of-type]:text-danger-text',
};

/** Compact page header: title, purpose, state chips, actions, optional metric strip. */
export function PageHeader({
  breadcrumbs,
  title,
  description,
  badge,
  chips,
  scopeBadge,
  roleBadge,
  actions,
  primaryAction,
  secondaryActions,
  metrics,
  facilityContext,
  className,
}: PageHeaderProps) {
  const renderBadge = (item?: BadgeInfo | React.ReactNode, icon?: React.ReactNode) => {
    if (!item) return null;
    if (React.isValidElement(item)) return item;
    if (typeof item === 'object' && 'label' in (item as object)) {
      return (
        <Badge variant={(item as BadgeInfo).variant || 'outline'} className="gap-1.5 rounded-md">
          {icon}
          {(item as BadgeInfo).label}
        </Badge>
      );
    }
    return null;
  };

  const contextChips = [
    facilityContext ? (
      <span key="facility" className="inline-flex items-center gap-1.5 rounded-md border border-neutral-border bg-neutral-soft px-2 py-0.5 text-caption font-medium text-neutral-text">
        <Building2 className="size-3.5 text-primary-text" aria-hidden="true" />
        {facilityContext}
      </span>
    ) : null,
    scopeBadge ? <React.Fragment key="scope">{renderBadge(scopeBadge, <MapPin className="size-3" aria-hidden="true" />)}</React.Fragment> : null,
    roleBadge ? <React.Fragment key="role">{renderBadge(roleBadge, <Shield className="size-3" aria-hidden="true" />)}</React.Fragment> : null,
  ].filter(Boolean);

  const hasChips = !!(badge || chips || contextChips.length);
  const hasActions = !!(actions || secondaryActions || primaryAction);

  return (
    <header className={cn('mb-5 flex flex-col gap-3', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" className="text-small text-muted-foreground">
          <ol className="flex flex-wrap items-center gap-1.5">
            {breadcrumbs.map((crumb, idx) => {
              const last = idx === breadcrumbs.length - 1;
              return (
                <li key={idx} className="inline-flex items-center gap-1.5">
                  {idx > 0 && <span aria-hidden="true">/</span>}
                  {crumb.href || crumb.onClick ? (
                    <button
                      type="button"
                      onClick={crumb.onClick}
                      className="cursor-pointer rounded-sm hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                    >
                      {crumb.label}
                    </button>
                  ) : (
                    <span aria-current={last ? 'page' : undefined} className={last ? 'font-medium text-foreground' : undefined}>
                      {crumb.label}
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
        </nav>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
            <h1 className="text-page-title text-foreground">{title}</h1>
            {hasChips && (
              <div className="flex flex-wrap items-center gap-1.5">
                {badge}
                {chips}
                {contextChips}
              </div>
            )}
          </div>
          {description && <p className="max-w-3xl text-small text-muted-foreground">{description}</p>}
        </div>

        {hasActions && (
          <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">
            {actions}
            {secondaryActions}
            {primaryAction}
          </div>
        )}
      </div>

      {metrics && metrics.length > 0 && (
        <div
          className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6"
          role="group"
          aria-label={title}
        >
          {metrics.map((m, idx) => (
            <Metric
              key={idx}
              label={m.label}
              value={m.value}
              hint={m.hint}
              icon={m.icon}
              className={cn('rounded-none border-0', METRIC_TONE[m.variant ?? 'default'])}
            />
          ))}
        </div>
      )}
    </header>
  );
}
