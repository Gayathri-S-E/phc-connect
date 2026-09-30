import React from 'react';
import { Check } from 'lucide-react';

export interface PillarCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  items?: string[];
  className?: string;
}

export const PillarCard: React.FC<PillarCardProps> = ({ icon, title, description, items = [], className = '' }) => (
  <article className={`flex h-full flex-col rounded-lg border border-border bg-card p-6 ${className}`}>
    <div
      aria-hidden="true"
      className="mb-4 flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-primary-soft text-primary-text"
    >
      {icon}
    </div>
    <h3 className="text-section-title font-semibold text-foreground">{title}</h3>
    <p className="mt-2 text-small leading-relaxed text-muted-foreground">{description}</p>
    {items.length > 0 && (
      <ul className="mt-4 space-y-2 border-t border-border pt-4">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2 text-small text-foreground">
            <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary-text" aria-hidden="true" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    )}
  </article>
);
