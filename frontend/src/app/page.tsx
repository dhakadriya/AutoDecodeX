"use client";
import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

import Sidebar from "@/components/layout/Sidebar";
import InspectorPanel from "@/components/layout/InspectorPanel";
import LiveAnalysisFeed, { type LogEntry } from "@/components/layout/LiveAnalysisFeed";
import CommandPalette from "@/components/layout/CommandPalette";
import ThemeSwitcher from "@/components/layout/ThemeSwitcher";

// Workspaces
import DecoderWorkspace from "@/components/workspaces/DecoderWorkspace";
import StegoAnalyzer from "@/components/stego/StegoAnalyzer";
import MetadataWorkspace from "@/components/workspaces/MetadataWorkspace";
import FileAnalyzerWorkspace from "@/components/workspaces/FileAnalyzerWorkspace";
import SettingsWorkspace from "@/components/workspaces/SettingsWorkspace";
import ExperimentsWorkspace from "@/components/workspaces/ExperimentsWorkspace";
import InvestigationWorkspace from "@/components/workspaces/InvestigationWorkspace";

export default function Home() {
  const [activeView, setActiveView] = useState("decoder");
  const [inspectorData, setInspectorData] = useState<any>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const addLog = useCallback((type: LogEntry["type"], message: string) => {
    const newLog: LogEntry = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      message,
      timestamp: Date.now(),
    };
    setLogs((prev) => [...prev, newLog]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleGlobalShortcuts = (e: KeyboardEvent) => {
      let enabled = true;
      try {
        const saved = localStorage.getItem("autodecodex_settings");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed.enableKeyboardShortcuts !== undefined) {
            enabled = !!parsed.enableKeyboardShortcuts;
          }
        }
      } catch (err) {
        // ignore
      }

      if (!enabled) return;

      const isMac = typeof window !== "undefined" && navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdKey = isMac ? e.metaKey : e.ctrlKey;

      // Cmd/Ctrl + K toggle command palette
      if (cmdKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      }

      // Nav views: Cmd/Ctrl + 1/2/3/4/5/,
      if (cmdKey && e.key === '1') {
        e.preventDefault();
        setActiveView("decoder");
      }
      if (cmdKey && e.key === '2') {
        e.preventDefault();
        setActiveView("stego");
      }
      if (cmdKey && e.key === '3') {
        e.preventDefault();
        setActiveView("metadata");
      }
      if (cmdKey && e.key === '4') {
        e.preventDefault();
        setActiveView("file");
      }
      if (cmdKey && e.key === '5') {
        e.preventDefault();
        setActiveView("experiments");
      }
      if (cmdKey && e.key === ',') {
        e.preventDefault();
        setActiveView("settings");
      }

      // Action clear: Shift + C
      if (e.shiftKey && e.key === 'C') {
        e.preventDefault();
        clearLogs();
        addLog("info", "Live logs cleared via shortcut.");
      }
    };

    window.addEventListener("keydown", handleGlobalShortcuts);
    return () => window.removeEventListener("keydown", handleGlobalShortcuts);
  }, [clearLogs, addLog]);

  return (
    <div className="h-screen flex bg-theme-bg text-theme-primary overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,var(--border-color-glow),transparent_50%)] opacity-40" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,var(--border-color-glow),transparent_50%)] opacity-30" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(6,182,212,0.015)_1px,transparent_1px),linear-gradient(to_bottom,rgba(6,182,212,0.015)_1px,transparent_1px)] bg-[size:4rem_4rem]" />
      </div>

      {/* Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onViewChange={setActiveView}
        onClearLogs={clearLogs}
      />

      {/* 3-Panel Layout */}
      <div className="relative z-10 flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar activeView={activeView} onViewChange={setActiveView} />

        {/* Main Workspace */}
        <div className="flex-1 flex flex-col overflow-hidden bg-theme-bg">
          {/* Top Header bar */}
          <header className="h-14 border-b border-theme-border bg-theme-surface/30 backdrop-blur-md px-6 flex items-center justify-between shrink-0 select-none">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-mono font-bold tracking-wider text-theme-secondary uppercase">
                Forensic Node: {activeView.replace("go-", "").toUpperCase()}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-1.5 text-[10px] font-mono text-theme-muted bg-theme-bg border border-theme-border px-2 py-1 rounded-md">
                <span>Press</span>
                <kbd className="bg-theme-hover border border-theme-border px-1 rounded text-theme-secondary text-[9px] font-sans">⌘</kbd>
                <kbd className="bg-theme-hover border border-theme-border px-1 rounded text-theme-secondary text-[9px] font-sans">K</kbd>
                <span>for commands</span>
              </div>
              <ThemeSwitcher />
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
            <AnimatePresence mode="wait">
              {activeView === "decoder" && (
                <DecoderWorkspace
                  key="decoder"
                  onInspectorUpdate={setInspectorData}
                  onLog={addLog}
                  onClearLogs={clearLogs}
                />
              )}
              {activeView === "stego" && (
                <motion.div
                  key="stego"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="h-full"
                >
                  <StegoAnalyzer />
                </motion.div>
              )}
              {activeView === "metadata" && (
                <MetadataWorkspace
                  key="metadata"
                  onInspectorUpdate={setInspectorData}
                  onLog={addLog}
                  onClearLogs={clearLogs}
                />
              )}
              {activeView === "file" && (
                <FileAnalyzerWorkspace
                  key="file"
                  onInspectorUpdate={setInspectorData}
                  onLog={addLog}
                  onClearLogs={clearLogs}
                />
              )}
              {activeView === "experiments" && (
                <ExperimentsWorkspace
                  key="experiments"
                  onLog={addLog}
                />
              )}
              {activeView === "investigation" && (
                <InvestigationWorkspace
                  key="investigation"
                  onLog={addLog}
                  onClearLogs={clearLogs}
                />
              )}
              {activeView === "settings" && (
                <SettingsWorkspace
                  key="settings"
                  onLog={addLog}
                />
              )}
            </AnimatePresence>
          </div>

          {/* Live Analysis Feed - Only show when there are logs */}
          {logs.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="p-4 border-t border-white/10 bg-black/40"
            >
              <LiveAnalysisFeed logs={logs} maxHeight="150px" />
            </motion.div>
          )}
        </div>

        {/* Right Inspector Panel */}
        <div className="w-80 flex-shrink-0">
          <InspectorPanel data={inspectorData} />
        </div>
      </div>
    </div>
  );
}
