import React, { createContext, useContext, useState, useEffect } from 'react';
import type { UserProfile, RoleCode, ScopeLevel, NavigationItem } from '../services/types';
import { api, setTokens, clearTokens, getAccessToken } from '../services/api';

export const DEMO_ACCOUNTS: Record<string, { email: string; name: string; role: RoleCode; defaultPath: string }> = {
  PATIENT: {
    email: 'patient@demo.smarthealth.com',
    name: 'Citizen / Patient',
    role: 'PATIENT',
    defaultPath: '/patient',
  },
  DOCTOR: {
    email: 'doctor@demo.smarthealth.com',
    name: 'Dr. Ramesh (Medical Officer)',
    role: 'DOCTOR',
    defaultPath: '/clinical/queue',
  },
  NURSE: {
    email: 'nurse@demo.smarthealth.com',
    name: 'Sister Priya (Triage Nurse)',
    role: 'NURSE',
    defaultPath: '/clinical/triage',
  },
  PHC_IN_CHARGE: {
    email: 'phc.in.charge@demo.smarthealth.com',
    name: 'Dr. Natarajan (PHC In-Charge)',
    role: 'PHC_IN_CHARGE',
    defaultPath: '/facility',
  },
  PHARMACIST: {
    email: 'pharmacist@demo.smarthealth.com',
    name: 'Kavitha (Dispensary Pharmacist)',
    role: 'PHARMACIST',
    defaultPath: '/pharmacy/dispense',
  },
  DISTRICT_HEALTH_OFFICER: {
    email: 'district.health.officer@demo.smarthealth.com',
    name: 'Dr. Sundaram (District Health Officer)',
    role: 'DISTRICT_HEALTH_OFFICER',
    defaultPath: '/district',
  },
  DISTRICT_SUPPLY_OFFICER: {
    email: 'district.supply.officer@demo.smarthealth.com',
    name: 'Anand (District Supply Chain Officer)',
    role: 'DISTRICT_SUPPLY_OFFICER',
    defaultPath: '/supply/requests',
  },
  DISTRICT_EMERGENCY_COORDINATOR: {
    email: 'district.emergency.coordinator@demo.smarthealth.com',
    name: 'Balamurugan (District Emergency Coordinator)',
    role: 'DISTRICT_EMERGENCY_COORDINATOR',
    defaultPath: '/emergency',
  },
  STATE_HEALTH_ADMIN: {
    email: 'state.health.admin@demo.smarthealth.com',
    name: 'Dr. Radhakrishnan (State Health Administrator)',
    role: 'STATE_HEALTH_ADMIN',
    defaultPath: '/state',
  },
  STATE_SUPPLY_MANAGER: {
    email: 'state.supply.manager@demo.smarthealth.com',
    name: 'Venkatesh (State Central Warehouse Manager)',
    role: 'STATE_SUPPLY_MANAGER',
    defaultPath: '/supply',
  },
  STATE_PUBLIC_HEALTH_ANALYST: {
    email: 'state.public.health.analyst@demo.smarthealth.com',
    name: 'Dr. Malathi (State Public Health Analyst)',
    role: 'STATE_PUBLIC_HEALTH_ANALYST',
    defaultPath: '/analytics',
  },
  NATIONAL_HEALTH_AUTHORITY: {
    email: 'national.health.authority@demo.smarthealth.com',
    name: 'Joint Secretary (National Health Authority)',
    role: 'NATIONAL_HEALTH_AUTHORITY',
    defaultPath: '/national',
  },
  SUPER_ADMIN: {
    email: 'super.admin@demo.smarthealth.com',
    name: 'National Platform Administrator',
    role: 'SUPER_ADMIN',
    defaultPath: '/platform',
  },
};

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeRole: RoleCode | null;
  scope: ScopeLevel | null;
  navItems: NavigationItem[];
  login: (email: string, password?: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  switchDemoRole: (roleCode: string) => Promise<{ success: boolean; path: string; error?: string }>;
  hasPermission: (permissionCode: string) => boolean;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [navItems, setNavItems] = useState<NavigationItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchNavAndUser = async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setNavItems([]);
      setIsLoading(false);
      return;
    }

    try {
      const [meRes, navRes] = await Promise.all([
        api.get<UserProfile>('/auth/me'),
        api.get<{ items: NavigationItem[] }>('/navigation/me'),
      ]);

      if (meRes.data) {
        setUser(meRes.data);
      } else {
        clearTokens();
        setUser(null);
      }

      if (navRes.data?.items) {
        setNavItems(navRes.data.items);
      }
    } catch {
      clearTokens();
      setUser(null);
      setNavItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNavAndUser();
  }, []);

  const login = async (email: string, password = 'Demo@Health2026') => {
    setIsLoading(true);
    const res = await api.post<{ access_token: string; refresh_token?: string; user?: UserProfile }>('/auth/login', {
      email,
      password,
    });

    if (res.data) {
      const tokens = res.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      await fetchNavAndUser();
      return { success: true };
    }

    setIsLoading(false);
    return {
      success: false,
      error: res.error?.detail || 'Authentication failed. Please verify credentials.',
    };
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout', {});
    } catch {
      // Ignore network errors on logout
    } finally {
      clearTokens();
      setUser(null);
      setNavItems([]);
    }
  };

  const switchDemoRole = async (roleCode: string): Promise<{ success: boolean; path: string; error?: string }> => {
    const account = DEMO_ACCOUNTS[roleCode];
    if (!account) return { success: false, path: '/login', error: `Unknown role code: ${roleCode}` };

    const res = await login(account.email, 'Demo@Health2026');
    if (res.success) {
      return { success: true, path: account.defaultPath };
    }
    return { success: false, path: '/login', error: res.error || 'Sign-in failed. Please check your details and try again.' };
  };

  const hasPermission = (permissionCode: string): boolean => {
    if (!user) return false;
    const isSuper = user.roles?.some((r: any) => 
      (typeof r === 'string' ? r : r.role_code) === 'SUPER_ADMIN'
    );
    if (isSuper) return true;
    return user.permissions?.includes(permissionCode) || false;
  };

  const rawRole = user?.roles?.[0];
  const activeRole: RoleCode | null = (
    typeof rawRole === 'string' ? rawRole : rawRole?.role_code
  ) as RoleCode || null;

  const scope: ScopeLevel | null = (
    typeof rawRole === 'object' && rawRole ? rawRole.scope_level : null
  ) as ScopeLevel || null;

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        activeRole,
        scope,
        navItems,
        login,
        logout,
        switchDemoRole,
        hasPermission,
        refreshUserData: fetchNavAndUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
