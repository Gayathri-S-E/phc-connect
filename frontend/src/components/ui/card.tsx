import React from 'react';

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', style, children, ...props }) => (
  <div
    className={`bg-white rounded-xl border border-slate-200/90 shadow-sm transition-all duration-200 hover:shadow-md hover:border-slate-300 ${className}`}
    style={style}
    {...props}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', style, children, ...props }) => (
  <div className={`p-5 pb-3 flex flex-col space-y-1.5 ${className}`} style={style} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className = '', style, children, ...props }) => (
  <h3 className={`text-base font-bold text-slate-900 tracking-tight leading-tight ${className}`} style={style} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className = '', style, children, ...props }) => (
  <p className={`text-xs text-slate-500 font-medium leading-relaxed ${className}`} style={style} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', style, children, ...props }) => (
  <div className={`p-5 pt-0 ${className}`} style={style} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', style, children, ...props }) => (
  <div className={`p-5 pt-0 flex items-center ${className}`} style={style} {...props}>
    {children}
  </div>
);
