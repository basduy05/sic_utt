'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { AppHeader } from './AppHeader';
import { AppSidebar } from './AppSidebar';

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === '/landing';

  if (isLandingPage) {
    // Standalone Landing Page: No AppHeader, No AppSidebar, full scrollable viewport
    return (
      <div className="h-screen w-full overflow-y-auto overflow-x-hidden bg-[#f8fafc] relative">
        {children}
      </div>
    );
  }

  // Dashboard / App Layout
  return (
    <div className="h-screen max-h-screen overflow-hidden flex flex-col bg-[#f8fafc] text-slate-900 antialiased relative">
      {/* Top Modern Header */}
      <AppHeader />

      {/* Main Body Shell: Sidebar + Content */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <AppSidebar />

        {/* Main Content Viewport */}
        <main className="flex-1 flex flex-col min-h-0 overflow-y-auto overflow-x-hidden bg-[#f8fafc] relative">
          {children}
        </main>
      </div>
    </div>
  );
}
