import React, { useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { cn } from '../../lib/utils';

export interface SectionNavItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  /** Small count badge (e.g. open items). Omit when zero is not interesting. */
  count?: number;
  disabled?: boolean;
}

export interface SectionNavProps {
  items: SectionNavItem[];
  value: string;
  onChange: (key: string) => void;
  /** Accessible name of the tab list (e.g. "Patient sections"). */
  label?: string;
  /** Prefix used for element ids so SectionPanel can reference its tab. Must match SectionPanel `id`. */
  id?: string;
  className?: string;
}

/**
 * Underline section tabs for sub-views of the current destination (NOT for global destinations: those live in the
 * sidebar). Keyboard: Left/Right (and Home/End) move between tabs; horizontally scrollable on small screens.
 * Pair with useSectionParam() so the active section lives in the URL.
 */
export function SectionNav({ items, value, onChange, label, id = 'section', className }: SectionNavProps) {
  const listRef = useRef<HTMLDivElement>(null);

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const enabled = items.filter((i) => !i.disabled);
    const idx = enabled.findIndex((i) => i.key === value);
    let next: SectionNavItem | undefined;
    if (e.key === 'ArrowRight') next = enabled[(idx + 1) % enabled.length];
    else if (e.key === 'ArrowLeft') next = enabled[(idx - 1 + enabled.length) % enabled.length];
    else if (e.key === 'Home') next = enabled[0];
    else if (e.key === 'End') next = enabled[enabled.length - 1];
    if (!next) return;
    e.preventDefault();
    onChange(next.key);
    requestAnimationFrame(() => {
      listRef.current?.querySelector<HTMLElement>(`[data-key="${CSS.escape(next!.key)}"]`)?.focus();
    });
  };

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={label}
      onKeyDown={onKeyDown}
      className={cn('no-scrollbar mb-5 flex max-w-full items-center gap-1 overflow-x-auto border-b border-border', className)}
    >
      {items.map((item) => {
        const active = item.key === value;
        return (
          <button
            key={item.key}
            type="button"
            role="tab"
            id={`${id}-tab-${item.key}`}
            data-key={item.key}
            aria-selected={active}
            aria-controls={`${id}-panel-${item.key}`}
            tabIndex={active ? 0 : -1}
            disabled={item.disabled}
            onClick={() => onChange(item.key)}
            className={cn(
              '-mb-px inline-flex shrink-0 cursor-pointer select-none items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2 text-small transition-colors',
              'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50',
              active
                ? 'border-primary-text font-semibold text-foreground'
                : 'border-transparent font-medium text-muted-foreground hover:text-foreground'
            )}
          >
            {item.icon ? <span aria-hidden="true" className="[&_svg]:size-4">{item.icon}</span> : null}
            <span>{item.label}</span>
            {typeof item.count === 'number' && (
              <span className="min-w-5 rounded-full bg-muted px-1.5 text-center text-caption font-semibold tabular-nums text-neutral-text">
                {item.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export interface SectionPanelProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'id'> {
  /** Same `id` as the SectionNav. */
  id?: string;
  /** Key of this section. */
  section: string;
  /** Currently active section (value of the SectionNav). The panel renders only when they match. */
  active: string;
}

/** Tab panel for a section; renders nothing unless active. Gives the content the right ARIA wiring. */
export function SectionPanel({ id = 'section', section, active, className, children, ...props }: SectionPanelProps) {
  if (section !== active) return null;
  return (
    <div
      role="tabpanel"
      id={`${id}-panel-${section}`}
      aria-labelledby={`${id}-tab-${section}`}
      tabIndex={0}
      className={cn('animate-fade-in focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring', className)}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * URL-driven section state: stores the active section in the `?section=` search param so deep links and the browser
 * back button work. The default key is represented by the ABSENCE of the param (clean URLs).
 *
 *   const [section, setSection] = useSectionParam('appointments', ['appointments', 'records']);
 */
export function useSectionParam(defaultKey: string, validKeys?: readonly string[], param = 'section') {
  const [params, setParams] = useSearchParams();
  const raw = params.get(param);
  const section = raw && (!validKeys || validKeys.includes(raw)) ? raw : defaultKey;

  const setSection = useCallback(
    (key: string) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (key === defaultKey) next.delete(param);
          else next.set(param, key);
          return next;
        },
        { replace: false }
      );
    },
    [setParams, defaultKey, param]
  );

  return [section, setSection] as const;
}
