"use client";
import React, { createContext, useContext, useState, useEffect } from "react";

export type Theme = "light" | "dark" | "cyber" | "system";

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: "light" | "dark" | "cyber";
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("cyber");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark" | "cyber">("cyber");

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("autodecodex_settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.theme) {
          setThemeState(parsed.theme);
        }
      } catch (e) {
        // ignore
      }
    }
  }, []);

  useEffect(() => {
    // Resolve theme
    let currentTheme: "light" | "dark" | "cyber" = "cyber";
    if (theme === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      currentTheme = isDark ? "dark" : "light";
    } else {
      currentTheme = theme;
    }

    setResolvedTheme(currentTheme);

    // Apply attribute to document element
    document.documentElement.setAttribute("data-theme", currentTheme);
  }, [theme]);

  // Sync with system preference changes if system theme is selected
  useEffect(() => {
    if (theme !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e: MediaQueryListEvent) => {
      const resolved = e.matches ? "dark" : "light";
      setResolvedTheme(resolved);
      document.documentElement.setAttribute("data-theme", resolved);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    // Persist in localStorage settings
    try {
      const saved = localStorage.getItem("autodecodex_settings");
      const settings = saved ? JSON.parse(saved) : {};
      settings.theme = newTheme;
      localStorage.setItem("autodecodex_settings", JSON.stringify(settings));
    } catch (e) {
      // ignore
    }
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
