"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Code2, Eye, Database, FileSearch, Settings, FlaskConical, Command, Trash2 } from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onViewChange: (view: string) => void;
  onClearLogs: () => void;
}

export default function CommandPalette({ isOpen, onClose, onViewChange, onClearLogs }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const items = [
    { id: "go-decoder", label: "Go to Decoder", category: "Navigation", icon: Code2, action: () => onViewChange("decoder"), shortcut: "⌘1" },
    { id: "go-stego", label: "Go to Stego Analyzer", category: "Navigation", icon: Eye, action: () => onViewChange("stego"), shortcut: "⌘2" },
    { id: "go-metadata", label: "Go to Metadata Explorer", category: "Navigation", icon: Database, action: () => onViewChange("metadata"), shortcut: "⌘3" },
    { id: "go-file", label: "Go to File Analyzer", category: "Navigation", icon: FileSearch, shortcut: "⌘4", action: () => onViewChange("file") },
    { id: "go-experiments", label: "Go to Experiments", category: "Navigation", icon: FlaskConical, shortcut: "⌘5", action: () => onViewChange("experiments") },
    { id: "go-settings", label: "Go to Settings", category: "Navigation", icon: Settings, shortcut: "⌘,", action: () => onViewChange("settings") },
    { id: "action-clear", label: "Clear Live Analysis Logs", category: "Actions", icon: Trash2, shortcut: "Shift+C", action: () => { onClearLogs(); onClose(); } },
  ];

  // Filter items
  const filtered = items.filter(item => 
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setSelectedIdx(0);
    }
  }, [isOpen]);

  // Handle keyboard interaction
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIdx(prev => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIdx(prev => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIdx]) {
          filtered[selectedIdx].action();
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filtered, selectedIdx, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
          />

          {/* Dialog Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -10 }}
            className="relative w-full max-w-lg bg-theme-card border border-theme-border rounded-xl shadow-2xl overflow-hidden z-10 mx-4"
          >
            {/* Search Input Bar */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-theme-border bg-theme-surface/50">
              <Search size={18} className="text-theme-muted" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={e => {
                  setQuery(e.target.value);
                  setSelectedIdx(0);
                }}
                placeholder="Type a command or navigate..."
                className="w-full bg-transparent text-sm text-theme-primary placeholder-theme-muted outline-none font-mono"
              />
              <div className="px-2 py-0.5 border border-theme-border rounded bg-theme-input text-[9px] font-mono text-theme-secondary select-none">
                ESC
              </div>
            </div>

            {/* Command List */}
            <div className="max-h-[300px] overflow-y-auto custom-scrollbar p-2 space-y-2">
              {filtered.length === 0 ? (
                <div className="p-8 text-center text-xs text-theme-muted font-mono">
                  No commands match your search query
                </div>
              ) : (
                Object.entries(
                  filtered.reduce((groups, item) => {
                    if (!groups[item.category]) groups[item.category] = [];
                    groups[item.category].push(item);
                    return groups;
                  }, {} as Record<string, typeof filtered>)
                ).map(([category, groupItems]) => (
                  <div key={category} className="space-y-1">
                    <div className="px-3 py-1 text-[9px] font-mono font-bold tracking-wider text-theme-muted uppercase">
                      {category}
                    </div>
                    {groupItems.map(item => {
                      const Icon = item.icon;
                      const globalIdx = filtered.findIndex(f => f.id === item.id);
                      const isSelected = globalIdx === selectedIdx;

                      return (
                        <div
                          key={item.id}
                          onClick={() => {
                            item.action();
                            onClose();
                          }}
                          className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors border
                            ${isSelected 
                              ? "bg-theme-accent/10 text-theme-accent border-theme-accent/25" 
                              : "text-theme-secondary hover:text-theme-primary hover:bg-theme-hover border-transparent"
                            }`}
                        >
                          <div className="flex items-center gap-3">
                            <Icon size={16} className={isSelected ? "text-theme-accent" : "text-theme-muted"} />
                            <span className="text-xs font-mono">{item.label}</span>
                          </div>
                          <span className="text-[10px] font-mono text-theme-muted bg-theme-input border border-theme-border px-2 py-0.5 rounded">
                            {item.shortcut}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ))
              )}
            </div>

            {/* Footer help */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-theme-border bg-theme-surface/50 text-[9px] font-mono text-theme-muted">
              <div className="flex gap-3">
                <span>↑↓ Navigate</span>
                <span>Enter Select</span>
              </div>
              <div className="flex items-center gap-1">
                <Command size={10} />
                <span>K / Ctrl K to toggle</span>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
