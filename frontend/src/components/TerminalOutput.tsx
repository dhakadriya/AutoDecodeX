"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { Copy, Flag, Terminal } from "lucide-react";
import type { DecodeResponse, BruteForceResponse } from "@/lib/api";

interface Props {
  result: DecodeResponse | null;
  bruteForceResult: BruteForceResponse | null;
}

function useTypingEffect(text: string, speed = 12) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    setDisplayed("");
    if (!text) return;
    let i = 0;
    const interval = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(interval);
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);
  return displayed;
}

export default function TerminalOutput({ result, bruteForceResult }: Props) {
  const [copied, setCopied] = useState(false);
  const displayedOutput = useTypingEffect(result?.final_output ?? "");

  const handleCopy = () => {
    if (result?.final_output) {
      navigator.clipboard.writeText(result.final_output);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!result && !bruteForceResult) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-4"
    >
      {/* Main decode result */}
      {result && (
        <div className="rounded-xl border border-cyber-border bg-cyber-card overflow-hidden">
          {/* Terminal header */}
          <div className="flex items-center justify-between px-4 py-2 bg-cyber-surface border-b border-cyber-border">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-cyber-green" />
              <span className="text-xs text-cyber-muted font-mono">output.txt</span>
              {result.is_ctf_flag && (
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyber-green/20 border border-cyber-green/50"
                >
                  <Flag size={10} className="text-cyber-green" />
                  <span className="text-xs text-cyber-green font-mono">CTF FLAG</span>
                </motion.div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-cyber-muted">
                score: <span className="text-cyber-yellow">{Math.round(result.total_score * 100)}%</span>
              </span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-cyber-muted hover:text-cyber-blue transition-colors"
              >
                <Copy size={12} />
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

          {/* Terminal body */}
          <div className="p-4 font-mono text-sm min-h-[80px]">
            <div className="flex gap-2 text-cyber-muted text-xs mb-2">
              <span className="text-cyber-green">$</span>
              <span>autodecodex decode --input &lt;encoded&gt;</span>
            </div>
            <div className="text-cyber-muted text-xs mb-1">{result.path_description}</div>
            <div className="mt-3">
              <span className="text-cyber-muted text-xs">Result: </span>
              <span className={`text-sm break-all ${result.is_ctf_flag ? "text-cyber-green neon-green" : "text-cyber-text"}`}>
                {displayedOutput}
                {displayedOutput.length < (result.final_output?.length ?? 0) && (
                  <span className="animate-pulse text-cyber-green">█</span>
                )}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Brute force results */}
      {bruteForceResult && bruteForceResult.results.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-xl border border-cyber-pink/30 bg-cyber-card overflow-hidden"
        >
          <div className="flex items-center gap-2 px-4 py-2 bg-cyber-surface border-b border-cyber-border">
            <span className="text-xs text-cyber-pink font-mono uppercase tracking-widest">
              Brute Force — {bruteForceResult.mode.toUpperCase()} — Top Results
            </span>
          </div>
          <div className="p-3 space-y-2">
            <AnimatePresence>
              {bruteForceResult.results.slice(0, 8).map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3 p-2 rounded bg-cyber-surface border border-cyber-border"
                >
                  <span className="text-xs text-cyber-muted w-20 shrink-0 font-mono">
                    {bruteForceResult.mode === "caesar"
                      ? `shift=${r.shift}`
                      : `key=${r.key_hex}`}
                  </span>
                  <span className="text-xs font-mono text-cyber-text flex-1 truncate">{r.decoded}</span>
                  <div className="flex items-center gap-1 shrink-0">
                    <div className="w-16 h-1 bg-cyber-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-cyber-pink rounded-full"
                        style={{ width: `${r.score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-cyber-muted">{Math.round(r.score * 100)}%</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
