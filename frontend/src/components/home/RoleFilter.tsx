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
      className="flex items-center gap-1.5 overflow-x-auto no-scrollbar snap-x p-1.5 rounded-xl shrink-0 max-w-full bg-slate-100 border border-slate-200 shadow-2xs"
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
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold snap-start shrink-0 whitespace-nowrap transition cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
              active
                ? 'bg-white text-sky-900 shadow-2xs border border-slate-200/80'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            {label}
            <span
              className={`px-1.5 py-0.5 rounded-md text-[10px] font-mono tabular-nums font-semibold ${
                active
                  ? 'bg-sky-100 text-sky-800'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {counts[key]}
            </span>
          </button>
        );
      })}
    </div>
  );
};
