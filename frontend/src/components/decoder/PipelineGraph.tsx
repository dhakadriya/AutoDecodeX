"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, ChevronRight, CheckCircle2, ShieldCheck } from "lucide-react";
import type { DecodingStep } from "@/lib/api";

interface PipelineGraphProps {
  steps: DecodingStep[];
  initialInput: string;
  isCtfFlag: boolean;
}

export default function PipelineGraph({ steps, initialInput, isCtfFlag }: PipelineGraphProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  // Compile all nodes: Initial -> Steps
  const nodes = [
    {
      title: "Source Input",
      type: "source",
      output: initialInput,
      confidence: 100,
      score: 0,
    },
    ...steps.map(s => ({
      title: `Step ${s.step_number}: ${s.encoding_type}`,
      type: s.encoding_type,
      output: s.output_text,
      confidence: s.confidence * 100,
      score: s.score * 100,
    })),
  ];

  return (
    <div className="space-y-6">
      {/* Visual Pipeline Node-Link view */}
      <div className="relative flex flex-col md:flex-row items-center gap-4 py-6 px-4 bg-theme-surface border border-theme-border rounded-xl overflow-x-auto custom-scrollbar">
        {nodes.map((node, idx) => (
          <div key={idx} className="flex flex-col md:flex-row items-center gap-4 shrink-0">
            {/* Connection Arrow */}
            {idx > 0 && (
              <div className="flex flex-col items-center justify-center shrink-0 select-none">
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.15 }}
                  className="flex items-center justify-center w-8 h-8 rounded-full bg-theme-accent/10 border border-theme-accent/20 text-theme-accent"
                >
                  <ArrowRight size={14} className="rotate-90 md:rotate-0" />
                </motion.div>
              </div>
            )}

            {/* Node Card */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.12 }}
              whileHover={{ scale: 1.02 }}
              onClick={() => setSelectedIdx(idx)}
              className={`cursor-pointer w-64 p-4 rounded-xl border transition-all duration-300 relative group select-none
                ${idx === selectedIdx 
                  ? "bg-theme-accent/5 border-theme-accent shadow-[0_0_15px_var(--border-color-glow)]" 
                  : "bg-theme-card border-theme-border hover:border-theme-accent/50 hover:shadow-[0_0_10px_var(--border-color-glow)]"
                }`}
            >
              {/* Glow header indicator */}
              <div className={`absolute top-0 left-0 right-0 h-1 rounded-t-xl
                ${node.type === "source" 
                  ? "bg-theme-muted" 
                  : idx === nodes.length - 1 && isCtfFlag 
                  ? "bg-theme-success"
                  : "bg-theme-accent"
                }`}
              />

              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono tracking-wider text-theme-secondary uppercase">
                  {node.type === "source" ? "Raw Input" : "Transformed"}
                </span>
                {node.type !== "source" && (
                  <span className="text-[10px] font-mono text-theme-accent bg-theme-accent/10 px-2 py-0.5 rounded-full border border-theme-accent/20">
                    {Math.round(node.confidence)}% conf
                  </span>
                )}
              </div>

              <h4 className="text-xs font-bold text-theme-primary mb-2 truncate capitalize font-mono">
                {node.title}
              </h4>

              <div className="text-[11px] font-mono text-theme-secondary bg-theme-input rounded p-2 h-14 overflow-hidden border border-theme-border break-all">
                {node.output}
              </div>

              {node.type !== "source" && (
                <div className="flex items-center justify-between mt-3 text-[10px] font-mono">
                  <span className="text-theme-secondary">Readability</span>
                  <span className={`font-bold ${node.score > 60 ? "text-theme-success" : "text-theme-warning"}`}>
                    {Math.round(node.score)}%
                  </span>
                </div>
              )}
            </motion.div>
          </div>
        ))}
      </div>

      {/* Selected Node Inspector Detail view */}
      <AnimatePresence mode="wait">
        {selectedIdx !== null && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="p-5 bg-theme-surface border border-theme-border rounded-xl space-y-4 shadow-lg"
          >
            <div className="flex justify-between items-center pb-2 border-b border-theme-border/50 select-none">
              <h4 className="text-sm font-mono font-bold text-theme-accent flex items-center gap-2">
                <ChevronRight size={16} />
                Node Inspector: {nodes[selectedIdx].title}
              </h4>
              <button 
                onClick={() => setSelectedIdx(null)}
                className="text-xs font-mono text-theme-secondary hover:text-theme-primary"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono tracking-wider text-theme-secondary uppercase block select-none">Raw Output Bytes</span>
                <div className="p-3 bg-theme-input rounded-lg border border-theme-border text-xs text-theme-secondary font-mono max-h-40 overflow-y-auto custom-scrollbar break-all">
                  {nodes[selectedIdx].output}
                </div>
              </div>

              <div className="space-y-3">
                <span className="text-[10px] font-mono tracking-wider text-theme-secondary uppercase block select-none">Layer Statistics</span>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono select-none">
                  <div className="p-3 bg-theme-card border border-theme-border rounded-lg">
                    <p className="text-theme-secondary text-[10px]">Confidence</p>
                    <p className="text-theme-primary font-bold text-base mt-1">
                      {Math.round(nodes[selectedIdx].confidence)}%
                    </p>
                  </div>
                  <div className="p-3 bg-theme-card border border-theme-border rounded-lg">
                    <p className="text-theme-secondary text-[10px]">Readability Score</p>
                    <p className="text-theme-primary font-bold text-base mt-1">
                      {Math.round(nodes[selectedIdx].score)}%
                    </p>
                  </div>
                </div>

                {selectedIdx === nodes.length - 1 && (
                  <div className={`p-3 rounded-lg flex items-center gap-3 border select-none ${
                    isCtfFlag 
                      ? "bg-theme-success/10 border-theme-success/20 text-theme-success" 
                      : "bg-theme-accent/10 border-theme-accent/20 text-theme-accent"
                  }`}>
                    {isCtfFlag ? (
                      <>
                        <ShieldCheck size={18} />
                        <span className="text-[11px] font-mono">CTF Flag Format Matched and Decoded Successfully!</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 size={18} />
                        <span className="text-[11px] font-mono">Decoded Output reached target scoring confidence.</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
