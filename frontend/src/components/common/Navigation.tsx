import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, Calendar, FileText, MessageSquare, Users, Activity,
  User, Pill, Box, Truck, Building2, ClipboardList,
  AlertTriangle, Siren, Map, Target, CheckSquare, BarChart3,
  Globe, ListFilter, Bell, Server, Shield, FlaskConical, Layers
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { formatRoleName } from '../../utils/formatters';

const ICON_MAP: Record<string, React.ReactNode> = {
  home: <Home size={18} />,
  calendar: <Calendar size={18} />,
  file: <FileText size={18} />,
  chat: <MessageSquare size={18} />,
  users: <Users size={18} />,
  activity: <Activity size={18} />,
  user: <User size={18} />,
  flask: <FlaskConical size={18} />,
  pill: <Pill size={18} />,
  box: <Box size={18} />,
  truck: <Truck size={18} />,
  building: <Building2 size={18} />,
  clipboard: <ClipboardList size={18} />,
  alert: <AlertTriangle size={18} />,
  siren: <Siren size={18} />,
  map: <Map size={18} />,
  target: <Target size={18} />,
  check: <CheckSquare size={18} />,
  chart: <BarChart3 size={18} />,
  globe: <Globe size={18} />,
  list: <ListFilter size={18} />,
  bell: <Bell size={18} />,
  server: <Server size={18} />,
  shield: <Shield size={18} />,
};

interface NavigationProps {
  onItemClick?: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({ onItemClick }) => {
  const { navItems, activeRole } = useAuth();
  const { t } = useLanguage();

  const formatLabel = (key: string): string => {
    const parts = key.split('.');
    const raw = parts[parts.length - 1];
    return raw.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const getSectionHeader = (key: string): string => {
    if (key.startsWith('patient') || key.startsWith('clinical') || key.startsWith('triage')) {
      return 'CLINICAL OPERATIONS';
    }
    if (key.startsWith('pharmacy') || key.startsWith('inventory')) {
      return 'PHARMACY & INVENTORY';
    }
    if (key.startsWith('supply') || key.startsWith('warehouse')) {
      return 'SUPPLY CHAIN & LOGISTICS';
    }
    if (key.startsWith('emergency') || key.startsWith('disaster')) {
      return 'EMERGENCY RESPONSE';
    }
    if (key.startsWith('analytics') || key.startsWith('district') || key.startsWith('state') || key.startsWith('national')) {
      return 'INTELLIGENCE & GOVERNANCE';
    }
    if (key.startsWith('platform') || key.startsWith('admin') || key.startsWith('audit')) {
      return 'PLATFORM ADMINISTRATION';
    }
    return 'MODULES';
  };

  // Group navItems by section
  const groupedItems: Record<string, typeof navItems> = {};
  navItems.forEach((item) => {
    const section = getSectionHeader(item.key);
    if (!groupedItems[section]) groupedItems[section] = [];
    groupedItems[section].push(item);
  });

  return (
    <nav className="flex flex-col gap-4 p-3 font-sans text-slate-800">
      {/* Role Title Header Banner */}
      <div className="px-3 py-2 bg-sky-50/80 border border-sky-200/80 rounded-xl">
        <div className="text-[10px] font-bold text-sky-700 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3 h-3 text-sky-600" />
          Active Workspace
        </div>
        <div className="text-xs font-bold text-slate-900 mt-0.5 truncate">
          {activeRole ? formatRoleName(activeRole) : 'Authorized Portal'}
        </div>
      </div>

      {navItems.length === 0 ? (
        <div className="px-3 py-2 text-xs text-slate-500 font-medium">
          {t('state.loading')}
        </div>
      ) : (
        Object.entries(groupedItems).map(([sectionTitle, items]) => (
          <div key={sectionTitle} className="space-y-1">
            <div className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              {sectionTitle}
            </div>
            {items.map((item) => {
              const icon = ICON_MAP[item.icon] || <Activity size={18} />;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onItemClick}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                      isActive
                        ? 'bg-sky-600 text-white shadow-xs font-bold'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
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
