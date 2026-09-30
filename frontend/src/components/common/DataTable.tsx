import React, { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Inbox, Rows3, Search } from 'lucide-react';
import { StateView } from './StateView';
import { useLanguage } from '../../context/LanguageContext';
import { useMediaQuery } from '../layout/useMediaQuery';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { EmptyState } from '../ui/empty-state';
import { TableHeader, TableBody, TableHead, TableRow, TableCell } from '../ui/table';
import { cn } from '../../lib/utils';

export interface Column<T> {
  key?: string;
  header: string;
  accessor?: keyof T | string | ((row: T) => React.ReactNode);
  render?: (row: T) => React.ReactNode;
  width?: string;
  /** Click the header to sort (client-side). */
  sortable?: boolean;
  /** Value used for sorting when the cell is rendered JSX. Defaults to the raw field value. */
  sortValue?: (row: T) => string | number | null | undefined;
  align?: 'left' | 'right' | 'center';
  /** In the small-screen card list, hide this column (keep cards short). */
  hideOnMobile?: boolean;
}

export interface SortState {
  key: string;
  dir: 'asc' | 'desc';
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor?: (row: T) => string;
  keyField?: keyof T | string;
  searchable?: boolean;
  searchPlaceholder?: string;
  /** Custom search. When omitted, the search matches any primitive field of the row. */
  searchFilter?: (row: T, query: string) => boolean;
  isLoading?: boolean;
  /** Empty state: what is empty. */
  emptyTitle?: string;
  /** Empty state: why / what it is for. */
  emptyMessage?: string;
  /** Empty state: next action (a Button). */
  emptyAction?: React.ReactNode;
  pageSize?: number;
  /** Toolbar slot (right side of the search row). */
  actions?: React.ReactNode;
  /** Error state: shows StateView error with retry instead of the table. */
  errorMessage?: string | null;
  onRetry?: () => void;
  /** Extra per-row action slot, rendered in a trailing column (and at the bottom of each card on small screens). */
  rowActions?: (row: T) => React.ReactNode;
  rowActionsLabel?: string;
  onRowClick?: (row: T) => void;
  /** Sticky header while scrolling inside the table. Default true. */
  stickyHeader?: boolean;
  /** Max height of the scrolling table body area (CSS value). Default 70vh. */
  maxHeight?: string;
  density?: 'comfortable' | 'compact';
  /** Shows a comfortable/compact toggle in the toolbar. */
  densityToggle?: boolean;
  initialSort?: SortState;
  /** Accessible table name (visually hidden caption). */
  caption?: string;
  className?: string;
}

const colKeyOf = <T,>(col: Column<T>, idx: number) => col.key || (typeof col.accessor === 'string' ? col.accessor : String(idx));

function rawValue<T>(col: Column<T>, row: T): unknown {
  if (typeof col.accessor === 'function') return col.accessor(row);
  if (col.accessor) return (row as any)[col.accessor];
  if (col.key) return (row as any)[col.key];
  return undefined;
}

function cellContent<T>(col: Column<T>, row: T): React.ReactNode {
  if (col.render) return col.render(row);
  return rawValue(col, row) as React.ReactNode;
}

function sortKeyOf<T>(col: Column<T>, row: T): string | number | null {
  if (col.sortValue) return col.sortValue(row) ?? null;
  const v = rawValue(col, row);
  if (typeof v === 'number') return v;
  if (typeof v === 'string') return v;
  if (typeof v === 'boolean') return v ? 1 : 0;
  return null;
}

function defaultMatch(row: unknown, query: string): boolean {
  if (row && typeof row === 'object') {
    return Object.values(row as Record<string, unknown>).some(
      (v) => (typeof v === 'string' || typeof v === 'number') && String(v).toLowerCase().includes(query)
    );
  }
  return String(row).toLowerCase().includes(query);
}

