import React, { useState } from 'react';
import { Header } from './Header';
import { Navigation } from './Navigation';
import { UnifiedAiAssistant } from '../ai/UnifiedAiAssistant';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-main)',
        color: 'var(--text-main)',
      }}
    >
      {/* Top Header */}
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Content Area */}
      <div style={{ display: 'flex', flex: 1, position: 'relative' }}>
        {/* Desktop Sidebar */}
        <aside
          className="desktop-sidebar"
          style={{
            width: '260px',
            backgroundColor: '#ffffff',
            borderRight: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            position: 'sticky',
            top: '64px',
            height: 'calc(100vh - 64px)',
            overflowY: 'auto',
          }}
        >
          <Navigation />
        </aside>

        {/* Mobile Slide-in Drawer */}
        {sidebarOpen && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 800,
              backgroundColor: 'rgba(15, 23, 42, 0.5)',
              backdropFilter: 'blur(3px)',
            }}
            onClick={() => setSidebarOpen(false)}
          >
            <div
              style={{
                width: '280px',
                height: '100%',
                backgroundColor: '#ffffff',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                display: 'flex',
                flexDirection: 'column',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <Navigation onItemClick={() => setSidebarOpen(false)} />
            </div>
          </div>
        )}

        {/* Primary Page Content with Dedicated Bottom Safe Area for Floating Controls */}
        <main
          style={{
            flex: 1,
            padding: '1.5rem',
            paddingBottom: '6rem',
            maxWidth: '1440px',
            margin: '0 auto',
            width: '100%',
            overflowX: 'hidden',
          }}
        >
          {children}
        </main>
      </div>

      {/* Unified Context-Aware AI Assistant */}
      <UnifiedAiAssistant />
    </div>
  );
};
