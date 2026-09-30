import React from 'react';
import { AppShell } from '../layout/AppShell';

/** Kept for backwards compatibility: the application layout is now the AppShell (components/layout). */
export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => <AppShell>{children}</AppShell>;
