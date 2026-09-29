import React from 'react';
import { ArrowRight } from 'lucide-react';
import { formatRoleName } from '../../utils/formatters';

/* Category → accent colour map */
const ACCENTS = {
  clinical: { border: '#0d9488', iconBg: 'rgba(13,148,136,0.15)', label: '#0d9488' },
  supply:   { border: '#0284c7', iconBg: 'rgba(2,132,199,0.15)',  label: '#0284c7' },
  admin:    { border: '#7c3aed', iconBg: 'rgba(124,58,237,0.15)', label: '#7c3aed' },
};

interface Props {
  code:       string;
  index:      number;
  account:    { email: string; name: string; role: string; defaultPath: string };
  category:   'clinical' | 'supply' | 'admin';
  icon:       React.ReactNode;
  isDisabled?: boolean;
  onSelect:   (code: string) => void;
}

export const RoleCard: React.FC<Props> = ({
  code, index, account, category, icon, isDisabled = false, onSelect,
}) => {
  const accent = ACCENTS[category];

  return (
    <button
      type="button"
      onClick={() => onSelect(code)}
      disabled={isDisabled}
      aria-label={`Sign in as ${formatRoleName(code)}`}
      className="flex flex-col p-5 rounded-2xl text-left h-full w-full transition duration-200 cursor-pointer
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2
                 disabled:opacity-50 disabled:cursor-not-allowed group"
      style={{
        backgroundColor: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderLeft: `4px solid ${accent.border}`,
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'rgba(255,255,255,0.1)'; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'rgba(255,255,255,0.05)'; }}
    >
      {/* Top row: icon + role number chip */}
      <div className="flex items-center justify-between mb-3 min-w-0">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: accent.iconBg }}>
          {icon}
        </div>
        <span
          className="text-[11px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-md"
          style={{ backgroundColor: 'rgba(255,255,255,0.08)', color: '#94a3b8' }}
        >
          ROLE {String(index + 1).padStart(2, '0')}
        </span>
      </div>

      {/* Role title — line-clamp-2, min-h for 2 lines so cards align */}
      <h3
        className="text-base font-semibold text-white leading-snug mb-1"
        style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', minHeight: '2.75rem' }}
      >
        {formatRoleName(code)}
      </h3>

      {/* Persona name */}
      <p className="text-sm text-slate-300 truncate mb-1 min-w-0">{account.name}</p>

      {/* Email — mono, truncated, never overflows */}
      <p
        className="text-xs text-slate-400 truncate min-w-0 block"
        style={{ fontFamily: "'JetBrains Mono', monospace" }}
        title={account.email}
      >
        {account.email}
      </p>

      {/* "Sign in as →" pinned bottom */}
      <div className="mt-auto pt-4 flex items-center justify-between border-t min-w-0" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
        <span className="text-xs font-semibold" style={{ color: accent.label }}>
          Sign in as →
        </span>
        <ArrowRight className="w-3.5 h-3.5 shrink-0 opacity-60 group-hover:opacity-100 transition" style={{ color: accent.label }} />
      </div>
    </button>
  );
};
