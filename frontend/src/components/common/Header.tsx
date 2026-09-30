import React, { useState } from 'react';
import { 
  Hospital, Globe, User, LogOut, ChevronDown, 
  Menu, ShieldCheck, RefreshCw, Sparkles, Building2,
  Stethoscope, Layers, Bot, Activity
} from 'lucide-react';
import { useAuth, DEMO_ACCOUNTS } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { formatRoleName, formatScopeLevel } from '../../utils/formatters';

interface HeaderProps {
  onToggleSidebar?: () => void;
  onToggleAi?: () => void;
  aiOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar, onToggleAi, aiOpen }) => {
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
    <header className="h-16 bg-white border-b border-slate-200/90 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40 shadow-2xs backdrop-blur-md">
      {/* Left: Brand & Mobile Menu */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleSidebar}
            aria-label={t('nav.navigation') || 'Toggle Navigation'}
            className="lg:hidden text-slate-700"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-xs font-black shrink-0"
            style={{ background: 'linear-gradient(135deg, #5aa9e6 0%, #7fc8f8 100%)' }}
          >
            <Hospital className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-extrabold text-slate-900 tracking-tight leading-tight">
                Med2Us
              </h1>
              <span className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 tracking-wider">
                GOVT OF TAMIL NADU
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium block truncate max-w-[200px] sm:max-w-none">
              Connected Healthcare &amp; Resilient Medical Supply
            </span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* AI Copilot Toggle Button (Native intelligence integration) */}
        {onToggleAi && (
          <Button
            variant={aiOpen ? "primary" : "outline"}
            size="sm"
            onClick={onToggleAi}
            title={aiOpen ? "Collapse Med2Us Copilot" : "Open Med2Us Clinical Copilot"}
            className={`hidden sm:inline-flex items-center gap-1.5 h-8 px-2.5 text-xs font-bold transition-all shadow-2xs ${
              aiOpen 
                ? 'bg-sky-600 text-white border-sky-600' 
                : 'text-slate-700 bg-white border-slate-200 hover:border-sky-300 hover:text-sky-700'
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-sky-500" />
            <span>Med2Us Copilot</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          </Button>
        )}

        {/* Role Switcher Dropdown */}
        <div className="relative flex items-center">
          <select
            value={activeRole || 'PATIENT'}
            onChange={(e) => handleRoleChange(e.target.value)}
            disabled={isSwitching}
            aria-label={t('nav.switchRole') || 'Switch Role'}
            className="pl-3 pr-8 py-1.5 rounded-lg border border-sky-200 bg-sky-50/70 text-sky-950 font-bold text-xs cursor-pointer appearance-none outline-none hover:bg-sky-100 transition focus:ring-2 focus:ring-sky-500 shadow-2xs"
          >
            {Object.entries(DEMO_ACCOUNTS).map(([key, acc]) => (
              <option key={key} value={key}>
                {acc.name} ({formatRoleName(key, t)})
              </option>
            ))}
          </select>
          <div className="absolute right-2.5 pointer-events-none text-sky-600">
            {isSwitching ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </div>
        </div>

        {/* Scope Pill Badge */}
        {scope && (
          <Badge variant="outline" className="hidden md:inline-flex text-[11px] font-bold text-slate-700 bg-slate-50 gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            <span>{scope.toUpperCase()} SCOPE</span>
          </Badge>
        )}

        {/* Trilingual Language Selector */}
        <div className="relative flex items-center">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as any)}
            aria-label={t('nav.language') || 'Select Language'}
            className="pl-7 pr-6 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-800 font-bold text-xs cursor-pointer appearance-none outline-none hover:bg-slate-50 transition shadow-2xs focus:ring-2 focus:ring-sky-500"
          >
            <option value="en">English</option>
            <option value="ta">தமிழ்</option>
            <option value="hi">हिन्दी</option>
          </select>
          <Globe className="w-3.5 h-3.5 text-sky-600 absolute left-2 pointer-events-none" />
          <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 pointer-events-none" />
        </div>

        {/* User Profile / Logout */}
        {user && (
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
            <div
              title={user.email}
              className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-xs border border-sky-200 shadow-2xs"
            >
              <User className="w-4 h-4" />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              title={t('nav.logout') || 'Sign Out'}
              className="text-slate-500 hover:text-red-600 hover:bg-red-50"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </header>
  );
};
