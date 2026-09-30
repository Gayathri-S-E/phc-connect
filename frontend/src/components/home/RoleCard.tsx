import React from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';
import { formatRoleName } from '../../utils/formatters';
import { Badge } from '../ui/badge';

/* Category → accent styling (Med2Us Signature Palette) */
const ACCENT_STYLES = {
  clinical: {
    border: 'border-l-[#5aa9e6] hover:border-l-[#3b8ec8]',
    iconBg: 'bg-[#f0f7fe] text-[#257bb5] border border-[#7fc8f8]/60',
    label: 'text-[#257bb5]',
  },
  supply: {
    border: 'border-l-[#7fc8f8] hover:border-l-[#5aa9e6]',
    iconBg: 'bg-[#f0f9ff] text-[#257bb5] border border-[#7fc8f8]/60',
    label: 'text-[#257bb5]',
  },
  admin: {
    border: 'border-l-[#ff6392] hover:border-l-[#e04f7b]',
    iconBg: 'bg-[#fff0f5] text-[#d93b6e] border border-[#ff6392]/40',
    label: 'text-[#d93b6e]',
  },
};

interface Props {
  code: string;
  index: number;
  account: { email: string; name: string; role: string; defaultPath: string };
  category: 'clinical' | 'supply' | 'admin';
  icon: React.ReactNode;
  isDisabled?: boolean;
  isLoading?: boolean;
  onSelect: (code: string) => void;
}

export const RoleCard: React.FC<Props> = ({
  code, index, account, category, icon, isDisabled = false, isLoading = false, onSelect,
}) => {
  const accent = ACCENT_STYLES[category];

  return (
    <button
      type="button"
      onClick={() => onSelect(code)}
      disabled={isDisabled}
      aria-label={`Sign in as ${formatRoleName(code)}`}
      className={`flex flex-col p-5 rounded-xl text-left h-full w-full transition-all duration-200 cursor-pointer
                 bg-white hover:bg-slate-50/80 border border-slate-200/90 hover:border-slate-300 border-l-4 ${accent.border}
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2
                 disabled:opacity-50 disabled:cursor-not-allowed group shadow-2xs hover:shadow-md`}
    >
      {/* Top row: icon + role number chip */}
      <div className="flex items-center justify-between mb-3 w-full">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${accent.iconBg}`}>
          {icon}
        </div>
        <span className="text-[11px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200/60">
          ROLE {String(index + 1).padStart(2, '0')}
        </span>
      </div>

      {/* Role title */}
      <h3 className="text-sm font-extrabold text-slate-900 leading-snug mb-1 line-clamp-2 min-h-[2.5rem]">
        {formatRoleName(code)}
      </h3>

      {/* Persona name */}
      <p className="text-xs text-slate-700 font-semibold truncate mb-1 w-full">{account.name}</p>

      {/* Email & Demo Credential note */}
      <p className="text-[11px] font-mono text-slate-500 truncate w-full" title={account.email}>
        {account.email}
      </p>
      <p className="text-[10px] font-mono text-slate-400 truncate w-full mt-0.5">
        Credential: Demo@Health2026
      </p>

      {/* "Sign in as →" pinned bottom */}
      <div className="mt-auto pt-3 flex items-center justify-between border-t border-slate-100 w-full">
        <span className={`text-xs font-bold ${accent.label}`}>
          {isLoading ? 'Authenticating...' : 'Sign in as →'}
        </span>
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 text-sky-600 animate-spin shrink-0" />
        ) : (
          <ArrowRight className={`w-3.5 h-3.5 shrink-0 opacity-70 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all ${accent.label}`} />
        )}
      </div>
    </button>
  );
};
