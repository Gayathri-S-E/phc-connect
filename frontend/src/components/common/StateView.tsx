import React from 'react';
import { Loader2, AlertOctagon, ShieldAlert, FileQuestion, RefreshCw, Inbox, WifiOff } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

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
      <div
        role="status"
        aria-busy="true"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 1.5rem',
          color: 'var(--text-muted)',
          gap: '1rem',
        }}
      >
        <Loader2 size={36} className="animate-spin" style={{ color: 'var(--primary)' }} />
        <p style={{ fontSize: '0.95rem', fontWeight: 500 }}>{message || t('state.loading')}</p>
      </div>
    );
  }

  if (currentState === 'empty') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 1.5rem',
          textAlign: 'center',
          gap: '0.75rem',
          backgroundColor: 'rgba(241, 245, 249, 0.5)',
          borderRadius: '12px',
          border: '1px dashed var(--border-color)',
        }}
      >
        <Inbox size={40} style={{ color: 'var(--text-muted)', opacity: 0.6 }} />
        <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>{title || t('state.empty')}</h4>
        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '400px' }}>
          {message || 'No items available at this moment.'}
        </p>
        {actionText && onAction && (
          <button className="btn-primary" onClick={onAction} style={{ marginTop: '0.5rem' }}>
            {actionText}
          </button>
        )}
      </div>
    );
  }

  if (currentState === '403') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4rem 1.5rem',
          textAlign: 'center',
          gap: '1rem',
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#dc2626',
          }}
        >
          <ShieldAlert size={32} />
        </div>
        <h3 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700 }}>403 — {title || 'Access Restricted'}</h3>
        <p style={{ margin: 0, fontSize: '0.925rem', color: 'var(--text-muted)', maxWidth: '460px' }}>
          {message || t('state.forbidden')}
        </p>
        {onAction ? (
          <button className="btn-primary" onClick={onAction}>
            {actionText || 'Return to Dashboard'}
          </button>
        ) : null}
      </div>
    );
  }

  if (currentState === 'offline') {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '3rem 1.5rem',
          textAlign: 'center',
          gap: '0.75rem',
          backgroundColor: 'rgba(239, 68, 68, 0.05)',
          borderRadius: '12px',
          border: '1px solid rgba(239, 68, 68, 0.2)',
        }}
      >
        <WifiOff size={36} style={{ color: '#dc2626' }} />
        <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Connection Lost</h4>
        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {message || 'Unable to communicate with the server. Operating in offline cache mode.'}
        </p>
        {onRetry && (
          <button className="btn-secondary" onClick={onRetry} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <RefreshCw size={14} /> {t('state.retry')}
          </button>
        )}
      </div>
    );
  }

  // Error / 500 / Generic Error
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 1.5rem',
        textAlign: 'center',
        gap: '0.75rem',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        borderRadius: '12px',
        border: '1px solid rgba(239, 68, 68, 0.2)',
      }}
    >
      <AlertOctagon size={40} style={{ color: '#dc2626' }} />
      <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>{title || t('state.error')}</h4>
      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '450px' }}>
        {message || 'An unexpected problem occurred while processing this request.'}
      </p>
      {onRetry && (
        <button
          className="btn-primary"
          onClick={onRetry}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}
        >
          <RefreshCw size={14} /> {t('state.retry')}
        </button>
      )}
    </div>
  );
};
