'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

export type FontSizeScale = 'sm' | 'md' | 'lg';

interface ThemeContextType {
  fontSizeScale: FontSizeScale;
  setFontSizeScale: (size: FontSizeScale) => void;
  voiceEnabled: boolean;
  setVoiceEnabled: (enabled: boolean) => void;
  soundAlerts: boolean;
  setSoundAlerts: (enabled: boolean) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [fontSizeScale, setFontSizeScaleState] = useState<FontSizeScale>('md');
  const [voiceEnabled, setVoiceEnabledState] = useState<boolean>(true);
  const [soundAlerts, setSoundAlertsState] = useState<boolean>(true);
  const [isSidebarCollapsed, setIsSidebarCollapsedState] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
    const savedSize = localStorage.getItem('medibot_font_size') as FontSizeScale;
    if (savedSize && ['sm', 'md', 'lg'].includes(savedSize)) {
      setFontSizeScaleState(savedSize);
      document.documentElement.setAttribute('data-font-size', savedSize);
    } else {
      document.documentElement.setAttribute('data-font-size', 'md');
    }

    const savedVoice = localStorage.getItem('medibot_voice_enabled');
    if (savedVoice !== null) {
      setVoiceEnabledState(savedVoice === 'true');
    }

    const savedSound = localStorage.getItem('medibot_sound_alerts');
    if (savedSound !== null) {
      setSoundAlertsState(savedSound === 'true');
    }

    const savedSidebar = localStorage.getItem('medibot_sidebar_collapsed');
    if (savedSidebar !== null) {
      setIsSidebarCollapsedState(savedSidebar === 'true');
    }
  }, []);

  const setFontSizeScale = (size: FontSizeScale) => {
    setFontSizeScaleState(size);
    if (typeof window !== 'undefined') {
      localStorage.setItem('medibot_font_size', size);
      document.documentElement.setAttribute('data-font-size', size);
    }
  };

  const setVoiceEnabled = (enabled: boolean) => {
    setVoiceEnabledState(enabled);
    if (typeof window !== 'undefined') {
      localStorage.setItem('medibot_voice_enabled', String(enabled));
    }
  };

  const setSoundAlerts = (enabled: boolean) => {
    setSoundAlertsState(enabled);
    if (typeof window !== 'undefined') {
      localStorage.setItem('medibot_sound_alerts', String(enabled));
    }
  };

  const setIsSidebarCollapsed = (collapsed: boolean) => {
    setIsSidebarCollapsedState(collapsed);
    if (typeof window !== 'undefined') {
      localStorage.setItem('medibot_sidebar_collapsed', String(collapsed));
    }
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsedState((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') {
        localStorage.setItem('medibot_sidebar_collapsed', String(next));
      }
      return next;
    });
  };

  return (
    <ThemeContext.Provider
      value={{
        fontSizeScale,
        setFontSizeScale,
        voiceEnabled,
        setVoiceEnabled,
        soundAlerts,
        setSoundAlerts,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        toggleSidebar,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
