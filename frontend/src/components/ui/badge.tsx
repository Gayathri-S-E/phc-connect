import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'sky' | 'teal' | 'success' | 'warning' | 'destructive' | 'outline' | 'slate';
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  className = '',
  style,
  children,
  ...props
}) => {
  const baseStyles = "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide transition-colors";

  const variants = {
    default: "bg-slate-900 text-white",
    sky: "bg-sky-100 text-sky-800 border border-sky-200/80",
    teal: "bg-teal-100 text-teal-800 border border-teal-200/80",
    success: "bg-emerald-100 text-emerald-800 border border-emerald-200/80",
    warning: "bg-amber-100 text-amber-800 border border-amber-200/80",
    destructive: "bg-red-100 text-red-800 border border-red-200/80",
    outline: "bg-white text-slate-700 border border-slate-200",
    slate: "bg-slate-100 text-slate-700 border border-slate-200",
  };

  return (
    <div className={`${baseStyles} ${variants[variant]} ${className}`} style={style} {...props}>
      {children}
    </div>
  );
};
