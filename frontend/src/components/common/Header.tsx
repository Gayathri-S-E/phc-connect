import React, { useState } from 'react';
import { 
  Activity, Globe, User, LogOut, ChevronDown, 
  Menu, ShieldCheck, RefreshCw 
} from 'lucide-react';
import { useAuth, DEMO_ACCOUNTS } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { user, activeRole, scope, logout, switchDemoRole } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const [isSwitching, setIsSwitching] = useState(false);

  const handleRoleChange = async (roleKey: string) => {
    setIsSwitching(true);
    try {
      const res = await switchDemoRole(roleKey);
      if (res.success && res.path) {
        navigate(res.path);
      }
    } finally {
      setIsSwitching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.25rem',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
      }}
    >
      {/* Left: Brand & Mobile Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
            className="btn-icon"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-main)',
              display: 'flex',
              padding: '0.4rem',
              borderRadius: '6px',
            }}
          >
            <Menu size={22} />
          </button>
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--primary) 0%, #1e40af 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.3)',
            }}
          >
            <Activity size={22} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1.2 }}>
              {t('app.title')}
            </h1>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              {t('app.subtitle')}
            </span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Role Switcher Dropdown (Dev & Demo Feature) */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <select
            value={activeRole || 'PATIENT'}
            onChange={(e) => handleRoleChange(e.target.value)}
            disabled={isSwitching}
            aria-label={t('nav.switchRole')}
            style={{
              padding: '0.4rem 1.85rem 0.4rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid rgba(37, 99, 235, 0.3)',
              backgroundColor: 'rgba(37, 99, 235, 0.05)',
              color: 'var(--primary)',
              fontWeight: 600,
              fontSize: '0.825rem',
              cursor: 'pointer',
              appearance: 'none',
              outline: 'none',
            }}
          >
            {Object.entries(DEMO_ACCOUNTS).map(([key, acc]) => (
              <option key={key} value={key}>
                {acc.name}
              </option>
            ))}
          </select>
          <div style={{ position: 'absolute', right: '0.5rem', pointerEvents: 'none', color: 'var(--primary)' }}>
            {isSwitching ? <RefreshCw size={13} className="animate-spin" /> : <ChevronDown size={14} />}
          </div>
        </div>

        {/* Scope Pill Badge */}
        {scope && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.75rem',
              padding: '0.25rem 0.6rem',
              borderRadius: '6px',
              backgroundColor: 'rgba(100, 116, 139, 0.1)',
              color: '#334155',
              fontWeight: 600,
            }}
          >
            <ShieldCheck size={13} style={{ color: 'var(--primary)' }} />
            {scope}
          </span>
        )}

        {/* Language Switcher */}
        <button
          onClick={() => setLanguage(language === 'en' ? 'ta' : 'en')}
          className="btn-secondary"
          title="Toggle English / தமிழ்"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.35rem 0.65rem',
            fontSize: '0.8rem',
            fontWeight: 600,
          }}
        >
          <Globe size={14} />
          {language === 'en' ? 'தமிழ்' : 'English'}
        </button>

        {/* User Profile / Logout */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: '0.25rem' }}>
            <div
              title={user.email}
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary)',
                fontWeight: 700,
                fontSize: '0.85rem',
              }}
            >
              <User size={16} />
            </div>
            <button
              onClick={handleLogout}
              className="btn-icon"
              title={t('nav.logout')}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                padding: '0.4rem',
                borderRadius: '6px',
                display: 'flex',
              }}
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
