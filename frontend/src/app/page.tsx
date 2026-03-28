"use client";
import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cpu, Github, Zap, RotateCcw } from "lucide-react";

import CyberInput from "@/components/CyberInput";
import SettingsPanel from "@/components/SettingsPanel";
import DetectionBadges from "@/components/DetectionBadges";
import DecodingPipeline from "@/components/DecodingPipeline";
import TerminalOutput from "@/components/TerminalOutput";

import {
  decodeText, detectText, bruteForce,
  type DecodeResponse, type Detection, type BruteForceResponse,
} from "@/lib/api";

interface Settings {
  ctfMode: boolean;
  bruteForce: "none" | "caesar" | "xor";
}

export default function Home() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DecodeResponse | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [bruteForceResult, setBruteForceResult] = useState<BruteForceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<Settings>({ ctfMode: false, bruteForce: "none" });

  // Live detection as user types (debounced)
  useEffect(() => {
    if (!input.trim() || input.length < 4) {
      setDetections([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await detectText(input);
        setDetections(res.detections);
      } catch {
        // silent fail for live detection
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [input]);

  const handleDecode = useCallback(async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setBruteForceResult(null);

    try {
      // Run brute force if enabled
      if (settings.bruteForce !== "none") {
        const bf = await bruteForce(input, settings.bruteForce);
        setBruteForceResult(bf);
      }

      const res = await decodeText(input, settings.ctfMode);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to connect to backend. Is the server running?");
    } finally {
      setLoading(false);
    }
  }, [input, settings]);

  const handleReset = () => {
    setInput("");
    setResult(null);
    setDetections([]);
    setBruteForceResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-cyber-border bg-cyber-surface/80 backdrop-blur-sm sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-blue to-cyber-purple flex items-center justify-center"
            >
              <Cpu size={16} className="text-white" />
            </motion.div>
            <div>
              <h1 className="text-lg font-bold font-mono neon-blue tracking-wider">AutoDecodeX</h1>
              <p className="text-xs text-cyber-muted">AI-Assisted Encoding Decoder</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {settings.ctfMode && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyber-green/10 border border-cyber-green/40"
              >
                <Zap size={10} className="text-cyber-green" />
                <span className="text-xs text-cyber-green font-mono">CTF MODE</span>
              </motion.div>
            )}
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyber-muted hover:text-cyber-text transition-colors"
            >
              <Github size={18} />
            </a>
          </div>
        </div>
      </motion.header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">

          {/* Left column */}
          <div className="space-y-6">
            {/* Hero text */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="space-y-1"
            >
              <h2 className="text-2xl font-bold font-mono text-cyber-text">
                Decode <span className="neon-green">anything</span>.
              </h2>
              <p className="text-sm text-cyber-muted">
                Multi-layer encoding detection with step-by-step explainability.
              </p>
            </motion.div>

            {/* Input */}
            <CyberInput
              value={input}
              onChange={setInput}
              onDecode={handleDecode}
              loading={loading}
            />

            {/* Reset */}
            {(result || bruteForceResult) && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={handleReset}
                className="flex items-center gap-2 text-xs text-cyber-muted hover:text-cyber-text transition-colors font-mono"
              >
                <RotateCcw size={12} />
                Reset
              </motion.button>
            )}

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="p-4 rounded-lg border border-red-500/40 bg-red-500/10 text-red-400 text-sm font-mono"
                >
                  ⚠ {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Live detections */}
            <AnimatePresence>
              {detections.length > 0 && !loading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <DetectionBadges detections={detections} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Pipeline */}
            <AnimatePresence>
              {(loading || (result && result.steps.length > 0)) && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="bg-cyber-surface border border-cyber-border rounded-xl p-5"
                >
                  <DecodingPipeline steps={result?.steps ?? []} loading={loading} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Output */}
            <TerminalOutput result={result} bruteForceResult={bruteForceResult} />
          </div>

          {/* Right column */}
          <div className="space-y-4">
            <SettingsPanel settings={settings} onChange={setSettings} />

            {/* Quick examples */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-cyber-surface border border-cyber-border rounded-xl p-4"
            >
              <p className="text-xs text-cyber-muted uppercase tracking-widest mb-3">Quick Examples</p>
              <div className="space-y-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.label}
                    onClick={() => { setInput(ex.value); setResult(null); setBruteForceResult(null); }}
                    className="w-full text-left p-2.5 rounded-lg border border-cyber-border bg-cyber-card
                      hover:border-cyber-blue/50 hover:bg-cyber-blue/5 transition-all duration-150 group"
                  >
                    <p className="text-xs text-cyber-blue font-mono group-hover:neon-blue">{ex.label}</p>
                    <p className="text-xs text-cyber-muted truncate mt-0.5">{ex.value}</p>
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Stats */}
            {result && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-3"
              >
                <p className="text-xs text-cyber-muted uppercase tracking-widest">Analysis Stats</p>
                <div className="grid grid-cols-2 gap-3">
                  <Stat label="Layers" value={result.steps.length.toString()} color="text-cyber-blue" />
                  <Stat label="Score" value={`${Math.round(result.total_score * 100)}%`} color="text-cyber-green" />
                  <Stat label="Flag" value={result.is_ctf_flag ? "YES" : "NO"} color={result.is_ctf_flag ? "text-cyber-green" : "text-cyber-muted"} />
                  <Stat label="Status" value={result.success ? "OK" : "PARTIAL"} color={result.success ? "text-cyber-green" : "text-amber-400"} />
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-cyber-border py-4 text-center">
        <p className="text-xs text-cyber-muted font-mono">
          AutoDecodeX v1.0.0 — Built for CTF players &amp; cybersecurity students
        </p>
      </footer>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-cyber-card rounded-lg p-3 border border-cyber-border">
      <p className="text-xs text-cyber-muted">{label}</p>
      <p className={`text-sm font-mono font-bold mt-1 ${color}`}>{value}</p>
    </div>
  );
}

const EXAMPLES = [
  { label: "Base64", value: "SGVsbG8gV29ybGQh" },
  { label: "Hex", value: "48656c6c6f20576f726c6421" },
  { label: "ROT13", value: "Uryyb Jbeyq!" },
  { label: "Binary", value: "01001000 01100101 01101100 01101100 01101111" },
  { label: "Morse", value: ".... . .-.. .-.. ---" },
  { label: "Multi-layer (B64→Hex)", value: "NTM2NTZjNmM2ZjIwNTc2ZjcyNmM2NA==" },
  { label: "URL Encoded", value: "Hello%20World%21" },
  { label: "CTF Flag (B64)", value: "ZmxhZ3t0ZXN0X2ZsYWd9" },
];
