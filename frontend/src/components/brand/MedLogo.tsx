import { cn } from '../../lib/utils';

export interface MedLogoProps {
  /** Height of the mark in px (the wordmark scales with it). */
  size?: number;
  /** mark = symbol only; full = symbol + "Med2Us" wordmark. */
  variant?: 'mark' | 'full';
  className?: string;
  /** Set when the logo is the only label of a link/button; otherwise it is announced as "Med2Us". */
  title?: string;
}

/**
 * Med2Us logo. A medical cross drawn as a network: four nodes joined to a gold hub.
 * The rose node (right) is the "us" end of the connection. Palette only: cool-sky, snow, gold, rose, ink.
 */
export function MedLogoMark({ size = 32, className, title = 'Med2Us' }: Omit<MedLogoProps, 'variant'>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width={size}
      height={size}
      role="img"
      aria-label={title}
      className={cn('shrink-0', className)}
    >
      <rect width="48" height="48" rx="12" fill="#5aa9e6" />
      <path d="M24 12v24M12 24h24" stroke="#0b1f33" strokeWidth="4.5" strokeLinecap="round" />
      <circle cx="24" cy="12" r="4.5" fill="#f9f9f9" stroke="#0b1f33" strokeWidth="2.5" />
      <circle cx="24" cy="36" r="4.5" fill="#f9f9f9" stroke="#0b1f33" strokeWidth="2.5" />
      <circle cx="12" cy="24" r="4.5" fill="#f9f9f9" stroke="#0b1f33" strokeWidth="2.5" />
      <circle cx="36" cy="24" r="4.5" fill="#ff6392" stroke="#0b1f33" strokeWidth="2.5" />
      <circle cx="24" cy="24" r="5.5" fill="#ffe45e" stroke="#0b1f33" strokeWidth="2.5" />
    </svg>
  );
}

export function MedLogo({ size = 32, variant = 'mark', className, title = 'Med2Us' }: MedLogoProps) {
  if (variant === 'mark') return <MedLogoMark size={size} className={className} title={title} />;
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)} role="img" aria-label={title}>
      <MedLogoMark size={size} title="" className="" />
      <span
        aria-hidden="true"
        className="font-semibold leading-none tracking-tight text-foreground"
        style={{ fontSize: Math.round(size * 0.6) }}
      >
        Med<span className="text-primary-text">2</span>Us
      </span>
    </span>
  );
}

export default MedLogo;
