import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, Calendar, FileText, MessageSquare, Users, Activity,
  User, Pill, Box, Truck, Building2, ClipboardList,
  AlertTriangle, Siren, Map, Target, CheckSquare, BarChart3,
  Globe, ListFilter, Bell, Server, Shield, FlaskConical
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

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

  // Format label from navigation key (e.g. "clinical.queue" -> "Queue")
  const formatLabel = (key: string): string => {
    const parts = key.split('.');
    const raw = parts[parts.length - 1];
    return raw.charAt(0).toUpperCase() + raw.slice(1);
  };

  return (
    <nav
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.35rem',
        padding: '1rem 0.75rem',
      }}
    >
      <div
        style={{
          fontSize: '0.75rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--text-muted)',
          padding: '0.25rem 0.75rem 0.5rem',
        }}
      >
        {activeRole ? activeRole.replace(/_/g, ' ') : 'NAVIGATION'}
      </div>

      {navItems.length === 0 ? (
        <div style={{ padding: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {t('state.loading')}
        </div>
      ) : (
        navItems.map((item) => {
          const icon = ICON_MAP[item.icon] || <Activity size={18} />;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onItemClick}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.65rem 0.85rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--primary)' : 'var(--text-main)',
                backgroundColor: isActive ? 'rgba(37, 99, 235, 0.08)' : 'transparent',
                textDecoration: 'none',
                transition: 'background-color 0.15s ease, color 0.15s ease',
              })}
            >
              <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>
              <span>{formatLabel(item.key)}</span>
            </NavLink>
          );
        })
      )}
    </nav>
  );
};
