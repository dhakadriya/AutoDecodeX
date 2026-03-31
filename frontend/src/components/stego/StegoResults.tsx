"use client";
import { motion, AnimatePresence } from "framer-motion";
import { Flag, ChevronDown, ChevronUp, Copy, CheckCircle, AlertTriangle } from "lucide-react";
import { useState } from "react";
import type { StegoAnalyzeResponse, StegoBruteResult } from "@/lib/api";

interface Props {
  result: StegoAnalyzeResponse | null;
  bruteResults: StegoBruteResult[] | null;
  diffMap: string | null;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="flex items-center gap-1 text-xs text-cyber-muted hover:text-cyber-blue transition-colors"
    >
      <Copy size={11} />
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function Section({ title, children, defaultOpen = true }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-cyber-border bg-cyber-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-cyber-surface hover:bg-cyber-card transition-colors"
      >
        <span className="text-xs font-mono text-cyber-muted uppercase tracking-widest">{title}</span>
        {open ? <ChevronUp size={14} className="text-cyber-muted" /> : <ChevronDown size={14} className="text-cyber-muted" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function EntropyBar({ label, value, max = 8 }: { label: string; value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color = value > 7.5 ? "bg-red-400" : value > 6 ? "bg-amber-400" : "bg-cyber-green";
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-cyber-muted w-6 font-mono">{label}</span>
      <div className="flex-1 h-1.5 bg-cyber-border rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-cyber-muted w-10 text-right font-mono">{value.toFixed(3)}</span>
    </div>
  );
}

export default function StegoResults({ result, bruteResults, diffMap }: Props) {
  if (!result && !bruteResults) return null;

  return (
    <div className="space-y-4">
      {/* Entropy Analysis */}
      {result?.entropy && (
        <Section title="Entropy Analysis">
          <div className="space-y-3">
            {/* Stego likelihood */}
            <div className={`flex items-center gap-3 p-3 rounded-lg border ${
              result.entropy.suspicious
                ? "border-red-500/40 bg-red-500/10"
                : "border-cyber-green/30 bg-cyber-green/5"
            }`}>
              {result.entropy.suspicious
                ? <AlertTriangle size={14} className="text-red-400 shrink-0" />
                : <CheckCircle size={14} className="text-cyber-green shrink-0" />
              }
              <div>
                <p className={`text-xs font-mono font-semibold ${result.entropy.suspicious ? "text-red-400" : "text-cyber-green"}`}>
                  {result.entropy.suspicious ? "⚠ Steganography likely detected" : "No obvious stego detected"}
                </p>
                <p className="text-xs text-cyber-muted mt-0.5">
                  Likelihood: {Math.round(result.entropy.stego_likelihood * 100)}% · Chi²: {result.entropy.chi_square_score.toFixed(3)}
                </p>
              </div>
            </div>

            {/* Channel entropy */}
            <div className="space-y-2">
              <p className="text-xs text-cyber-muted">Channel Entropy</p>
              {Object.entries(result.entropy.channel_entropy).map(([ch, val]) => (
                <EntropyBar key={ch} label={ch} value={val} />
              ))}
            </div>

            {/* LSB entropy */}
            <div className="space-y-2">
              <p className="text-xs text-cyber-muted">LSB Entropy (near 1.0 = suspicious)</p>
              {Object.entries(result.entropy.lsb_entropy).map(([ch, val]) => (
                <EntropyBar key={ch} label={ch} value={val} max={1} />
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* LSB Extraction */}
      {result?.lsb && (
        <Section title={`LSB Extraction — ${result.lsb.channels} · ${result.lsb.bits_used} bit(s)`}>
          <div className="space-y-3">
            {result.lsb.ascii_text ? (
              <div className="bg-cyber-surface rounded-lg p-3 border border-cyber-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-cyber-muted">Extracted ASCII</span>
                  <CopyButton text={result.lsb.ascii_text} />
                </div>
                <p className="text-xs font-mono text-cyber-text break-all leading-relaxed">
                  {result.lsb.ascii_text.slice(0, 400)}
                  {result.lsb.ascii_text.length > 400 && <span className="text-cyber-muted">…</span>}
                </p>
              </div>
            ) : (
              <p className="text-xs text-cyber-muted">No readable ASCII found in LSB data.</p>
            )}

            {result.lsb.possible_b64.length > 0 && (
              <div>
                <p className="text-xs text-cyber-muted mb-2">Possible Base64 chunks</p>
                {result.lsb.possible_b64.map((chunk, i) => (
                  <div key={i} className="flex items-center gap-2 mb-1">
                    <code className="text-xs font-mono text-cyber-blue bg-cyber-surface px-2 py-1 rounded flex-1 truncate">
                      {chunk}
                    </code>
                    <CopyButton text={chunk} />
                  </div>
                ))}
              </div>
            )}

            <div className="text-xs text-cyber-muted font-mono">
              Raw hex (first 64 bytes): <span className="text-cyber-text">{result.lsb.raw_bytes_hex.slice(0, 128)}</span>
            </div>
          </div>
        </Section>
      )}

      {/* Auto-Decode Pipeline */}
      {result?.auto_decode && (
        <Section title="Auto-Decode Pipeline">
          {result.auto_decode.error ? (
            <p className="text-xs text-red-400 font-mono">{result.auto_decode.error}</p>
          ) : (
            <div className="space-y-3">
              {result.auto_decode.is_ctf_flag && (
                <motion.div
                  animate={{ scale: [1, 1.02, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyber-green/10 border border-cyber-green/50"
                >
                  <Flag size={13} className="text-cyber-green" />
                  <span className="text-xs text-cyber-green font-mono font-semibold">CTF FLAG FOUND</span>
                </motion.div>
              )}
              <div className="bg-cyber-surface rounded-lg p-3 border border-cyber-border">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-cyber-muted">{result.auto_decode.path_description}</span>
                  <span className="text-xs text-cyber-yellow">{Math.round(result.auto_decode.total_score * 100)}%</span>
                </div>
                <p className={`text-sm font-mono break-all ${result.auto_decode.is_ctf_flag ? "text-cyber-green neon-green" : "text-cyber-text"}`}>
                  {result.auto_decode.final_output}
                </p>
              </div>
              {result.auto_decode.steps && result.auto_decode.steps.length > 0 && (
                <div className="space-y-1">
                  {result.auto_decode.steps.map((s) => (
                    <div key={s.step_number} className="flex items-center gap-2 text-xs font-mono text-cyber-muted">
                      <span className="text-cyber-blue">Step {s.step_number}</span>
                      <span>→</span>
                      <span className="text-cyber-purple">{s.encoding_type.toUpperCase()}</span>
                      <span>({Math.round(s.confidence * 100)}%)</span>
                      <span>→</span>
                      <span className="text-cyber-text truncate">{s.output_text.slice(0, 40)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Section>
      )}

      {/* Brute Force Results */}
      {bruteResults && bruteResults.length > 0 && (
        <Section title="Brute Force — Top Candidates">
          <div className="space-y-2">
            {bruteResults.slice(0, 6).map((r, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="p-3 rounded-lg border border-cyber-border bg-cyber-surface space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-cyber-blue">
                    {r.channels} · {r.bits} bit(s)
                  </span>
                  <div className="flex items-center gap-2">
                    {r.decode_result?.is_ctf_flag && (
                      <span className="text-xs text-cyber-green font-mono">FLAG</span>
                    )}
                    <span className="text-xs text-cyber-yellow">{Math.round(r.score * 100)}%</span>
                  </div>
                </div>
                <p className="text-xs font-mono text-cyber-text break-all line-clamp-2">
                  {r.ascii_text || <span className="text-cyber-muted italic">No readable text</span>}
                </p>
                {r.decode_result && (
                  <p className="text-xs font-mono text-cyber-green">
                    → {r.decode_result.final_output.slice(0, 80)}
                  </p>
                )}
              </motion.div>
            ))}
          </div>
        </Section>
      )}

      {/* Pixel Diff Map */}
      {diffMap && (
        <Section title="Pixel Difference Map" defaultOpen={false}>
          <div className="space-y-2">
            <p className="text-xs text-cyber-muted">
              Bright regions indicate LSB anomalies — potential hidden data locations.
            </p>
            <img
              src={`data:image/png;base64,${diffMap}`}
              alt="Pixel diff map"
              className="w-full rounded-lg border border-cyber-border object-contain max-h-48"
            />
          </div>
        </Section>
      )}
    </div>
  );
}