const ALIGN = { left: 'text-left', right: 'text-right', center: 'text-center' } as const;

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  keyField,
  searchable = true,
  searchPlaceholder,
  searchFilter,
  isLoading = false,
  emptyTitle,
  emptyMessage,
  emptyAction,
  pageSize = 10,
  actions,
  errorMessage,
  onRetry,
  rowActions,
  rowActionsLabel,
  onRowClick,
  stickyHeader = true,
  maxHeight = '70vh',
  density: densityProp = 'comfortable',
  densityToggle = false,
  initialSort,
  caption,
  className,
}: DataTableProps<T>) {
  const { t } = useLanguage();
  const isTable = useMediaQuery('(min-width: 768px)', true);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sort, setSort] = useState<SortState | null>(initialSort ?? null);
  const [density, setDensity] = useState<'comfortable' | 'compact'>(densityProp);

  const filteredData = useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!searchable || !q) return data;
    return data.filter((row) => (searchFilter ? searchFilter(row, q) : defaultMatch(row, q)));
  }, [data, search, searchable, searchFilter]);

  const sortedData = useMemo(() => {
    if (!sort) return filteredData;
    const col = columns.find((c, i) => colKeyOf(c, i) === sort.key);
    if (!col) return filteredData;
    const dir = sort.dir === 'asc' ? 1 : -1;
    return [...filteredData].sort((a, b) => {
      const av = sortKeyOf(col, a);
      const bv = sortKeyOf(col, b);
      if (av === null && bv === null) return 0;
      if (av === null) return 1; // empty values last in both directions
      if (bv === null) return -1;
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
      return String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' }) * dir;
    });
  }, [filteredData, sort, columns]);

  if (isLoading) return <StateView state="loading" layout="table" />;
  if (errorMessage) return <StateView state="error" message={errorMessage} onRetry={onRetry} />;

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
  const page = Math.min(currentPage, totalPages);
  const start = (page - 1) * pageSize;
  const paginatedData = sortedData.slice(start, start + pageSize);

  const rowKeyOf = (row: T, rIdx: number) =>
    keyExtractor
      ? keyExtractor(row)
      : keyField && (row as any)[keyField] !== undefined
      ? String((row as any)[keyField])
      : (row as any)?.id || String(start + rIdx);

  const toggleSort = (key: string) =>
    setSort((prev) => (!prev || prev.key !== key ? { key, dir: 'asc' } : prev.dir === 'asc' ? { key, dir: 'desc' } : null));

  const cellPad = density === 'compact' ? 'py-1.5' : 'py-3';
  const showToolbar = searchable || actions || densityToggle;
  const hasRowActions = !!rowActions;
  const emptyText = emptyMessage || (search ? t('table.noResults', 'No results matched your search.') : t('table.emptyMessage', 'No data records found in this view.'));

  const empty = (
    <EmptyState
      icon={<Inbox />}
      title={emptyTitle || t('table.emptyTitle', 'No items to display')}
      why={emptyText}
      action={
        search ? (
          <Button variant="outline" size="sm" onClick={() => setSearch('')}>
            {t('table.clearSearch', 'Clear search')}
          </Button>
        ) : (
          emptyAction
        )
      }
    />
  );

  return (
    <div className={cn('flex w-full flex-col gap-3', className)}>
      {showToolbar && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          {searchable ? (
            <div className="relative w-full min-w-0 sm:max-w-sm sm:flex-1">
              <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" aria-hidden="true" />
              <Input
                type="search"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
                aria-label={searchPlaceholder || t('table.search', 'Search records...')}
                placeholder={searchPlaceholder || t('table.search', 'Search records...')}
                className="pl-9"
              />
            </div>
          ) : (
            <div />
          )}
          <div className="flex items-center gap-2 text-small text-muted-foreground">
            <span aria-live="polite">
              {t('table.total', 'Total')}: <strong className="font-semibold text-foreground tabular-nums">{sortedData.length}</strong>
            </span>
            {densityToggle && isTable && (
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-pressed={density === 'compact'}
                aria-label={t('table.compact', 'Compact rows')}
                title={t('table.compact', 'Compact rows')}
                onClick={() => setDensity((d) => (d === 'compact' ? 'comfortable' : 'compact'))}
              >
                <Rows3 className="size-4" aria-hidden="true" />
              </Button>
            )}
            {actions}
          </div>
        </div>
      )}

      {paginatedData.length === 0 ? (
        empty
      ) : isTable ? (
        <div
          className="relative w-full overflow-auto rounded-lg border border-border bg-card"
          style={stickyHeader ? { maxHeight } : undefined}
        >
          <table className="w-full caption-bottom text-small">
            {caption && <caption className="sr-only">{caption}</caption>}
            <TableHeader className={cn(stickyHeader && 'sticky top-0 z-10')}>
              <TableRow className="hover:bg-muted">
                {columns.map((col, idx) => {
                  const key = colKeyOf(col, idx);
                  const active = sort?.key === key;
                  const ariaSort = col.sortable ? (active ? (sort!.dir === 'asc' ? 'ascending' : 'descending') : 'none') : undefined;
                  return (
                    <TableHead
                      key={key}
                      style={{ width: col.width }}
                      aria-sort={ariaSort}
                      className={cn('bg-muted', ALIGN[col.align ?? 'left'], density === 'compact' && 'h-8')}
                    >
                      {col.sortable ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(key)}
                          className={cn(
                            '-mx-1 inline-flex cursor-pointer items-center gap-1 rounded-sm px-1 uppercase tracking-wide hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring',
                            active && 'text-foreground'
                          )}
                        >
                          {col.header}
                          {active ? (
                            sort!.dir === 'asc' ? <ArrowUp className="size-3.5" aria-hidden="true" /> : <ArrowDown className="size-3.5" aria-hidden="true" />
                          ) : (
                            <ArrowUpDown className="size-3.5 opacity-60" aria-hidden="true" />
                          )}
                        </button>
                      ) : (
                        col.header
                      )}
                    </TableHead>
                  );
                })}
                {hasRowActions && (
                  <TableHead className="bg-muted text-right">
                    <span className="sr-only">{rowActionsLabel || t('table.actions', 'Actions')}</span>
                  </TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.map((row, rIdx) => (
                <TableRow
                  key={rowKeyOf(row, rIdx)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(onRowClick && 'cursor-pointer')}
                >
                  {columns.map((col, cIdx) => (
                    <TableCell key={colKeyOf(col, cIdx)} className={cn(cellPad, ALIGN[col.align ?? 'left'])}>
                      {cellContent(col, row)}
                    </TableCell>
                  ))}
                  {hasRowActions && (
                    <TableCell className={cn(cellPad, 'text-right')} onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">{rowActions!(row)}</div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </table>
        </div>
      ) : (
        // Small screens: card list (one card per row, label/value pairs)
        <ul className="space-y-2">
          {paginatedData.map((row, rIdx) => {
            const visible = columns.filter((c) => !c.hideOnMobile);
            const [primary, ...rest] = visible;
            return (
              <li
                key={rowKeyOf(row, rIdx)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn('rounded-lg border border-border bg-card p-3', onRowClick && 'cursor-pointer')}
              >
                {primary && <div className="text-small font-semibold text-foreground">{cellContent(primary, row)}</div>}
                {rest.length > 0 && (
                  <dl className="mt-2 grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-x-3 gap-y-1.5 text-small">
                    {rest.map((col, cIdx) => (
                      <React.Fragment key={colKeyOf(col, cIdx)}>
                        <dt className="text-muted-foreground">{col.header}</dt>
                        <dd className="min-w-0 break-words text-foreground">{cellContent(col, row)}</dd>
                      </React.Fragment>
                    ))}
                  </dl>
                )}
                {hasRowActions && (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-2" onClick={(e) => e.stopPropagation()}>
                    {rowActions!(row)}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {/* Row count + pagination */}
      {sortedData.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 px-1 text-small">
          <span className="text-muted-foreground tabular-nums">
            {t('table.showing', 'Showing')} {start + 1}–{Math.min(start + pageSize, sortedData.length)} {t('table.of', 'of')} {sortedData.length}
          </span>
          {totalPages > 1 && (
            <nav aria-label={t('table.pagination', 'Pagination')} className="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setCurrentPage(Math.max(page - 1, 1))}
                aria-label={t('action.previous', 'Previous')}
              >
                <ChevronLeft className="size-4" aria-hidden="true" />
                <span className="hidden sm:inline">{t('action.previous', 'Previous')}</span>
              </Button>
              <span className="px-2 font-medium text-foreground tabular-nums">{t('table.pageOf', { page, total: totalPages })}</span>
              <Button
                variant="outline"
                size="sm"
                disabled={page === totalPages}
                onClick={() => setCurrentPage(Math.min(page + 1, totalPages))}
                aria-label={t('action.next', 'Next')}
              >
                <span className="hidden sm:inline">{t('action.next', 'Next')}</span>
                <ChevronRight className="size-4" aria-hidden="true" />
              </Button>
            </nav>
          )}
        </div>
      )}
    </div>
  );
}
