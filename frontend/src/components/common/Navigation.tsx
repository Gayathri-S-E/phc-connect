import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, Calendar, FileText, MessageSquare, Users, Activity,
  User, Pill, Box, Truck, Building2, ClipboardList,
  AlertTriangle, Siren, Map, Target, CheckSquare, BarChart3,
  Globe, ListFilter, Bell, Server, Shield, FlaskConical, Layers,
  Compass, HeartPulse
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { formatRoleName } from '../../utils/formatters';

const ICON_MAP: Record<string, React.ReactNode> = {
  home: <Home className="w-4 h-4" />,
  calendar: <Calendar className="w-4 h-4" />,
  file: <FileText className="w-4 h-4" />,
  chat: <MessageSquare className="w-4 h-4" />,
  users: <Users className="w-4 h-4" />,
  activity: <Activity className="w-4 h-4" />,
  user: <User className="w-4 h-4" />,
  flask: <FlaskConical className="w-4 h-4" />,
  pill: <Pill className="w-4 h-4" />,
  box: <Box className="w-4 h-4" />,
  truck: <Truck className="w-4 h-4" />,
  building: <Building2 className="w-4 h-4" />,
  clipboard: <ClipboardList className="w-4 h-4" />,
  alert: <AlertTriangle className="w-4 h-4" />,
  siren: <Siren className="w-4 h-4" />,
  map: <Map className="w-4 h-4" />,
  target: <Target className="w-4 h-4" />,
  check: <CheckSquare className="w-4 h-4" />,
  chart: <BarChart3 className="w-4 h-4" />,
  globe: <Globe className="w-4 h-4" />,
  list: <ListFilter className="w-4 h-4" />,
  bell: <Bell className="w-4 h-4" />,
  server: <Server className="w-4 h-4" />,
  shield: <Shield className="w-4 h-4" />,
};

interface NavigationProps {
  onItemClick?: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({ onItemClick }) => {
  const { navItems, activeRole, scope } = useAuth();
  const { t } = useLanguage();

  const formatLabel = (key: string): string => {
    const translated = t(key);
    if (translated && translated !== key) return translated;
    const parts = key.split('.');
    const raw = parts[parts.length - 1];
    return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const getSectionKey = (key: string): string => {
    if (key.startsWith('patient') || key.startsWith('clinical') || key.startsWith('triage')) {
      return 'nav.section.clinical';
    }
    if (key.startsWith('pharmacy') || key.startsWith('inventory')) {
      return 'nav.section.pharmacy';
    }
    if (key.startsWith('supply') || key.startsWith('warehouse')) {
      return 'nav.section.supply';
    }
    if (key.startsWith('emergency') || key.startsWith('disaster')) {
      return 'nav.section.emergency';
    }
    if (key.startsWith('analytics') || key.startsWith('district') || key.startsWith('state') || key.startsWith('national')) {
      return 'nav.section.governance';
    }
    if (key.startsWith('platform') || key.startsWith('admin') || key.startsWith('audit')) {
      return 'nav.section.platform';
    }
    return 'nav.section.modules';
  };

  // Group navItems by section
  const groupedItems: Record<string, typeof navItems> = {};
  navItems.forEach((item) => {
    const sectionKey = getSectionKey(item.key);
    if (!groupedItems[sectionKey]) groupedItems[sectionKey] = [];
    groupedItems[sectionKey].push(item);
  });

  return (
    <nav className="flex flex-col gap-4 p-3 font-sans text-slate-800">
      {/* Role & Scope Context Card */}
      <div className="p-3 bg-gradient-to-br from-sky-50 to-slate-50 border border-sky-100 rounded-xl space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-extrabold text-sky-700 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3 h-3 text-sky-600" />
            {t('nav.activeWorkspace') || 'Active Workspace'}
          </span>
          {scope && (
            <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-sky-200/80 text-sky-900">
              {scope}
            </span>
          )}
        </div>
        <div className="text-xs font-extrabold text-slate-900 truncate">
          {activeRole ? formatRoleName(activeRole, t) : t('nav.workspace') || 'Authorized Portal'}
        </div>
      </div>

      {navItems.length === 0 ? (
        <div className="px-3 py-4 text-xs text-slate-400 font-medium text-center">
          {t('state.loading') || 'Loading workspace modules...'}
        </div>
      ) : (
        Object.entries(groupedItems).map(([sectionKey, items]) => (
          <div key={sectionKey} className="space-y-1">
            <div className="px-3 text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">
              {t(sectionKey) || sectionKey.replace('nav.section.', '').toUpperCase()}
            </div>
            {items.map((item) => {
              const icon = ICON_MAP[item.icon] || <Activity className="w-4 h-4" />;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onItemClick}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                      isActive
                        ? 'bg-sky-600 text-white shadow-2xs font-bold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                    }`
                  }
                >
                  <span className="shrink-0">{icon}</span>
                  <span className="truncate">{formatLabel(item.key)}</span>
                </NavLink>
              );
            })}
          </div>
        ))
      )}
    </nav>
  );
};
