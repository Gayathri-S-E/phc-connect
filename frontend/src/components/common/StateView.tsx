import React from 'react';
import { AlertOctagon, ShieldAlert, Inbox, WifiOff, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { Button } from '../ui/button';
import { Skeleton } from '../ui/skeleton';

interface StateViewProps {
  state?: 'loading' | 'empty' | 'error' | '401' | '403' | '404' | 'offline';
  type?: 'loading' | 'empty' | 'error' | '401' | '403' | '404' | 'offline';
  title?: string;
  message?: string;
  onRetry?: () => void;
  actionText?: string;
  onAction?: () => void;
}

export const StateView: React.FC<StateViewProps> = ({
  state,
  type,
  title,
  message,
  onRetry,
  actionText,
  onAction,
}) => {
  const { t } = useLanguage();
  const currentState = state || type || 'loading';

  if (currentState === 'loading') {
    return (
      <div role="status" aria-busy="true" className="w-full space-y-6 py-4 animate-fade-in">
        <span className="sr-only">{message || t('state.loading')}</span>
        {/* Page heading */}
        <div className="space-y-2">
          <Skeleton className="h-7 w-64 max-w-full" />
          <Skeleton className="h-4 w-96 max-w-full" />
        </div>
        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-3 w-32" />
            </div>
          ))}
        </div>
        {/* Table */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
          <Skeleton className="h-5 w-40" />
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-9 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (currentState === 'empty') {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center gap-3 bg-slate-50/70 rounded-2xl border border-dashed border-slate-300 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-white border border-slate-200 flex items-center justify-center text-slate-400 shadow-2xs">
          <Inbox className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h4 className="text-base font-bold text-slate-900">{title || t('state.empty')}</h4>
          <p className="text-xs text-slate-500 max-w-md leading-relaxed">
            {message || 'No items available at this moment. New records will appear here as they are processed.'}
          </p>
        </div>
        {actionText && onAction && (
          <Button variant="primary" size="sm" onClick={onAction} className="mt-2">
            {actionText}
          </Button>
        )}
      </div>
    );
  }

  if (currentState === '403') {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-6 text-center gap-4 bg-red-50/40 rounded-2xl border border-red-200 animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center shadow-xs">
          <ShieldAlert className="w-7 h-7" />
        </div>
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-slate-900">403 — {title || 'Access Restricted'}</h3>
          <p className="text-xs text-slate-600 max-w-md leading-relaxed">
            {message || t('state.forbidden')}
          </p>
        </div>
        {onAction && (
          <Button variant="outline" size="sm" onClick={onAction}>
            {actionText || 'Return to Authorized Dashboard'}
          </Button>
        )}
      </div>
    );
  }

  if (currentState === 'offline') {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center gap-3 bg-amber-50/50 rounded-2xl border border-amber-200 animate-fade-in">
        <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shadow-2xs">
          <WifiOff className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h4 className="text-base font-bold text-amber-950">Connection Interrupted</h4>
          <p className="text-xs text-amber-800/80 max-w-md leading-relaxed">
            {message || 'Unable to communicate with the health network server. Local offline caching active.'}
          </p>
        </div>
        {onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw className="w-3.5 h-3.5" />
            {t('state.retry')}
          </Button>
        )}
      </div>
    );
  }

  // Error / Generic
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center gap-3 bg-red-50/50 rounded-2xl border border-red-200 animate-fade-in">
      <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center shadow-2xs">
        <AlertOctagon className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <h4 className="text-base font-bold text-red-950">{title || t('state.error')}</h4>
        <p className="text-xs text-red-800/80 max-w-md leading-relaxed">
          {message || 'An unexpected problem occurred while processing this health record.'}
        </p>
      </div>
      {onRetry && (
        <Button variant="primary" size="sm" onClick={onRetry} className="gap-2 mt-1">
          <RefreshCw className="w-3.5 h-3.5" />
          {t('state.retry')}
        </Button>
      )}
    </div>
  );
};
