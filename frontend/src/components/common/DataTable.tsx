import React, { useState } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { StateView } from './StateView';
import { useLanguage } from '../../context/LanguageContext';

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
}: DataTableProps<T>) {
  const { t } = useLanguage();
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  if (isLoading) {
    return <StateView state="loading" />;
  }

  const filteredData = searchable && search.trim() && searchFilter
    ? data.filter((row) => searchFilter(row, search.toLowerCase().trim()))
    : data;

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const paginatedData = filteredData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%' }}>
      {/* Search Header */}
      {searchable && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: '340px',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '0.85rem',
                color: 'var(--text-muted)',
              }}
            />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder={searchPlaceholder || t('table.search')}
              style={{
                width: '100%',
                padding: '0.55rem 0.85rem 0.55rem 2.25rem',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                fontSize: '0.875rem',
                outline: 'none',
              }}
            />
          </div>
          <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            {t('table.total')}: <strong>{filteredData.length}</strong>
          </span>
        </div>
      )}

      {/* Table Container */}
      <div
        style={{
          overflowX: 'auto',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          backgroundColor: '#ffffff',
        }}
      >
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '0.875rem',
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: 'rgba(248, 250, 252, 0.9)',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              {columns.map((col, idx) => (
                <th
                  key={col.key || (typeof col.accessor === 'string' ? col.accessor : String(idx))}
                  style={{
                    padding: '0.85rem 1rem',
                    fontWeight: 600,
                    color: 'var(--text-muted)',
                    width: col.width,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ padding: '2rem 1rem' }}>
                  <StateView
                    state="empty"
                    title={emptyTitle || t('table.emptyTitle')}
                    message={emptyMessage || (search ? t('table.noResults') : t('table.emptyMessage'))}
                  />
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rIdx) => {
                const rowKey = keyExtractor
                  ? keyExtractor(row)
                  : keyField && (row as any)[keyField] !== undefined
                  ? String((row as any)[keyField])
                  : (row as any).id || String(rIdx);

                return (
                  <tr
                    key={rowKey}
                    style={{
                      borderBottom: '1px solid rgba(226, 232, 240, 0.6)',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(241, 245, 249, 0.5)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    {columns.map((col, cIdx) => {
                      const colKey = col.key || (typeof col.accessor === 'string' ? col.accessor : String(cIdx));
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

                      return (
                        <td
                          key={colKey}
                          style={{
                            padding: '0.85rem 1rem',
                            color: 'var(--text-main)',
                            verticalAlign: 'middle',
                          }}
                        >
                          {content}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0',
          }}
        >
          <button
            className="btn-secondary"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            aria-label={t('action.previous')}
            style={{ padding: '0.35rem 0.65rem' }}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {t('table.pageOf', { page: currentPage, total: totalPages })}
          </span>
          <button
            className="btn-secondary"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
            aria-label={t('action.next')}
            style={{ padding: '0.35rem 0.65rem' }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
