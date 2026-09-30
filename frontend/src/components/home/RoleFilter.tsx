import React, { useRef } from 'react';
import { useLanguage } from '../../context/LanguageContext';

export type RoleCategory = 'all' | 'clinical' | 'supply' | 'admin';

const TABS: RoleCategory[] = ['all', 'clinical', 'supply', 'admin'];

interface Props {
  selected: RoleCategory;
  counts: Record<RoleCategory, number>;
  onChange: (c: RoleCategory) => void;
  /** id of the element that shows the filtered roles (tabpanel). */
  panelId?: string;
}

export const tabId = (key: RoleCategory) => `role-filter-${key}`;

export const RoleFilter: React.FC<Props> = ({ selected, counts, onChange, panelId = 'role-panel' }) => {
  const { t } = useLanguage();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const move = (idx: number) => {
    const n = (idx + TABS.length) % TABS.length;
    onChange(TABS[n]);
    refs.current[n]?.focus();
  };

  const handleKey = (e: React.KeyboardEvent, idx: number) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); move(idx + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); move(idx - 1); }
    else if (e.key === 'Home') { e.preventDefault(); move(0); }
    else if (e.key === 'End') { e.preventDefault(); move(TABS.length - 1); }
  };

  return (
    <div
      role="tablist"
      aria-label={t('landing.roles.filter')}
      className="flex max-w-full items-end gap-1 overflow-x-auto border-b border-border no-scrollbar"
    >
      {TABS.map((key, idx) => {
        const active = selected === key;
        return (
          <button
            key={key}
            id={tabId(key)}
            ref={(el) => { refs.current[idx] = el; }}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={panelId}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(key)}
            onKeyDown={(e) => handleKey(e, idx)}
            className={`-mb-px flex shrink-0 cursor-pointer items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2.5 text-small font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              active
                ? 'border-primary-text text-primary-text'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t(`landing.cat.${key}`)}
            <span className="rounded-md bg-muted px-1.5 font-mono text-caption tabular-nums text-neutral-text">
              {counts[key]}
            </span>
          </button>
        );
      })}
    </div>
  );
};
