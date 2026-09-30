import React from 'react';
import { ChevronRight, Home, Shield, MapPin, Building2 } from 'lucide-react';
import { Badge, type BadgeProps } from './badge';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { formatRoleName, formatScopeLevel } from '../../utils/formatters';
import { useLanguage } from '../../context/LanguageContext';

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
  breadcrumbs?: BreadcrumbItem[];
  title: string;
  description?: string;
  badge?: React.ReactNode;
  scopeBadge?: BadgeInfo | React.ReactNode;
  roleBadge?: BadgeInfo | React.ReactNode;
  actions?: React.ReactNode;
  metrics?: MetricItem[];
  facilityContext?: string;
  className?: string;
}

export function PageHeader({
  breadcrumbs,
  title,
  description,
  badge,
  scopeBadge,
  roleBadge,
  actions,
  metrics,
  facilityContext,
  className,
}: PageHeaderProps) {
  const { activeRole, scope, user } = useAuth();
  const { t } = useLanguage();

  const renderBadge = (item?: BadgeInfo | React.ReactNode) => {
    if (!item) return null;
    if (React.isValidElement(item)) return item;
    if (typeof item === 'object' && 'label' in item) {
      return (
        <Badge variant={(item as BadgeInfo).variant || 'outline'}>
          {(item as BadgeInfo).label}
        </Badge>
      );
    }
    return null;
  };

  return (
    <div className={cn('flex flex-col gap-4 mb-6', className)}>
      {/* 1. Context Breadcrumbs & Scope Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-muted-foreground font-medium">
          <span className="flex items-center gap-1 text-muted-foreground hover:text-neutral-text">
            <Home className="w-3.5 h-3.5" />
            <span>Med2Us</span>
          </span>
          {breadcrumbs && breadcrumbs.length > 0 ? (
            breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                <ChevronRight className="w-3 h-3 text-muted-foreground" />
                {crumb.href || crumb.onClick ? (
                  <button
                    type="button"
                    onClick={crumb.onClick}
                    className="hover:text-primary-text transition-colors cursor-pointer"
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className="text-foreground font-semibold">{crumb.label}</span>
                )}
              </React.Fragment>
            ))
          ) : (
            <>
              <ChevronRight className="w-3 h-3 text-muted-foreground" />
              <span className="text-foreground font-semibold truncate max-w-xs">{title}</span>
            </>
          )}
        </nav>

        {/* Dynamic Scope & Role Context Pill */}
        <div className="flex items-center gap-2 flex-wrap">
          {scopeBadge ? (
            renderBadge(scopeBadge)
          ) : facilityContext ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-soft border border-neutral-border text-[11px] font-semibold text-neutral-text">
              <Building2 className="w-3 h-3 text-primary-text" />
              <span>{facilityContext}</span>
            </div>
          ) : scope ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-soft border border-neutral-border text-[11px] font-semibold text-neutral-text">
              <MapPin className="w-3 h-3 text-primary-text" />
              <span>{scope.toUpperCase()} SCOPE</span>
            </div>
          ) : null}

          {roleBadge ? (
            renderBadge(roleBadge)
          ) : activeRole ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-info-soft border border-info-border text-[11px] font-bold text-info-text">
              <Shield className="w-3 h-3 text-primary-text" />
              <span>{formatRoleName(activeRole, t)}</span>
            </div>
          ) : null}
        </div>
      </div>

      {/* 2. Main Title Row with Primary / Secondary Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-foreground leading-tight">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-xs sm:text-sm text-muted-foreground font-normal leading-relaxed max-w-3xl">
              {description}
            </p>
          )}
        </div>

        {actions && (
          <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
            {actions}
          </div>
        )}
      </div>

      {/* 3. Optional Context Metrics Strip */}
      {metrics && metrics.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          {metrics.map((m, idx) => (
            <div
              key={idx}
              className="p-3 bg-card rounded-xl border border-border shadow-2xs flex flex-col justify-between"
            >
              <div className="text-[11px] font-medium text-muted-foreground truncate">{m.label}</div>
              <div className="text-lg font-bold text-foreground mt-1 flex items-baseline gap-1.5">
                {m.icon && <span className="text-muted-foreground text-sm">{m.icon}</span>}
                <span>{m.value}</span>
              </div>
              {m.hint && <div className="text-[10px] text-muted-foreground mt-0.5">{m.hint}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
