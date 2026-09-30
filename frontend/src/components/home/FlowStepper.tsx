import React from 'react';
import { useLanguage } from '../../context/LanguageContext';

const STEP_NUMBERS = [1, 2, 3, 4] as const;

export const FlowStepper: React.FC = () => {
  const { t } = useLanguage();

  return (
    <ol className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0 lg:divide-x lg:divide-border lg:rounded-lg lg:border lg:border-border lg:bg-card">
      {STEP_NUMBERS.map((n) => (
        <li
          key={n}
          className="flex flex-col rounded-lg border border-border bg-card p-5 lg:rounded-none lg:border-0 lg:p-6"
        >
          <div className="mb-3 flex items-center gap-3">
            <span
              aria-hidden="true"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary font-mono text-small font-semibold text-primary-foreground"
            >
              {n}
            </span>
            <span className="text-caption font-semibold uppercase tracking-wide text-muted-foreground">
              {t('landing.flow.step', { n })}
            </span>
          </div>
          <h3 className="text-body font-semibold text-foreground">{t(`landing.flow.${n}.title`)}</h3>
          <p className="mt-1.5 text-small leading-relaxed text-muted-foreground">{t(`landing.flow.${n}.desc`)}</p>
        </li>
      ))}
    </ol>
  );
};
