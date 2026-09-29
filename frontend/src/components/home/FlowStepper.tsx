import React from 'react';

interface Step {
  badge: string;
  badgeBg: string;
  badgeColor: string;
  title: string;
  description: string;
}

const STEPS: Step[] = [
  {
    badge: 'STEP 01',
    badgeBg: '#e0f2fe',
    badgeColor: '#0369a1',
    title: 'Patient Consultation',
    description: 'Patient registers at PHC, receives triage from Nurse, and is diagnosed by Doctor.',
  },
  {
    badge: 'STEP 02',
    badgeBg: '#ccfbf1',
    badgeColor: '#0f766e',
    title: 'Pharmacy Dispensing',
    description: 'e-Prescription auto-routes to Pharmacist dispensary; stock levels update instantly.',
  },
  {
    badge: 'STEP 03',
    badgeBg: '#fef3c7',
    badgeColor: '#92400e',
    title: 'Stock Reorder Alert',
    description: 'Low stock triggers automated reorder request to District Supply Officer.',
  },
  {
    badge: 'STEP 04',
    badgeBg: '#f1f5f9',
    badgeColor: '#334155',
    title: 'State & National View',
    description: 'State and National dashboards visualize epidemiologic demand and buffer readiness.',
  },
];

export const FlowStepper: React.FC = () => (
  /* Mobile: vertical rail; tablet: 2×2; desktop: 4 cols with connector */
  <div className="relative">
    {/* Desktop connector line (hidden on mobile/tablet) */}
    <div
      className="hidden lg:block absolute top-12 left-0 right-0 h-px"
      style={{ backgroundColor: '#e2e8f0', zIndex: 0 }}
      aria-hidden="true"
    />

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch relative z-10">
      {STEPS.map((step, i) => (
        <div
          key={step.badge}
          className="flex flex-col p-6 rounded-2xl border border-slate-200 bg-white shadow-sm h-full"
        >
          {/* Step number circle (connects to the line on desktop) */}
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold mb-4 shrink-0 relative z-10 border-2"
            style={{ backgroundColor: '#ffffff', borderColor: step.badgeColor, color: step.badgeColor }}
          >
            {i + 1}
          </div>

          {/* Step badge chip — inside the card flow, never overlapping */}
          <span
            className="inline-flex items-center self-start px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider mb-3"
            style={{ backgroundColor: step.badgeBg, color: step.badgeColor }}
          >
            {step.badge}
          </span>

          <h3 className="text-base font-bold text-slate-900 mb-2">{step.title}</h3>
          <p className="text-sm text-slate-600 leading-relaxed text-pretty font-normal flex-1">{step.description}</p>
        </div>
      ))}
    </div>
  </div>
);
