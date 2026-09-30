import React, { useState } from 'react';
import { Header } from './Header';
import { Navigation } from './Navigation';
import { UnifiedAiAssistant } from '../ai/UnifiedAiAssistant';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      {/* Top Application Header */}
      <Header
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onToggleAi={() => setAiOpen(!aiOpen)}
        aiOpen={aiOpen}
      />

      {/* Main Flex Area */}
      <div className="flex flex-1 relative">
        {/* Desktop Sticky Navigation Sidebar */}
        <aside className="hidden lg:flex w-64 bg-white border-r border-slate-200/90 flex-col sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto z-30 shrink-0">
          <Navigation />
        </aside>

        {/* Mobile Slide-in Drawer */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs lg:hidden animate-fade-in"
            onClick={() => setSidebarOpen(false)}
          >
            <div
              className="w-72 max-w-[85vw] h-full bg-white shadow-2xl flex flex-col overflow-y-auto animate-scale-in"
              onClick={(e) => e.stopPropagation()}
            >
              <Navigation onItemClick={() => setSidebarOpen(false)} />
            </div>
          </div>
        )}

        {/* Primary Page Content Area (Full-Width Responsive Desktop Layout) */}
        <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6 min-w-0 overflow-x-hidden">
          {children}
        </main>

        {/* Desktop Docked AI Copilot Rail (Non-obstructive Intelligence Workspace) */}
        {aiOpen && (
          <aside className="hidden xl:flex w-[400px] shrink-0 border-l border-slate-200/90 bg-white sticky top-16 h-[calc(100vh-4rem)] flex-col z-30 shadow-xs">
            <UnifiedAiAssistant docked isOpen={true} onClose={() => setAiOpen(false)} />
          </aside>
        )}
      </div>

      {/* Mobile & Tablet Slide-over AI Copilot Drawer */}
      <div className="xl:hidden">
        <UnifiedAiAssistant isOpen={aiOpen} onClose={() => setAiOpen(false)} onOpen={() => setAiOpen(true)} />
      </div>
    </div>
  );
};
