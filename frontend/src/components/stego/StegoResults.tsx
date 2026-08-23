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
      className="flex items-center gap-1 text-xs text-theme-muted hover:text-theme-accent transition-colors font-mono"
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
    <div className="rounded-xl border border-theme-border bg-theme-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-theme-surface hover:bg-theme-hover transition-colors"
      >
        <span className="text-xs font-mono text-theme-secondary uppercase tracking-widest">{title}</span>
        {open ? <ChevronUp size={14} className="text-theme-secondary" /> : <ChevronDown size={14} className="text-theme-secondary" />}
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
            <div className="p-4 bg-theme-card">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function EntropyBar({ label, value, max = 8 }: { label: string; value: number; max?: number }) {
  const pct = (value / max) * 100;
  const color = value > 7.5 ? "bg-theme-error" : value > 6 ? "bg-theme-warning" : "bg-theme-success";
  return (
    <div className="flex items-center gap-3 select-none">
      <span className="text-xs text-theme-secondary w-6 font-mono">{label}</span>
      <div className="flex-1 h-1.5 bg-theme-input rounded-full overflow-hidden border border-theme-border">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-theme-secondary w-10 text-right font-mono">{value.toFixed(3)}</span>
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
                ? "border-theme-error/40 bg-theme-error/10"
                : "border-theme-success/30 bg-theme-success/5"
            }`}>
              {result.entropy.suspicious
                ? <AlertTriangle size={14} className="text-theme-error shrink-0" />
                : <CheckCircle size={14} className="text-theme-success shrink-0" />
              }
              <div>
                <p className={`text-xs font-mono font-semibold ${result.entropy.suspicious ? "text-theme-error font-bold" : "text-theme-success font-bold"}`}>
                  {result.entropy.suspicious ? "⚠ Steganography likely detected" : "No obvious stego detected"}
                </p>
                <p className="text-xs text-theme-secondary mt-0.5 font-mono">
                  Likelihood: {Math.round(result.entropy.stego_likelihood * 100)}% · Chi²: {result.entropy.chi_square_score.toFixed(3)}
                </p>
              </div>
            </div>

            {/* Channel entropy */}
            <div className="space-y-2">
              <p className="text-xs text-theme-secondary font-mono select-none">Channel Entropy</p>
              {Object.entries(result.entropy.channel_entropy).map(([ch, val]) => (
                <EntropyBar key={ch} label={ch} value={val} />
              ))}
            </div>

            {/* LSB entropy */}
            <div className="space-y-2">
              <p className="text-xs text-theme-secondary font-mono select-none">LSB Entropy (near 1.0 = suspicious)</p>
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
              <div className="bg-theme-input rounded-lg p-3 border border-theme-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-theme-secondary font-mono">Extracted ASCII</span>
                  <CopyButton text={result.lsb.ascii_text} />
                </div>
                <p className="text-xs font-mono text-theme-primary break-all leading-relaxed bg-theme-surface/50 p-2 rounded border border-theme-border/50">
                  {result.lsb.ascii_text.slice(0, 400)}
                  {result.lsb.ascii_text.length > 400 && <span className="text-theme-muted">…</span>}
                </p>
              </div>
            ) : (
              <p className="text-xs text-theme-muted font-mono">No readable ASCII found in LSB data.</p>
            )}

            {result.lsb.possible_b64.length > 0 && (
              <div>
                <p className="text-xs text-theme-secondary font-mono mb-2 select-none">Possible Base64 chunks</p>
                {result.lsb.possible_b64.map((chunk, i) => (
                  <div key={i} className="flex items-center gap-2 mb-1">
                    <code className="text-xs font-mono text-theme-accent bg-theme-input px-2 py-1 rounded flex-1 truncate border border-theme-border">
                      {chunk}
                    </code>
                    <CopyButton text={chunk} />
                  </div>
                ))}
              </div>
            )}

            <div className="text-xs text-theme-secondary font-mono select-none">
              Raw hex (first 64 bytes): <span className="text-theme-accent font-mono break-all">{result.lsb.raw_bytes_hex.slice(0, 128)}</span>
            </div>
          </div>
        </Section>
      )}

      {/* Auto-Decode Pipeline */}
      {result?.auto_decode && (
        <Section title="Auto-Decode Pipeline">
          {result.auto_decode.error ? (
            <p className="text-xs text-theme-error font-mono">{result.auto_decode.error}</p>
          ) : (
            <div className="space-y-3">
              {result.auto_decode.is_ctf_flag && (
                <motion.div
                  animate={{ scale: [1, 1.01, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-theme-success/10 border border-theme-success/30 select-none"
                >
                  <Flag size={13} className="text-theme-success" />
                  <span className="text-xs text-theme-success font-mono font-bold">CTF FLAG FOUND</span>
                </motion.div>
              )}
              <div className="bg-theme-input rounded-lg p-3 border border-theme-border">
                <div className="flex items-center justify-between font-mono select-none mb-1">
                  <span className="text-xs text-theme-secondary">{result.auto_decode.path_description}</span>
                  <span className="text-xs text-theme-warning font-bold">{Math.round(result.auto_decode.total_score * 100)}%</span>
                </div>
                <p className={`text-sm font-mono break-all ${result.auto_decode.is_ctf_flag ? "text-theme-success font-bold" : "text-theme-primary"}`}>
                  {result.auto_decode.final_output}
                </p>
              </div>
              {result.auto_decode.steps && result.auto_decode.steps.length > 0 && (
                <div className="space-y-1 select-none">
                  {result.auto_decode.steps.map((s) => (
                    <div key={s.step_number} className="flex items-center gap-2 text-xs font-mono text-theme-secondary">
                      <span className="text-theme-accent">Step {s.step_number}</span>
                      <span>→</span>
                      <span className="text-theme-accent">{s.encoding_type.toUpperCase()}</span>
                      <span>({Math.round(s.confidence * 100)}%)</span>
                      <span>→</span>
                      <span className="text-theme-primary truncate max-w-[120px]">{s.output_text.slice(0, 40)}</span>
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
                className="p-3 rounded-lg border border-theme-border bg-theme-input space-y-1.5"
              >
                <div className="flex items-center justify-between font-mono select-none">
                  <span className="text-xs font-bold text-theme-accent">
                    {r.channels} · {r.bits} bit(s)
                  </span>
                  <div className="flex items-center gap-2">
                    {r.decode_result?.is_ctf_flag && (
                      <span className="text-xs text-theme-success font-bold">FLAG</span>
                    )}
                    <span className="text-xs text-theme-warning font-bold">{Math.round(r.score * 100)}%</span>
                  </div>
                </div>
                <p className="text-xs font-mono text-theme-primary break-all line-clamp-2 bg-theme-surface/55 p-2 rounded border border-theme-border/50">
                  {r.ascii_text || <span className="text-theme-muted italic">No readable text</span>}
                </p>
                {r.decode_result && (
                  <p className="text-xs font-mono text-theme-success font-bold pl-2 border-l border-theme-success/50">
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
            <p className="text-xs text-theme-secondary font-mono select-none">
              Bright regions indicate LSB anomalies — potential hidden data locations.
            </p>
            <img
              src={`data:image/png;base64,${diffMap}`}
              alt="Pixel diff map"
              className="w-full rounded-lg border border-theme-border bg-theme-input object-contain max-h-48"
            />
          </div>
        </Section>
      )}
    </div>
  );
}
