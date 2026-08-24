"use client";
import { motion } from "framer-motion";
import { 
  Code2, 
  Eye, 
  Database, 
  FileSearch, 
  Settings, 
  ChevronLeft,
  Keyboard,
  FlaskConical
} from "lucide-react";
import { useState } from "react";

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

const NAV_ITEMS = [
  { id: "decoder", label: "Decoder", icon: Code2, shortcut: "⌘1" },
  { id: "stego", label: "Stego Analyzer", icon: Eye, shortcut: "⌘2" },
  { id: "metadata", label: "Metadata Explorer", icon: Database, shortcut: "⌘3" },
  { id: "file", label: "File Analyzer", icon: FileSearch, shortcut: "⌘4" },
  { id: "experiments", label: "Experiments", icon: FlaskConical, shortcut: "⌘5" },
  { id: "settings", label: "Settings", icon: Settings, shortcut: "⌘," },
];

export default function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.div
      animate={{ width: collapsed ? 60 : 240 }}
      className="h-full bg-theme-surface border-r border-theme-border flex flex-col relative"
    >
      {/* Logo */}
      <div className="p-4 border-b border-theme-border">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: collapsed ? 0 : 1, scale: 1 }}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.3 }}
          className="flex items-center gap-3"
        >
          <motion.div 
            animate={{
              boxShadow: [
                "0 0 0px rgba(6, 182, 212, 0)",
                "0 0 10px rgba(6, 182, 212, 0.4)",
                "0 0 0px rgba(6, 182, 212, 0)"
              ]
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="w-8 h-8 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15"
          >
            <motion.div
              animate={{
                rotate: [0, -6, 6, -6, 0],
                scale: [1, 1.06, 0.97, 1.03, 1]
              }}
              transition={{
                duration: 6,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              <Code2 size={16} className="text-white" />
            </motion.div>
          </motion.div>
          {!collapsed && (
            <div>
              <h1 className="text-sm font-bold text-theme-primary font-mono tracking-wide">AutoDecodeX</h1>
            </div>
          )}
        </motion.div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all relative group border
                ${isActive 
                  ? "bg-theme-accent/10 text-theme-accent border-theme-accent/25" 
                  : "text-theme-secondary hover:text-theme-primary hover:bg-theme-hover border-transparent"
                }`}
            >
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-theme-gradient rounded-r"
                />
              )}
              
              <Icon size={18} className={isActive ? "text-theme-accent" : "text-theme-muted"} />
              
              {!collapsed && (
                <>
                  <span className="text-xs font-medium flex-1 text-left">{item.label}</span>
                  <span className="text-[10px] text-theme-muted font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.shortcut}
                  </span>
                </>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="p-3 border-t border-theme-border flex items-center justify-center hover:bg-theme-hover transition-colors"
      >
        <motion.div animate={{ rotate: collapsed ? 180 : 0 }}>
          <ChevronLeft size={16} className="text-theme-secondary" />
        </motion.div>
      </button>

      {/* Keyboard Hint */}
      {!collapsed && (
        <div className="p-3 border-t border-theme-border bg-theme-bg/50">
          <div className="flex items-center gap-2 text-[10px] text-theme-muted">
            <Keyboard size={12} className="text-theme-muted" />
            <span>Press ⌘K for commands</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
