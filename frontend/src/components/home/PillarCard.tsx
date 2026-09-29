import React from 'react';

export interface PillarCardProps {
  icon: React.ReactNode;
  iconBg: string;   /* CSS color string, e.g. '#0284c7' */
  title: string;
  description: string;
  className?: string;
}

export const PillarCard: React.FC<PillarCardProps> = ({ icon, iconBg, title, description, className = '' }) => (
  <div
    className={`flex flex-col p-6 lg:p-8 rounded-2xl border border-slate-200 bg-white shadow-sm hover:-translate-y-1 hover:shadow-lg transition-all duration-200 h-full ${className}`}
  >
    {/* 48px icon box */}
    <div
      className="w-12 h-12 rounded-xl flex items-center justify-center text-white shrink-0 mb-5"
      style={{ backgroundColor: iconBg }}
    >
      {icon}
    </div>
    <h3 className="text-xl font-bold text-slate-900 mb-2 tracking-tight">{title}</h3>
    <p className="text-sm text-slate-600 leading-relaxed text-pretty font-normal flex-1">{description}</p>
  </div>
);
