import React from 'react';
import { Sparkles, ArrowRight, HeartPulse, Boxes, Truck, LineChart } from 'lucide-react';
import { Container } from '../common/Container';

interface HeroProps {
  onOpenLogin: () => void;
}

const PILLS = [
  {
    icon: <HeartPulse className="w-5 h-5" />,
    bg: '#e0f2fe',
    color: '#0284c7',
    title: 'Clinical OPD',
    sub: 'Triage to Consultation',
  },
  {
    icon: <Boxes className="w-5 h-5" />,
    bg: '#ccfbf1',
    color: '#0d9488',
    title: 'Stock Visibility',
    sub: 'Real-time Buffer Status',
  },
  {
    icon: <Truck className="w-5 h-5" />,
    bg: '#dbeafe',
    color: '#1d4ed8',
    title: 'Supply Pipeline',
    sub: 'Fulfillment & Reorders',
  },
  {
    icon: <LineChart className="w-5 h-5" />,
    bg: '#f3e8ff',
    color: '#7c3aed',
    title: 'Public Health',
    sub: 'Epidemic Trend Analysis',
  },
];

export const Hero: React.FC<HeroProps> = ({ onOpenLogin }) => (
  <section className="relative pt-28 pb-16 sm:pt-32 sm:pb-24 border-b border-slate-200"
    style={{ background: 'linear-gradient(180deg, #f0f9ff 0%, #ffffff 60%, #f8fafc 100%)' }}
  >
    <Container className="flex flex-col items-center text-center gap-6">

      {/* Kicker chip */}
      <div
        className="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold uppercase tracking-wider shadow-sm"
        style={{ backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd' }}
      >
        <Sparkles className="w-3.5 h-3.5 shrink-0" />
        Smart Health &amp; Supply Chain Resilience
      </div>

      {/* H1 */}
      <h1
        className="font-bold tracking-tight text-slate-900 text-balance max-w-4xl w-full"
        style={{ fontSize: 'clamp(2rem, 5vw + 0.5rem, 3.75rem)', lineHeight: 1.1 }}
      >
        Connected Healthcare Operations with{' '}
        <span style={{ backgroundImage: 'linear-gradient(90deg,#0284c7,#0d9488)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
          Resilient Supply Chains
        </span>
      </h1>

      {/* Lead paragraph */}
      <p className="max-w-2xl text-base md:text-lg leading-relaxed text-slate-600 text-pretty w-full">
        An integrated healthcare platform empowering primary health centers, clinical staff, district coordinators, and state authorities with real-time inventory visibility and decision support.
      </p>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-4 w-full max-w-sm sm:max-w-none">
        <a
          href="#roles"
          className="inline-flex items-center justify-center gap-2 h-12 px-7 rounded-xl text-sm font-bold text-white shadow-md hover:opacity-90 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2"
          style={{ backgroundColor: '#0284c7' }}
        >
          Explore 13 Role Portals
          <ArrowRight className="w-4 h-4 shrink-0" />
        </a>
        <button
          onClick={onOpenLogin}
          className="inline-flex items-center justify-center gap-2 h-12 px-7 rounded-xl text-sm font-bold text-slate-800 border border-slate-300 hover:bg-slate-50 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2"
          style={{ backgroundColor: '#ffffff' }}
        >
          Direct Sign In
        </button>
      </div>

      {/* Quick-stat pills */}
      <div className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-8">
        {PILLS.map((p) => (
          <div
            key={p.title}
            className="flex items-center gap-4 p-4 rounded-2xl border border-slate-200 bg-white shadow-sm text-left"
          >
            {/* 40 px icon box */}
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: p.bg, color: p.color }}
            >
              {p.icon}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold text-slate-900 truncate">{p.title}</div>
              <div className="text-xs text-slate-500 truncate mt-0.5">{p.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </Container>
  </section>
);
