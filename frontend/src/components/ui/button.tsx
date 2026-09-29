import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'sky';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  asChild?: boolean;
}

/*
  IMPORTANT: All color/background values are written as inline-compatible
  explicit Tailwind classes AND backed by an explicit style prop fallback.
  This ensures they win over any bare `button {}` CSS resets in older
  stylesheet layers.

  In Tailwind v4 all utilities are generated at @layer utilities, which
  has lower specificity than an unlayered `button {}` rule. The safest
  fix is to ensure index.css does NOT do `button { background: none }`.
  This component also explicitly names every class so Tailwind v4's
  content scanner detects them.
*/

const variantStyles: Record<string, { className: string; style: React.CSSProperties }> = {
  default: {
    className: 'bg-sky-600 text-white hover:bg-sky-700 shadow-sm',
    style: { backgroundColor: '#0284c7', color: '#ffffff' },
  },
  primary: {
    className: 'bg-sky-600 text-white hover:bg-sky-700 shadow-sm',
    style: { backgroundColor: '#0284c7', color: '#ffffff' },
  },
  sky: {
    className: 'bg-sky-600 text-white hover:bg-sky-700 shadow-md',
    style: { backgroundColor: '#0284c7', color: '#ffffff' },
  },
  secondary: {
    className: 'bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200',
    style: { backgroundColor: '#f1f5f9', color: '#1e293b' },
  },
  outline: {
    className: 'bg-white text-slate-800 border border-slate-300 hover:bg-slate-50',
    style: { backgroundColor: '#ffffff', color: '#1e293b', border: '1px solid #cbd5e1' },
  },
  ghost: {
    className: 'bg-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100',
    style: {},
  },
  destructive: {
    className: 'bg-red-600 text-white hover:bg-red-700 shadow-sm',
    style: { backgroundColor: '#dc2626', color: '#ffffff' },
  },
};

const sizeStyles: Record<string, string> = {
  sm:   'text-xs px-3 py-1.5 gap-1.5 min-h-[36px] min-w-[36px]',
  md:   'text-sm px-4 py-2 gap-2 min-h-[44px]',
  lg:   'text-sm px-6 gap-2.5 h-12',
  icon: 'p-2 min-w-[44px] min-h-[44px]',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'md',
  className = '',
  style,
  children,
  ...props
}) => {
  const vs = variantStyles[variant] ?? variantStyles.default;
  const ss = sizeStyles[size] ?? sizeStyles.md;

  const base =
    'inline-flex items-center justify-center font-semibold rounded-xl ' +
    'transition-all duration-150 select-none ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 ' +
    'active:scale-[0.97] disabled:opacity-50 disabled:pointer-events-none ' +
    'cursor-pointer whitespace-nowrap';

  return (
    <button
      className={`${base} ${vs.className} ${ss} ${className}`}
      style={{ ...vs.style, ...style }}
      {...props}
    >
      {children}
    </button>
  );
};
