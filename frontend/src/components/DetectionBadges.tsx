"use client";
import { motion, AnimatePresence } from "framer-motion";
import type { Detection } from "@/lib/api";

interface Props {
  detections: Detection[];
}

const TYPE_COLORS: Record<string, string> = {
  base64: "text-cyber-blue border-cyber-blue/50 bg-cyber-blue/10",
  base32: "text-cyan-400 border-cyan-400/50 bg-cyan-400/10",
  base85: "text-teal-400 border-teal-400/50 bg-teal-400/10",
  hex: "text-cyber-green border-cyber-green/50 bg-cyber-green/10",
  binary: "text-lime-400 border-lime-400/50 bg-lime-400/10",
  decimal_ascii: "text-emerald-400 border-emerald-400/50 bg-emerald-400/10",
  rot13: "text-cyber-purple border-cyber-purple/50 bg-cyber-purple/10",
  caesar: "text-violet-400 border-violet-400/50 bg-violet-400/10",
  morse: "text-amber-400 border-amber-400/50 bg-amber-400/10",
  url: "text-orange-400 border-orange-400/50 bg-orange-400/10",
  xor: "text-cyber-pink border-cyber-pink/50 bg-cyber-pink/10",
};

export default function DetectionBadges({ detections }: Props) {
  if (!detections.length) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-2"
    >
      <p className="text-xs text-cyber-muted uppercase tracking-widest">Detected Encodings</p>
      <div className="flex flex-wrap gap-2">
        <AnimatePresence>
          {detections.map((d, i) => (
            <motion.div
              key={d.type}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono
                ${TYPE_COLORS[d.type] ?? "text-cyber-text border-cyber-border bg-cyber-card"}`}
            >
              <span>{d.type.replace("_", " ").toUpperCase()}</span>
              <div className="w-px h-3 bg-current opacity-30" />
              <span className="opacity-80">{Math.round(d.confidence * 100)}%</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
