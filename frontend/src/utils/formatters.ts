export const ROLE_DISPLAY_NAMES: Record<string, string> = {
  PATIENT: 'Citizen / Patient',
  DOCTOR: 'Medical Officer',
  NURSE: 'Nurse / Healthcare Staff',
  PHC_IN_CHARGE: 'PHC In-Charge',
  PHARMACIST: 'Dispensary Pharmacist',
  DISTRICT_HEALTH_OFFICER: 'District Health Officer',
  DISTRICT_SUPPLY_OFFICER: 'District Supply Officer',
  DISTRICT_EMERGENCY_COORDINATOR: 'District Emergency Coordinator',
  STATE_HEALTH_ADMIN: 'State Health Administrator',
  STATE_SUPPLY_MANAGER: 'State Supply Manager',
  STATE_PUBLIC_HEALTH_ANALYST: 'State Public Health Analyst',
  NATIONAL_HEALTH_AUTHORITY: 'National Health Authority',
  SUPER_ADMIN: 'Super Administrator',
};

export function formatRoleName(roleCode?: string | null, t?: (key: string, fallback?: string) => string): string {
  if (!roleCode) return 'User';
  if (t) {
    const key = `role.${roleCode}`;
    const translated = t(key);
    if (translated && translated !== key) return translated;
  }
  return ROLE_DISPLAY_NAMES[roleCode] || roleCode.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatScopeLevel(scope?: string | null): string {
  if (!scope) return 'Facility';
  return scope.toUpperCase();
}
