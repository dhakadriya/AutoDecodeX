"use client";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDown, CheckCircle, Lock, Unlock } from "lucide-react";
import type { DecodingStep } from "@/lib/api";

interface Props {
  steps: DecodingStep[];
  loading: boolean;
}

const STEP_COLORS = [
  { bar: "bg-cyber-blue", text: "text-cyber-blue", border: "border-cyber-blue/40" },
  { bar: "bg-cyber-purple", text: "text-cyber-purple", border: "border-cyber-purple/40" },
  { bar: "bg-cyber-green", text: "text-cyber-green", border: "border-cyber-green/40" },
  { bar: "bg-amber-400", text: "text-amber-400", border: "border-amber-400/40" },
  { bar: "bg-cyber-pink", text: "text-cyber-pink", border: "border-cyber-pink/40" },
];

function ConfidenceBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-cyber-border rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-cyber-muted w-10 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}

export default function DecodingPipeline({ steps, loading }: Props) {
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-12 gap-4"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
          className="w-10 h-10 border-2 border-cyber-blue border-t-transparent rounded-full"
        />
        <motion.p
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-cyber-blue text-sm font-mono"
        >
          Analyzing encoding layers...
        </motion.p>
      </motion.div>
    );
  }

  if (!steps.length) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-1"
    >
      <p className="text-xs text-cyber-muted uppercase tracking-widest mb-3">Decoding Pipeline</p>

      <AnimatePresence>
        {steps.map((step, i) => {
          const colors = STEP_COLORS[i % STEP_COLORS.length];
          return (
            <motion.div
              key={step.step_number}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15, duration: 0.4 }}
            >
              {/* Step card */}
              <div className={`rounded-lg border ${colors.border} bg-cyber-card p-4 space-y-3`}>
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full border ${colors.border} flex items-center justify-center`}>
                      <span className={`text-xs font-bold ${colors.text}`}>{step.step_number}</span>
                    </div>
                    <Lock size={12} className="text-cyber-muted" />
                    <span className={`text-sm font-mono font-semibold ${colors.text}`}>
                      {step.encoding_type.replace("_", " ").toUpperCase()}
                    </span>
                    <Unlock size={12} className="text-cyber-muted" />
                  </div>
                  <div className="flex items-center gap-1">
                    <CheckCircle size={12} className="text-cyber-green" />
                    <span className="text-xs text-cyber-green">decoded</span>
                  </div>
                </div>

                {/* Confidence bar */}
                <div>
                  <p className="text-xs text-cyber-muted mb-1">Detection Confidence</p>
                  <ConfidenceBar value={step.confidence} color={colors.bar} />
                </div>

                {/* Output preview */}
                <div className="bg-cyber-surface rounded p-2 border border-cyber-border">
                  <p className="text-xs text-cyber-muted mb-1">Output</p>
                  <p className="text-xs font-mono text-cyber-text break-all line-clamp-2">
                    {step.output_text}
                  </p>
                </div>

                {/* Readability score */}
                <div>
                  <p className="text-xs text-cyber-muted mb-1">Readability Score</p>
                  <ConfidenceBar value={step.score} color="bg-cyber-green" />
                </div>
              </div>

              {/* Arrow connector */}
              {i < steps.length - 1 && (
                <div className="flex justify-center py-1">
                  <motion.div
                    animate={{ y: [0, 4, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    <ArrowDown size={16} className="text-cyber-muted" />
                  </motion.div>
                </div>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </motion.div>
  );
}
