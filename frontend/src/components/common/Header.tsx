import React, { useState } from 'react';
import { 
  Activity, Globe, User, LogOut, ChevronDown, 
  Menu, ShieldCheck, RefreshCw 
} from 'lucide-react';
import { useAuth, DEMO_ACCOUNTS } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { formatRoleName } from '../../utils/formatters';

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
    <header className="h-16 bg-white border-b border-slate-200/90 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40 shadow-xs">
      {/* Left: Brand & Mobile Menu */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
            className="lg:hidden text-slate-700"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-xs font-black shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-extrabold text-slate-900 leading-tight">
              {t('app.title')}
            </h1>
            <span className="text-[11px] text-slate-500 font-medium">
              {t('app.subtitle')}
            </span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Role Switcher Dropdown */}
        <div className="relative flex items-center">
          <select
            value={activeRole || 'PATIENT'}
            onChange={(e) => handleRoleChange(e.target.value)}
            disabled={isSwitching}
            aria-label={t('nav.switchRole')}
            className="pl-3 pr-8 py-1.5 rounded-lg border border-sky-200 bg-sky-50/70 text-sky-900 font-bold text-xs cursor-pointer appearance-none outline-none hover:bg-sky-100 transition"
          >
            {Object.entries(DEMO_ACCOUNTS).map(([key, acc]) => (
              <option key={key} value={key}>
                {acc.name} ({formatRoleName(key)})
              </option>
            ))}
          </select>
          <div className="absolute right-2.5 pointer-events-none text-sky-600">
            {isSwitching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </div>
        </div>

        {/* Scope Pill Badge */}
        {scope && (
          <Badge variant="slate" className="hidden md:inline-flex text-[11px] font-bold">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            {scope}
          </Badge>
        )}

        {/* Language Switcher */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLanguage(language === 'en' ? 'ta' : 'en')}
          title="Toggle English / தமிழ்"
          className="text-xs font-bold"
        >
          <Globe className="w-3.5 h-3.5 text-sky-600" />
          {language === 'en' ? 'தமிழ்' : 'English'}
        </Button>

        {/* User Profile / Logout */}
        {user && (
          <div className="flex items-center gap-2 pl-1 border-l border-slate-200">
            <div
              title={user.email}
              className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs border border-sky-200"
            >
              <User className="w-4 h-4" />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              title={t('nav.logout')}
              className="text-slate-500 hover:text-red-600"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </header>
  );
};
