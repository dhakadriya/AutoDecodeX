"use client";
import React from "react";
import { motion } from "framer-motion";
import { Shield, Crosshair, Cpu } from "lucide-react";

interface Settings {
  ctfMode: boolean;
  bruteForce: "none" | "caesar" | "xor";
}

interface Props {
  settings: Settings;
  onChange: (s: Settings) => void;
}

function Toggle({ enabled, onToggle, label, icon: Icon, color }: {
  enabled: boolean;
  onToggle: () => void;
  label: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-3 w-full p-3 rounded-lg border border-cyber-border
        hover:border-cyber-muted transition-colors duration-200 bg-cyber-card"
    >
      <Icon size={14} className={enabled ? color : "text-cyber-muted"} />
      <span className={`text-xs font-mono flex-1 text-left ${enabled ? "text-cyber-text" : "text-cyber-muted"}`}>
        {label}
      </span>
      <motion.div
        className={`w-10 h-5 rounded-full relative transition-colors duration-200 ${enabled ? "bg-cyber-green/30 border border-cyber-green" : "bg-cyber-border"}`}
        onClick={onToggle}
      >
        <motion.div
          animate={{ x: enabled ? 20 : 2 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className={`absolute top-0.5 w-4 h-4 rounded-full ${enabled ? "bg-cyber-green" : "bg-cyber-muted"}`}
        />
      </motion.div>
    </button>
  );
}

export default function SettingsPanel({ settings, onChange }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center gap-2 mb-3">
        <Cpu size={14} className="text-cyber-purple" />
        <span className="text-xs text-cyber-muted uppercase tracking-widest">Settings</span>
      </div>

      <Toggle
        enabled={settings.ctfMode}
        onToggle={() => onChange({ ...settings, ctfMode: !settings.ctfMode })}
        label="CTF Mode"
        icon={Shield}
        color="text-cyber-green"
      />

      {/* Brute Force selector */}
      <div className="p-3 rounded-lg border border-cyber-border bg-cyber-card">
        <div className="flex items-center gap-2 mb-2">
          <Crosshair size={14} className="text-cyber-pink" />
          <span className="text-xs text-cyber-muted">Brute Force</span>
        </div>
        <div className="flex gap-2">
          {(["none", "caesar", "xor"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => onChange({ ...settings, bruteForce: mode })}
              className={`flex-1 py-1.5 text-xs font-mono rounded border transition-all duration-150
                ${settings.bruteForce === mode
                  ? "border-cyber-pink text-cyber-pink bg-cyber-pink/10"
                  : "border-cyber-border text-cyber-muted hover:border-cyber-muted"
                }`}
            >
              {mode === "none" ? "Off" : mode.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
