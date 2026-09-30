import React from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { formatRoleName } from '../../utils/formatters';
import { useLanguage } from '../../context/LanguageContext';

interface Props {
  code: string;
  index: number;
  account: { email: string; name: string; role: string; defaultPath: string };
  category: 'clinical' | 'supply' | 'admin';
  icon: React.ReactNode;
  isDisabled?: boolean;
  isLoading?: boolean;
  onSelect: (code: string) => void;
}

export const RoleCard: React.FC<Props> = ({
  code, index, account, category, icon, isDisabled = false, isLoading = false, onSelect,
}) => {
  const { t } = useLanguage();
  const roleName = formatRoleName(code, t);

  return (
    <button
      type="button"
      onClick={() => onSelect(code)}
      disabled={isDisabled}
      aria-busy={isLoading}
      aria-label={t('landing.signInAs', { role: roleName })}
      className="group flex h-full w-full cursor-pointer flex-col rounded-lg border border-border bg-card p-4 text-left hover:border-primary-text hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-60"
    >
      <div className="flex w-full items-start gap-3">
        <span
          aria-hidden="true"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-primary-soft text-primary-text"
        >
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-body font-semibold leading-snug text-foreground">{roleName}</h3>
          <p className="mt-0.5 text-caption text-muted-foreground">
            <span className="font-mono">{String(index + 1).padStart(2, '0')}</span>
            <span aria-hidden="true"> · </span>
            {t(`landing.cat.${category}`)}
          </p>
        </div>
      </div>

      <p className="mb-4 mt-3 text-small leading-relaxed text-muted-foreground">
        {t(`landing.roleDesc.${code}`, account.name)}
      </p>

      <div className="mt-auto flex w-full items-center justify-between gap-2 border-t border-border pt-3">
        <span className="min-w-0 truncate font-mono text-caption text-muted-foreground" title={account.email}>
          {account.email}
        </span>
        <span className="flex shrink-0 items-center gap-1 text-small font-semibold text-primary-text">
          {isLoading ? t('landing.signingIn') : t('landing.openWorkspace')}
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5" aria-hidden="true" />
          )}
        </span>
      </div>
    </button>
  );
};
