import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { readStored, useMediaQuery, writeStored } from './useMediaQuery';

const AI_OPEN_KEY = 'med2us.ai.docked';
const NAV_COLLAPSED_KEY = 'med2us.nav.collapsed';

interface ShellContextValue {
  /** Mobile navigation sheet. */
  mobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
  /** Desktop sidebar: collapsed = icon rail. Remembered. */
  navCollapsed: boolean;
  toggleNavCollapsed: () => void;
  /** True on >= xl, where the AI panel is a docked column (remembered). Below xl it is a bottom sheet (not remembered). */
  aiDockable: boolean;
  /** Whether the AI panel is currently showing (docked column on xl, bottom sheet below). */
  aiOpen: boolean;
  setAiOpen: (open: boolean) => void;
  toggleAi: () => void;
}

const ShellContext = createContext<ShellContextValue | null>(null);

export const ShellProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const aiDockable = useMediaQuery('(min-width: 1280px)');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [navCollapsed, setNavCollapsed] = useState<boolean>(() => {
    const stored = readStored(NAV_COLLAPSED_KEY);
    if (stored === '1') return true;
    if (stored === '0') return false;
    return typeof window !== 'undefined' && window.innerWidth < 1024; // md: icon rail by default
  });
  const [dockedOpen, setDockedOpen] = useState<boolean>(() => readStored(AI_OPEN_KEY) === '1');
  const [sheetOpen, setSheetOpen] = useState(false);

  const toggleNavCollapsed = useCallback(() => {
    setNavCollapsed((prev) => {
      writeStored(NAV_COLLAPSED_KEY, prev ? '0' : '1');
      return !prev;
    });
  }, []);

  const setAiOpen = useCallback(
    (open: boolean) => {
      if (aiDockable) {
        setDockedOpen(open);
        writeStored(AI_OPEN_KEY, open ? '1' : '0');
      } else {
        setSheetOpen(open);
      }
    },
    [aiDockable]
  );

  const aiOpen = aiDockable ? dockedOpen : sheetOpen;
  const toggleAi = useCallback(() => setAiOpen(!aiOpen), [setAiOpen, aiOpen]);

  const value = useMemo<ShellContextValue>(
    () => ({ mobileNavOpen, setMobileNavOpen, navCollapsed, toggleNavCollapsed, aiDockable, aiOpen, setAiOpen, toggleAi }),
    [mobileNavOpen, navCollapsed, toggleNavCollapsed, aiDockable, aiOpen, setAiOpen, toggleAi]
  );

  return <ShellContext.Provider value={value}>{children}</ShellContext.Provider>;
};

export function useShell(): ShellContextValue {
  const ctx = useContext(ShellContext);
  if (!ctx) throw new Error('useShell must be used within an AppShell');
  return ctx;
}
