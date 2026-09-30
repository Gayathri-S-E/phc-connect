import React, { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Home, Calendar, FileText, MessageSquare, Users, Activity, User, Pill, Box, Truck, Building2, ClipboardList,
  AlertTriangle, Siren, Map, Target, CheckSquare, BarChart3, Globe, ListFilter, Bell, Server, Shield, FlaskConical, Lock,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import type { NavigationItem } from '../../services/types';

/** Backend icon names (GET /navigation/me) -> lucide icons. */
export const NAV_ICONS: Record<string, React.ComponentType<{ className?: string; 'aria-hidden'?: boolean }>> = {
  home: Home, calendar: Calendar, file: FileText, chat: MessageSquare, users: Users, activity: Activity, user: User,
  flask: FlaskConical, pill: Pill, box: Box, truck: Truck, building: Building2, clipboard: ClipboardList,
  alert: AlertTriangle, siren: Siren, map: Map, target: Target, check: CheckSquare, chart: BarChart3, globe: Globe,
  list: ListFilter, bell: Bell, server: Server, shield: Shield, lock: Lock,
};

/**
 * Backend section (navigation catalogue) -> existing i18n section key. Sections without a dedicated key in i18n.ts
 * fall back to the English label in SECTION_FALLBACK (t(key, fallback) is used, so adding the key later just works).
 */
const SECTION_KEY: Record<string, string> = {
  patient: 'nav.section.patient',
  clinical: 'nav.section.clinical',
  facility: 'nav.section.facility',
  pharmacy: 'nav.section.pharmacy',
  supply: 'nav.section.supply',
  emergency: 'nav.section.emergency',
  district: 'nav.section.governance',
  state: 'nav.section.governance',
  analytics: 'nav.section.governance',
  national: 'nav.section.governance',
  capacity: 'nav.section.capacity',
  intelligence: 'nav.section.intelligence',
  platform: 'nav.section.platform',
};

const SECTION_FALLBACK: Record<string, string> = {
  'nav.section.patient': 'My health',
  'nav.section.facility': 'Facility',
  'nav.section.capacity': 'Capacity',
  'nav.section.intelligence': 'Supply intelligence',
  'nav.section.modules': 'Modules',
};

export interface NavEntry {
  key: string;
  path: string;
  label: string;
  icon: string;
  sectionKey: string;
  sectionLabel: string;
}

export interface NavGroup {
  sectionKey: string;
  label: string;
  items: NavEntry[];
}

export interface CurrentPage {
  /** Matching catalogue entry, if the route is in the catalogue. */
  entry: NavEntry | null;
  sectionLabel: string | null;
  /** Page label (catalogue label, or a humanised last path segment). */
  pageLabel: string;
  pathname: string;
}

const humanise = (raw: string) => raw.replace(/[-_.]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function isPrefix(itemPath: string, pathname: string) {
  return pathname === itemPath || pathname.startsWith(itemPath.endsWith('/') ? itemPath : `${itemPath}/`);
}

/** Global destinations (from useAuth().navItems) grouped by section, plus resolution of the current route. */
export function useNavCatalogue() {
  const { navItems } = useAuth();
  const { t } = useLanguage();
  const { pathname } = useLocation();

  const label = React.useCallback(
    (key: string): string => {
      const translated = t(key);
      if (translated && translated !== key) return translated;
      return humanise(key.split('.').pop() || key);
    },
    [t]
  );

  const { groups, entries } = useMemo(() => {
    const seen = new Set<string>();
    const order: string[] = [];
    const byKey: Record<string, NavGroup> = {};
    const all: NavEntry[] = [];
    (navItems as NavigationItem[]).forEach((item) => {
      if (seen.has(item.path)) return;
      seen.add(item.path);
      const sectionKey = SECTION_KEY[item.section] ?? 'nav.section.modules';
      const sectionLabel = t(sectionKey, SECTION_FALLBACK[sectionKey] ?? humanise(item.section || 'modules'));
      const entry: NavEntry = {
        key: item.key,
        path: item.path,
        label: label(item.key),
        icon: item.icon,
        sectionKey,
        sectionLabel,
      };
      all.push(entry);
      if (!byKey[sectionKey]) {
        byKey[sectionKey] = { sectionKey, label: sectionLabel, items: [] };
        order.push(sectionKey);
      }
      byKey[sectionKey].items.push(entry);
    });
    return { groups: order.map((k) => byKey[k]), entries: all };
  }, [navItems, t, label]);

  const current: CurrentPage = useMemo(() => {
    // Longest catalogue path that is a prefix of the route wins, so exactly one item is active.
    let best: NavEntry | null = null;
    for (const e of entries) {
      if (isPrefix(e.path, pathname) && (!best || e.path.length > best.path.length)) best = e;
    }
    if (best) return { entry: best, sectionLabel: best.sectionLabel, pageLabel: best.label, pathname };
    const segs = pathname.split('/').filter(Boolean);
    const last = segs[segs.length - 1];
    return {
      entry: null,
      sectionLabel: null,
      pageLabel: last ? humanise(decodeURIComponent(last)) : t('nav.dashboard', 'Dashboard'),
      pathname,
    };
  }, [entries, pathname, t]);

  return { groups, entries, current };
}
