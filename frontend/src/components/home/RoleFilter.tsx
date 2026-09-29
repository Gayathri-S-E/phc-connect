import React, { useRef } from 'react';

export type RoleCategory = 'all' | 'clinical' | 'supply' | 'admin';

interface Tab {
  key: RoleCategory;
  label: string;
}

const TABS: Tab[] = [
  { key: 'all',      label: 'All Roles' },
  { key: 'clinical', label: 'Clinical'  },
  { key: 'supply',   label: 'Supply'    },
  { key: 'admin',    label: 'Admin'     },
];

interface Props {
  selected: RoleCategory;
  counts:   Record<RoleCategory, number>;
  onChange: (c: RoleCategory) => void;
}

export const RoleFilter: React.FC<Props> = ({ selected, counts, onChange }) => {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const handleKey = (e: React.KeyboardEvent, idx: number) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); const n = (idx + 1) % TABS.length; onChange(TABS[n].key); refs.current[n]?.focus(); }
    if (e.key === 'ArrowLeft')  { e.preventDefault(); const n = (idx - 1 + TABS.length) % TABS.length; onChange(TABS[n].key); refs.current[n]?.focus(); }
  };

  return (
    <div
      role="tablist"
      aria-label="Filter role portals"
      className="flex items-center gap-1.5 overflow-x-auto no-scrollbar snap-x p-1.5 rounded-xl shrink-0 max-w-full"
      style={{ backgroundColor: 'rgba(30,41,59,0.8)', border: '1px solid rgba(255,255,255,0.08)' }}
    >
      {TABS.map(({ key, label }, idx) => {
        const active = selected === key;
        return (
          <button
            key={key}
            ref={(el) => { refs.current[idx] = el; }}
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(key)}
            onKeyDown={(e) => handleKey(e, idx)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold snap-start shrink-0 whitespace-nowrap transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
            style={
              active
                ? { backgroundColor: '#0284c7', color: '#ffffff' }
                : { backgroundColor: 'transparent', color: '#94a3b8' }
            }
          >
            {label}
            <span
              className="px-1.5 py-0.5 rounded-md text-[10px] font-mono tabular-nums"
              style={active ? { backgroundColor: '#0369a1', color: '#fff' } : { backgroundColor: 'rgba(255,255,255,0.08)', color: '#94a3b8' }}
            >
              {counts[key]}
            </span>
          </button>
        );
      })}
    </div>
  );
};
