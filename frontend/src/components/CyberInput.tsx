"use client";
import { motion } from "framer-motion";
import { useState } from "react";
import { Terminal, Zap } from "lucide-react";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onDecode: () => void;
  loading: boolean;
}

export default function CyberInput({ value, onChange, onDecode, loading }: Props) {
  const [focused, setFocused] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      {/* Header bar */}
      <div className="flex items-center gap-2 mb-2 px-1">
        <Terminal size={14} className="text-cyber-blue" />
        <span className="text-xs text-cyber-muted uppercase tracking-widest">Input Terminal</span>
        <div className="flex-1 h-px bg-cyber-border" />
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500 opacity-70" />
          <div className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
          <div className="w-2 h-2 rounded-full bg-green-500 opacity-70" />
        </div>
      </div>

      {/* Textarea wrapper */}
      <motion.div
        animate={focused ? { boxShadow: "0 0 0 1px #00d4ff, 0 0 30px rgba(0,212,255,0.2)" } : { boxShadow: "0 0 0 1px #1e1e3a" }}
        transition={{ duration: 0.2 }}
        className="relative rounded-lg overflow-hidden bg-cyber-card border border-cyber-border"
      >
        {/* Animated top border */}
        {focused && (
          <motion.div
            className="absolute top-0 left-0 h-0.5 bg-gradient-to-r from-cyber-blue via-cyber-purple to-cyber-green"
            initial={{ width: 0 }}
            animate={{ width: "100%" }}
            transition={{ duration: 0.4 }}
          />
        )}

        <div className="flex items-start gap-2 p-3">
          <span className="text-cyber-green text-xs mt-1 select-none font-mono">$&gt;</span>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) onDecode();
            }}
            placeholder="Paste encoded text here... (Ctrl+Enter to decode)"
            rows={5}
            className="flex-1 bg-transparent text-cyber-text text-sm font-mono resize-none outline-none placeholder-cyber-muted leading-relaxed"
            spellCheck={false}
          />
        </div>

        {/* Character count */}
        <div className="flex justify-between items-center px-4 py-2 border-t border-cyber-border bg-cyber-surface">
          <span className="text-xs text-cyber-muted">{value.length} chars</span>
          <span className="text-xs text-cyber-muted">Ctrl+Enter to decode</span>
        </div>
      </motion.div>

      {/* Decode button */}
      <motion.button
        onClick={onDecode}
        disabled={loading || !value.trim()}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="mt-3 w-full py-3 rounded-lg font-mono text-sm font-semibold uppercase tracking-widest
          bg-gradient-to-r from-cyber-blue/20 to-cyber-purple/20
          border border-cyber-blue/50 text-cyber-blue
          hover:border-cyber-blue hover:bg-cyber-blue/10
          disabled:opacity-40 disabled:cursor-not-allowed
          transition-all duration-200 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="w-4 h-4 border-2 border-cyber-blue border-t-transparent rounded-full"
            />
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <Zap size={14} />
            <span>Decode</span>
          </>
        )}
      </motion.button>
    </motion.div>
  );
}
