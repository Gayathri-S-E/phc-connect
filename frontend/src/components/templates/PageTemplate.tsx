import React from 'react';
import { PageHeader, type PageHeaderProps } from '../ui/page-header';
import { SectionNav, type SectionNavItem } from './SectionNav';
import { cn } from '../../lib/utils';

export type PageWidth = 'full' | 'wide' | 'reading' | 'form';

const WIDTH_CLASS: Record<PageWidth, string> = {
  /** Uses the whole viewport (tables, dashboards). */
  full: '',
  /** Very wide monitors: stop growing at 1680px. */
  wide: 'max-w-[105rem]',
  /** Long-form text and records: comfortable line length. */
  reading: 'max-w-3xl',
  /** Forms: single column. */
  form: 'max-w-2xl',
};

export interface PageTemplateProps extends PageHeaderProps {
  /** Sub-views of this destination. Renders an underline SectionNav under the header. Use with useSectionParam(). */
  sections?: SectionNavItem[];
  section?: string;
  onSectionChange?: (key: string) => void;
  /** Accessible name for the section tabs. */
  sectionsLabel?: string;
  /** Right context column (>= xl); collapses below the main content on smaller screens. */
  rail?: React.ReactNode;
  /** Accessible name of the rail (aside landmark). */
  railLabel?: string;
  /** Max reading width of the MAIN column. Default `full`. The header always spans the whole width. */
  width?: PageWidth;
  children: React.ReactNode;
  /** Class for the content wrapper (below header and section tabs). */
  contentClassName?: string;
}

/**
 * Standard page: PageHeader (+ SectionNav) + main content (+ ContextRail).
 * The shell already provides padding and landmarks (<main>); do not add a container or max-w-7xl.
 */
export function PageTemplate({
  sections,
  section,
  onSectionChange,
  sectionsLabel,
  rail,
  railLabel,
  width = 'full',
  children,
  contentClassName,
  ...header
}: PageTemplateProps) {
  return (
    <div className="mx-auto w-full min-w-0">
      <PageHeader {...header} />
      {sections && sections.length > 0 && section !== undefined && onSectionChange && (
        <SectionNav items={sections} value={section} onChange={onSectionChange} label={sectionsLabel ?? header.title} />
      )}
      <div className={cn(rail ? 'grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_20rem] 2xl:grid-cols-[minmax(0,1fr)_22rem]' : '')}>
        <div className={cn('min-w-0 space-y-5', WIDTH_CLASS[width], contentClassName)}>{children}</div>
        {rail ? (
          <aside aria-label={railLabel ?? 'Context'} className="min-w-0 space-y-5 xl:sticky xl:top-0 xl:self-start">
            {rail}
          </aside>
        ) : null}
      </div>
    </div>
  );
}

export interface ContextRailSectionProps extends Omit<React.HTMLAttributes<HTMLElement>, 'title'> {
  title: React.ReactNode;
  /** Right-aligned small action (e.g. "View all"). */
  action?: React.ReactNode;
}

/**
 * One block inside the rail (selection details, next steps, related info). Flat: a bordered panel with a heading.
 * Do not nest cards inside it; use KeyValueList / lists.
 */
export function ContextRailSection({ title, action, className, children, ...props }: ContextRailSectionProps) {
  return (
    <section className={cn('rounded-lg border border-border bg-card', className)} {...props}>
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-2.5">
        <h2 className="text-small font-semibold text-foreground">{title}</h2>
        {action}
      </div>
      <div className="p-4 text-small">{children}</div>
    </section>
  );
}

/** Wrapper for several ContextRailSection blocks (optional; PageTemplate already spaces its `rail` children). */
export function ContextRail({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-5', className)} {...props} />;
}
