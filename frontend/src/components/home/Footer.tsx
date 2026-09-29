import React from 'react';
import { Building2 } from 'lucide-react';
import { Container } from '../common/Container';

export const Footer: React.FC = () => (
  <footer
    id="about"
    className="scroll-mt-[72px] border-t border-slate-200 py-6 text-sm"
    style={{ backgroundColor: '#0f172a' }}
  >
    <Container className="flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
      <div className="flex flex-col sm:flex-row items-center gap-2 min-w-0">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-sky-400 shrink-0" />
          <span className="font-bold text-white">Smart Health &amp; Supply Chain Resilience</span>
        </div>
        <span className="hidden sm:inline text-slate-600">•</span>
        <span className="text-slate-300">Government of Tamil Nadu</span>
      </div>
      <p className="text-xs text-slate-400 shrink-0">
        Protected by Strict Scope Authorization &amp; RFC Auditing.
      </p>
    </Container>
  </footer>
);
