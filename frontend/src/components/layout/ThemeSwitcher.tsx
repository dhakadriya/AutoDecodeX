"use client";
import { useTheme, type Theme } from "@/context/ThemeContext";
import { Sun, Moon, Monitor, Terminal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

export default function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  const options: { id: Theme; label: string; icon: any }[] = [
    { id: "light", label: "Light Mode", icon: Sun },
    { id: "dark", label: "Dark Mode", icon: Moon },
    { id: "cyber", label: "Cyber Mode", icon: Terminal },
    { id: "system", label: "System Default", icon: Monitor },
  ];

  const currentOption = options.find((o) => o.id === theme) || options[2];
  const Icon = currentOption.icon;

  return (
    <div className="relative z-30">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-theme-border bg-theme-surface hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-colors text-xs font-mono select-none"
      >
        <Icon size={14} className="text-theme-accent" />
        <span className="capitalize">{theme === "system" ? "System" : theme}</span>
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* Click-out overlay */}
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            
            <motion.div
              initial={{ opacity: 0, y: 8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 w-44 rounded-xl border border-theme-border bg-theme-card p-1 shadow-xl z-20"
            >
              {options.map((opt) => {
                const OptIcon = opt.icon;
                const active = theme === opt.id;

                return (
                  <button
                    key={opt.id}
                    onClick={() => {
                      setTheme(opt.id);
                      setOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors text-xs font-mono
                      ${active 
                        ? "bg-theme-accent/10 text-theme-accent font-bold border border-theme-accent/20" 
                        : "text-theme-secondary hover:text-theme-primary hover:bg-theme-hover border border-transparent"
                      }`}
                  >
                    <OptIcon size={14} className={active ? "text-theme-accent" : "text-theme-muted"} />
                    <span>{opt.label}</span>
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
