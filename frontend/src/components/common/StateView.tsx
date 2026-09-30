import React from 'react';
import { AlertOctagon, Clock, Inbox, LockKeyhole, RefreshCw, SearchX, ShieldAlert, WifiOff } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { Button } from '../ui/button';
import { Skeleton } from '../ui/skeleton';
import { EmptyState } from '../ui/empty-state';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { cn } from '../../lib/utils';

export type StateViewKind = 'loading' | 'empty' | 'error' | '401' | '403' | '404' | 'offline' | 'stale';

interface StateViewProps {
  state?: StateViewKind;
  type?: StateViewKind;
  /** empty: WHAT this is (e.g. "No appointments"). error/forbidden: the heading. */
  title?: string;
  /** empty: WHY it matters / what it is for. error: what happened. stale: extra detail. */
  message?: string;
  onRetry?: () => void;
  /** Next action (real actions only). For empty: primary call to action. For 403/401/404: navigation away. */
  actionText?: string;
  onAction?: () => void;
  /** stale: when the data was last refreshed (already formatted). */
  since?: string;
  /** loading: `page` = header + metrics + table skeleton (default); `inline` = a few lines; `table` = rows only. */
  layout?: 'page' | 'inline' | 'table';
  className?: string;
}

const Panel: React.FC<{ icon: React.ReactNode; title: string; body?: string; actions?: React.ReactNode; tone?: 'danger' | 'neutral'; className?: string }> = ({
  icon,
  title,
  body,
  actions,
  tone = 'neutral',
  className,
}) => (
  <div
    role={tone === 'danger' ? 'alert' : undefined}
    className={cn(
      'flex flex-col items-start gap-4 rounded-lg border bg-card p-6 animate-fade-in sm:flex-row sm:items-center',
      tone === 'danger' ? 'border-danger-border' : 'border-border',
      className
    )}
  >
    <div
      aria-hidden="true"
      className={cn(
        'flex size-10 shrink-0 items-center justify-center rounded-lg [&_svg]:size-5',
        tone === 'danger' ? 'bg-danger-soft text-danger-text' : 'bg-secondary text-primary-text'
      )}
    >
      {icon}
    </div>
    <div className="min-w-0 flex-1 space-y-1">
      <h2 className="text-section-title text-foreground">{title}</h2>
      {body && <p className="max-w-prose text-small text-muted-foreground">{body}</p>}
    </div>
    {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
  </div>
);

/**
 * One component for every data state: loading skeleton, empty (what + why + next), error with retry,
 * forbidden / signed-out / not found, offline, and a non-blocking stale-data notice.
 */
export const StateView: React.FC<StateViewProps> = ({
  state,
  type,
  title,
  message,
  onRetry,
  actionText,
  onAction,
  since,
  layout = 'page',
  className,
}) => {
  const { t } = useLanguage();
  const current: StateViewKind = state || type || 'loading';
  const retryButton = onRetry ? (
    <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
      <RefreshCw className="size-3.5" aria-hidden="true" />
      {t('state.retry', 'Retry')}
    </Button>
  ) : null;
  const actionButton = onAction ? (
    <Button variant="outline" size="sm" onClick={onAction}>
      {actionText}
    </Button>
  ) : null;

  if (current === 'loading') {
    const status = (
      <span className="sr-only">{message || t('state.loading', 'Loading')}</span>
    );
    if (layout === 'inline') {
      return (
        <div role="status" aria-busy="true" className={cn('w-full space-y-2 py-2 animate-fade-in', className)}>
          {status}
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-3/5" />
        </div>
      );
    }
    const table = (
      <div className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="border-b border-border bg-muted px-4 py-3">
          <Skeleton className="h-3.5 w-40 bg-border" />
        </div>
        <div className="divide-y divide-border">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="hidden h-4 w-1/6 sm:block" />
            </div>
          ))}
        </div>
      </div>
    );
    if (layout === 'table') {
      return (
        <div role="status" aria-busy="true" className={cn('w-full animate-fade-in', className)}>
          {status}
          {table}
        </div>
      );
    }
    return (
      <div role="status" aria-busy="true" className={cn('w-full space-y-5 py-1 animate-fade-in', className)}>
        {status}
        <div className="space-y-2">
          <Skeleton className="h-7 w-64 max-w-full" />
          <Skeleton className="h-4 w-96 max-w-full" />
        </div>
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="space-y-2 bg-card p-3">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </div>
        {table}
      </div>
    );
  }

  if (current === 'empty') {
    return (
      <EmptyState
        className={cn('animate-fade-in', className)}
        icon={<Inbox />}
        title={title || t('state.empty', 'No records found in this view.')}
        why={message}
        action={
          onAction && actionText ? (
            <Button variant="outline" size="sm" onClick={onAction}>
              {actionText}
            </Button>
          ) : undefined
        }
      />
    );
  }

  if (current === 'stale') {
    return (
      <Alert variant="warning" role="status" className={cn('animate-fade-in', className)}>
        <AlertTitle className="flex items-center gap-1.5 text-warning-text">
          <Clock className="size-4" aria-hidden="true" />
          {title || t('state.stale', 'This data may be out of date')}
        </AlertTitle>
        <AlertDescription className="flex flex-wrap items-center justify-between gap-2 text-warning-text">
          <span>
            {message || t('state.staleMessage', 'Showing the last information received.')}
            {since ? ` ${t('state.lastUpdated', 'Last updated')}: ${since}.` : ''}
          </span>
          {retryButton}
        </AlertDescription>
      </Alert>
    );
  }

  if (current === '403') {
    return (
      <Panel
        className={className}
        icon={<ShieldAlert />}
        title={title || t('state.accessRestricted', 'Access Restricted')}
        body={message || t('state.forbidden', 'You do not have the required permissions.')}
        actions={actionButton ?? undefined}
      />
    );
  }

  if (current === '401') {
    return (
      <Panel
        className={className}
        icon={<LockKeyhole />}
        title={title || t('state.sessionExpired', 'Session expired')}
        body={message || t('state.sessionExpiredMessage', 'Please sign in again to continue.')}
        actions={actionButton ?? undefined}
      />
    );
  }

  if (current === '404') {
    return (
      <Panel
        className={className}
        icon={<SearchX />}
        title={title || t('state.notFound', 'Not found')}
        body={message || t('state.notFoundMessage', 'This record or page does not exist or was moved.')}
        actions={actionButton ?? undefined}
      />
    );
  }

  if (current === 'offline') {
    return (
      <Panel
        className={className}
        icon={<WifiOff />}
        title={title || t('state.connectionLost', 'Connection Lost')}
        body={message || t('state.offlineMessage', 'Unable to reach the server. Check your connection.')}
        actions={retryButton ?? undefined}
      />
    );
  }

  // error
  return (
    <Panel
      tone="danger"
      className={className}
      icon={<AlertOctagon />}
      title={title || t('state.error', 'Unable to complete request.')}
      body={message || t('state.errorMessage', 'Something went wrong while loading this. Your data is unchanged. Try again.')}
      actions={
        <>
          {retryButton}
          {actionButton}
        </>
      }
    />
  );
};
