"use client";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings as SettingsIcon, Save, RotateCcw } from "lucide-react";
import { useTheme, type Theme } from "@/context/ThemeContext";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";

interface SettingsWorkspaceProps {
  onLog: (type: LogEntry["type"], message: string) => void;
}

interface AppSettings {
  theme: Theme;
  accentColor: "cyan" | "purple" | "green" | "pink";
  confidenceThreshold: number;
  recursionDepth: number;
  apiEndpoint: string;
  exportFormat: "json" | "txt" | "html";
  autoDecodeMetadata: boolean;
  showLiveAnalysis: boolean;
  enableKeyboardShortcuts: boolean;
  ctfMode: boolean;
}

const DEFAULT_SETTINGS: AppSettings = {
  theme: "cyber",
  accentColor: "cyan",
  confidenceThreshold: 75,
  recursionDepth: 10,
  apiEndpoint: "/api",
  exportFormat: "json",
  autoDecodeMetadata: true,
  showLiveAnalysis: true,
  enableKeyboardShortcuts: true,
  ctfMode: false,
};

export default function SettingsWorkspace({ onLog }: SettingsWorkspaceProps) {
  const { setTheme: setGlobalTheme } = useTheme();
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("autodecodex_settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      } catch (error) {
        onLog("error", "Failed to load settings");
      }
    }
  }, [onLog]);

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const saveSettings = () => {
    try {
      localStorage.setItem("autodecodex_settings", JSON.stringify(settings));
      setGlobalTheme(settings.theme); // Update global theme
      setHasChanges(false);
      onLog("success", "Settings saved successfully");
    } catch (error) {
      onLog("error", "Failed to save settings");
    }
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
    setGlobalTheme(DEFAULT_SETTINGS.theme);
    setHasChanges(true);
    onLog("info", "Settings reset to defaults");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="h-full flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15">
            <SettingsIcon size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-theme-primary">Settings</h2>
            <p className="text-xs text-theme-secondary">Configure AutoDecodeX preferences</p>
          </div>
        </div>

        <div className="flex gap-2">
          <motion.button
            onClick={resetSettings}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-4 py-2 rounded-lg bg-theme-surface hover:bg-theme-hover border border-theme-border text-theme-primary text-xs font-mono transition-all flex items-center gap-2"
          >
            <RotateCcw size={14} />
            Reset
          </motion.button>
          <motion.button
            onClick={saveSettings}
            disabled={!hasChanges}
            whileHover={{ scale: hasChanges ? 1.02 : 1 }}
            whileTap={{ scale: hasChanges ? 0.98 : 1 }}
            className="px-4 py-2 rounded-lg bg-theme-gradient hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-mono font-bold transition-all flex items-center gap-2 shadow-lg shadow-theme-accent/15"
          >
            <Save size={14} />
            {hasChanges ? "Save Changes" : "Saved"}
          </motion.button>
        </div>
      </div>

      {/* Settings Groups */}
      <div className="space-y-6">
        {/* Appearance */}
        <div className="bg-theme-surface rounded-xl border border-theme-border p-6 space-y-4">
          <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Appearance</h3>

          <div>
            <label className="text-xs text-theme-secondary block mb-2 font-mono">Theme</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {(["dark", "light", "cyber", "system"] as const).map(themeOpt => (
                <button
                  key={themeOpt}
                  onClick={() => updateSetting("theme", themeOpt)}
                  className={`py-2 px-4 rounded-lg border text-xs font-mono capitalize transition-all
                    ${settings.theme === themeOpt
                      ? "border-theme-accent bg-theme-accent/10 text-theme-accent font-bold"
                      : "border-theme-border bg-theme-input text-theme-secondary hover:border-theme-border/50"
                    }`}
                >
                  {themeOpt}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs text-theme-secondary block mb-2 font-mono">Accent Color</label>
            <div className="grid grid-cols-4 gap-2">
              {(["cyan", "purple", "green", "pink"] as const).map(color => (
                <button
                  key={color}
                  onClick={() => updateSetting("accentColor", color)}
                  className={`h-10 rounded-lg border-2 transition-all capitalize
                    ${settings.accentColor === color ? "border-theme-primary scale-105" : "border-transparent opacity-60 hover:opacity-100"}
                    ${color === "cyan" && "bg-gradient-to-br from-cyan-400 to-cyan-600"}
                    ${color === "purple" && "bg-gradient-to-br from-purple-400 to-purple-600"}
                    ${color === "green" && "bg-gradient-to-br from-green-400 to-green-600"}
                    ${color === "pink" && "bg-gradient-to-br from-pink-400 to-pink-600"}
                  `}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Decoding Engine */}
        <div className="bg-theme-surface rounded-xl border border-theme-border p-6 space-y-4">
          <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Decoding Engine</h3>

          <div>
            <div className="flex justify-between mb-2 font-mono">
              <label className="text-xs text-theme-secondary">Confidence Threshold</label>
              <span className="text-xs text-theme-accent font-bold">{settings.confidenceThreshold}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={settings.confidenceThreshold}
              onChange={e => updateSetting("confidenceThreshold", Number(e.target.value))}
              className="w-full accent-theme-accent bg-theme-border h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-theme-muted mt-1 font-mono">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-2 font-mono">
              <label className="text-xs text-theme-secondary">Maximum Recursion Depth</label>
              <span className="text-xs text-theme-accent font-bold">{settings.recursionDepth}</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={settings.recursionDepth}
              onChange={e => updateSetting("recursionDepth", Number(e.target.value))}
              className="w-full accent-theme-accent bg-theme-border h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-theme-muted mt-1 font-mono">
              <span>1</span>
              <span>10</span>
              <span>20</span>
            </div>
          </div>
        </div>

        {/* API & Export */}
        <div className="bg-theme-surface rounded-xl border border-theme-border p-6 space-y-4">
          <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">API & Export</h3>

          <div>
            <label className="text-xs text-theme-secondary block mb-2 font-mono">API Endpoint</label>
            <input
              type="text"
              value={settings.apiEndpoint}
              onChange={e => updateSetting("apiEndpoint", e.target.value)}
              className="w-full px-3 py-2 bg-theme-input border border-theme-border rounded-lg text-xs text-theme-primary font-mono outline-none focus:border-theme-accent transition-colors"
              placeholder="http://localhost:8000/api"
            />
          </div>

          <div>
            <label className="text-xs text-theme-secondary block mb-2 font-mono">Default Export Format</label>
            <div className="grid grid-cols-3 gap-2">
              {(["json", "txt", "html"] as const).map(format => (
                <button
                  key={format}
                  onClick={() => updateSetting("exportFormat", format)}
                  className={`py-2 px-4 rounded-lg border text-xs font-mono uppercase transition-all
                    ${settings.exportFormat === format
                      ? "border-theme-accent bg-theme-accent/10 text-theme-accent font-bold"
                      : "border-theme-border bg-theme-input text-theme-secondary hover:border-theme-border/50"
                    }`}
                >
                  {format}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="bg-theme-surface rounded-xl border border-theme-border p-6 space-y-4">
          <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Features</h3>

          {[
            { key: "autoDecodeMetadata" as const, label: "Auto-decode metadata values", desc: "Automatically decode encoded metadata fields" },
            { key: "showLiveAnalysis" as const, label: "Show live analysis feed", desc: "Display real-time analysis logs" },
            { key: "enableKeyboardShortcuts" as const, label: "Enable keyboard shortcuts", desc: "Use ⌘K and other shortcuts" },
            { key: "ctfMode" as const, label: "CTF Optimization Boost", desc: "Prioritize Base64, Hex, and ROT13 ciphers" },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-theme-border/50 hover:border-theme-border transition-colors">
              <div className="flex-1 pr-4">
                <p className="text-sm text-theme-primary font-mono">{label}</p>
                <p className="text-xs text-theme-muted mt-0.5">{desc}</p>
              </div>
              <button
                onClick={() => updateSetting(key, !settings[key])}
                className={`ml-4 w-12 h-6 rounded-full relative transition-all ${
                  settings[key] ? "bg-theme-accent/20 border-2 border-theme-accent" : "bg-theme-hover border-2 border-theme-border"
                }`}
              >
                <motion.div
                  animate={{ x: settings[key] ? 24 : 2 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  className={`absolute top-0.5 w-4 h-4 rounded-full ${
                    settings[key] ? "bg-theme-accent" : "bg-theme-muted"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>

        {/* Keyboard Shortcuts */}
        <div className="bg-theme-surface rounded-xl border border-theme-border p-6 space-y-3">
          <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Keyboard Shortcuts</h3>
          
          <div className="space-y-2">
            {[
              { keys: ["⌘", "1"], desc: "Open Decoder" },
              { keys: ["⌘", "2"], desc: "Open Stego Analyzer" },
              { keys: ["⌘", "3"], desc: "Open Metadata Explorer" },
              { keys: ["⌘", "4"], desc: "Open File Analyzer" },
              { keys: ["⌘", "5"], desc: "Open Experiments" },
              { keys: ["⌘", ","], desc: "Open Settings" },
              { keys: ["⌘", "K"], desc: "Command Palette" },
            ].map((shortcut, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <span className="text-theme-secondary font-mono">{shortcut.desc}</span>
                <div className="flex gap-1">
                  {shortcut.keys.map((key, i) => (
                    <span key={i} className="px-2 py-1 bg-theme-input border border-theme-border rounded text-theme-primary font-mono text-[10px]">
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
