import React, { useId, useState } from 'react';
import { ChevronDown, Search, SlidersHorizontal, X } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { useLanguage } from '../../context/LanguageContext';
import { cn } from '../../lib/utils';

export interface FilterBarProps {
  search?: {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    /** Accessible label (defaults to the placeholder). */
    label?: string;
  };
  /** Filter controls (Select, toggle group ...). Collapsed behind a "Filters" button below md. */
  filters?: React.ReactNode;
  /** Right-aligned actions (export, refresh, add). */
  actions?: React.ReactNode;
  /** Number of active filters: shown on the mobile Filters button and enables the Clear button. */
  activeCount?: number;
  onClear?: () => void;
  /** "24 results" style text, announced politely to assistive tech. */
  resultText?: React.ReactNode;
  className?: string;
}

/** Search + filters + actions in one quiet row (no card). On small screens the filters collapse. */
export function FilterBar({ search, filters, actions, activeCount = 0, onClear, resultText, className }: FilterBarProps) {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const searchLabel = search?.label ?? search?.placeholder ?? t('table.search', 'Search records...');

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex flex-wrap items-center gap-2">
        {search && (
          <div className="relative min-w-0 flex-1 basis-56 sm:max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              value={search.value}
              onChange={(e) => search.onChange(e.target.value)}
              placeholder={search.placeholder ?? t('table.search', 'Search records...')}
              aria-label={searchLabel}
              className="pl-9"
            />
          </div>
        )}

        {filters && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-9 md:hidden"
            aria-expanded={open}
            aria-controls={panelId}
            onClick={() => setOpen((o) => !o)}
          >
            <SlidersHorizontal className="size-4" aria-hidden="true" />
            {t('table.filters', 'Filters')}
            {activeCount > 0 && (
              <span className="rounded-full bg-secondary px-1.5 text-caption font-semibold tabular-nums text-primary-text">{activeCount}</span>
            )}
            <ChevronDown className={cn('size-3.5 transition-transform', open && 'rotate-180')} aria-hidden="true" />
          </Button>
        )}

        {filters && <div className="hidden flex-wrap items-center gap-2 md:flex">{filters}</div>}

        {onClear && activeCount > 0 && (
          <Button type="button" variant="ghost" size="sm" className="h-9" onClick={onClear}>
            <X className="size-4" aria-hidden="true" />
            {t('table.clearFilters', 'Clear')}
          </Button>
        )}

        {actions && <div className="ml-auto flex flex-wrap items-center gap-2">{actions}</div>}
      </div>

      {filters && open && (
        <div id={panelId} className="flex flex-col gap-2 rounded-lg border border-border bg-card p-3 md:hidden">
          {filters}
        </div>
      )}

      {resultText ? (
        <p role="status" aria-live="polite" className="text-small text-muted-foreground">
          {resultText}
        </p>
      ) : null}
    </div>
  );
}
