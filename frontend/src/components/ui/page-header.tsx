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
        <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-slate-500 font-medium">
          <span className="flex items-center gap-1 text-slate-400 hover:text-slate-700">
            <Home className="w-3.5 h-3.5" />
            <span>Med2Us</span>
          </span>
          {breadcrumbs && breadcrumbs.length > 0 ? (
            breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                <ChevronRight className="w-3 h-3 text-slate-300" />
                {crumb.href || crumb.onClick ? (
                  <button
                    type="button"
                    onClick={crumb.onClick}
                    className="hover:text-sky-600 transition-colors cursor-pointer"
                  >
                    {crumb.label}
                  </button>
                ) : (
                  <span className="text-slate-800 font-semibold">{crumb.label}</span>
                )}
              </React.Fragment>
            ))
          ) : (
            <>
              <ChevronRight className="w-3 h-3 text-slate-300" />
              <span className="text-slate-800 font-semibold truncate max-w-xs">{title}</span>
            </>
          )}
        </nav>

        {/* Dynamic Scope & Role Context Pill */}
        <div className="flex items-center gap-2 flex-wrap">
          {scopeBadge ? (
            renderBadge(scopeBadge)
          ) : facilityContext ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-700">
              <Building2 className="w-3 h-3 text-sky-600" />
              <span>{facilityContext}</span>
            </div>
          ) : scope ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-[11px] font-semibold text-slate-700">
              <MapPin className="w-3 h-3 text-sky-600" />
              <span>{scope.toUpperCase()} SCOPE</span>
            </div>
          ) : null}

          {roleBadge ? (
            renderBadge(roleBadge)
          ) : activeRole ? (
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-50 border border-sky-200 text-[11px] font-bold text-sky-800">
              <Shield className="w-3 h-3 text-sky-600" />
              <span>{formatRoleName(activeRole, t)}</span>
            </div>
          ) : null}
        </div>
      </div>

      {/* 2. Main Title Row with Primary / Secondary Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-slate-900 leading-tight">
              {title}
            </h1>
            {badge && <div>{badge}</div>}
          </div>
          {description && (
            <p className="text-xs sm:text-sm text-slate-500 font-normal leading-relaxed max-w-3xl">
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
              className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between"
            >
              <div className="text-[11px] font-medium text-slate-500 truncate">{m.label}</div>
              <div className="text-lg font-bold text-slate-900 mt-1 flex items-baseline gap-1.5">
                {m.icon && <span className="text-slate-400 text-sm">{m.icon}</span>}
                <span>{m.value}</span>
              </div>
              {m.hint && <div className="text-[10px] text-slate-400 mt-0.5">{m.hint}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
