import React, { useState } from 'react';
import { Search, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { StateView } from './StateView';
import { useLanguage } from '../../context/LanguageContext';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '../ui/table';

export interface Column<T> {
  key?: string;
  header: string;
  accessor?: keyof T | string | ((row: T) => React.ReactNode);
  render?: (row: T) => React.ReactNode;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor?: (row: T) => string;
  keyField?: keyof T | string;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchFilter?: (row: T, query: string) => boolean;
  isLoading?: boolean;
  emptyTitle?: string;
  emptyMessage?: string;
  pageSize?: number;
  actions?: React.ReactNode;
}

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
  pageSize = 10,
  actions,
}: DataTableProps<T>) {
  const { t } = useLanguage();
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  if (isLoading) {
    return <StateView state="loading" />;
  }

  const filteredData =
    searchable && search.trim() && searchFilter
      ? data.filter((row) => searchFilter(row, search.toLowerCase().trim()))
      : data;

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const paginatedData = filteredData.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="flex flex-col gap-3 w-full">
      {/* Search & Actions Header */}
      {(searchable || actions) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {searchable ? (
            <div className="relative w-full max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
              <Input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder={searchPlaceholder || t('table.search') || 'Filter records...'}
                className="pl-9 h-9 text-xs"
              />
            </div>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-3 self-end sm:self-auto text-xs text-slate-500 font-medium">
            <span>
              {t('table.total') || 'Total records'}: <strong className="text-slate-800 font-bold">{filteredData.length}</strong>
            </span>
            {actions}
          </div>
        </div>
      )}

      {/* Table Surface */}
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col, idx) => (
              <TableHead
                key={col.key || (typeof col.accessor === 'string' ? col.accessor : String(idx))}
                style={{ width: col.width }}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {paginatedData.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="p-8 text-center">
                <StateView
                  state="empty"
                  title={emptyTitle || t('table.emptyTitle')}
                  message={
                    emptyMessage ||
                    (search ? t('table.noResults') || 'No records matched your search query.' : t('table.emptyMessage'))
                  }
                />
              </TableCell>
            </TableRow>
          ) : (
            paginatedData.map((row, rIdx) => {
              const rowKey = keyExtractor
                ? keyExtractor(row)
                : keyField && (row as any)[keyField] !== undefined
                ? String((row as any)[keyField])
                : (row as any).id || String(rIdx);

              return (
                <TableRow key={rowKey}>
                  {columns.map((col, cIdx) => {
                    const colKey =
                      col.key ||
                      (typeof col.accessor === 'string' ? col.accessor : String(cIdx));
                    let content: React.ReactNode = null;
                    if (col.render) {
                      content = col.render(row);
                    } else if (typeof col.accessor === 'function') {
                      content = col.accessor(row);
                    } else if (col.accessor) {
                      content = (row as any)[col.accessor];
                    } else if (col.key) {
                      content = (row as any)[col.key];
                    }

                    return <TableCell key={colKey}>{content}</TableCell>;
                  })}
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between gap-3 px-1 py-1 text-xs">
          <span className="text-slate-500 font-medium">
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filteredData.length)} of {filteredData.length} records
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              aria-label={t('action.previous')}
              className="h-8 px-2.5 text-xs"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <span className="px-2 font-semibold text-slate-700">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              aria-label={t('action.next')}
              className="h-8 px-2.5 text-xs"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
